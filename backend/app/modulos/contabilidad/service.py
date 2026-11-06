"""Motor contable (Sprint 1, equipo A): el único lugar donde nacen las partidas.

Contrato para los demás módulos (compras, taller, unidades…): llamar a `registrar_automatica`
dentro de su propia transacción, con el documento que la origina. El servicio no confirma:
el documento y su partida se confirman juntos, o ninguno (regla 3 de la arquitectura).

HU-2.01 (incluido): partida manual en borrador, líneas en quetzales o dólares con su equivalente,
validación de dimensiones contra la cuenta, cuadre al enviar a revisión y correlativo al contabilizar.
HU-2.02 (incluido): borrador → en revisión → contabilizada, o devuelta con comentario y reenvío.
HU-2.03 (incluido): partida automática ligada a su documento, una por documento.
Pendiente: separación de funciones entre quien registra y quien contabiliza (HU-1.10); aprobación
del gerente financiero en ajustes grandes; lotes; adjuntos; reversión (HU-2.05); período abierto.
"""

from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad.models import LineaPartida, Partida
from app.modulos.contabilidad.schemas import LineaEntrada, PartidaEntrada

DECIMALES = 6
_LIMITE = Decimal("1000000000000")  # cabe en NUMERIC(18, 6)
_BLOQUEO_CORRELATIVO = 20261101  # llave del candado de transacción que serializa el correlativo


def _monto(texto: str, numero: int) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio(f"Línea {numero}: el monto no es un número válido") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio(f"Línea {numero}: el monto debe ser mayor que cero")
    if -valor.as_tuple().exponent > DECIMALES:  # type: ignore[operator]
        raise ErrorNegocio(f"Línea {numero}: el monto admite hasta {DECIMALES} decimales")
    if valor >= _LIMITE:
        raise ErrorNegocio(f"Línea {numero}: el monto excede el máximo permitido")
    return valor


def _linea(db: Session, fecha: date, numero: int, datos: LineaEntrada) -> LineaPartida:
    cuenta = configuracion.obtener_cuenta(db, datos.cuenta_id)
    try:
        linea_negocio = configuracion.resolver_dimensiones(db, cuenta.id, datos.linea_negocio, datos.vin)
    except ErrorNegocio as error:
        raise ErrorNegocio(f"Línea {numero}: {error.mensaje}", error.status) from None
    vin = (datos.vin or "").strip().upper() or None
    if vin is not None and len(vin) != 17:
        raise ErrorNegocio(f"Línea {numero}: el VIN debe tener 17 caracteres")
    monto = _monto(datos.monto, numero)

    monto_usd = tipo_cambio = None
    if datos.moneda == "USD":
        if not cuenta.monetaria_usd:
            raise ErrorNegocio(f"Línea {numero}: la cuenta {cuenta.codigo} no admite montos en USD")
        monto_usd, tipo_cambio = monto, configuracion.tipo_cambio_de(db, fecha)
        equivalente = convertir(monto_usd, tipo_cambio)
        if equivalente >= _LIMITE:
            raise ErrorNegocio(f"Línea {numero}: el equivalente en quetzales excede el máximo permitido")
        monto = redondear(equivalente, DECIMALES)
        if monto >= _LIMITE:
            raise ErrorNegocio(f"Línea {numero}: el equivalente en quetzales excede el máximo permitido")
        if monto <= 0:
            raise ErrorNegocio(f"Línea {numero}: el equivalente en quetzales es cero")

    cero = Decimal(0)
    return LineaPartida(
        numero_linea=numero,
        cuenta_id=cuenta.id,
        debe=monto if datos.lado == "debe" else cero,
        haber=monto if datos.lado == "haber" else cero,
        moneda=datos.moneda,
        monto_usd=monto_usd,
        tipo_cambio=tipo_cambio,
        linea_negocio=linea_negocio,
        vin=vin,
    )


def _lineas(db: Session, fecha: date, entradas: list[LineaEntrada]) -> list[LineaPartida]:
    if fecha > date.today():
        raise ErrorNegocio("La fecha de la partida no puede ser futura")
    if not entradas:
        raise ErrorNegocio("La partida necesita al menos una línea")
    return [_linea(db, fecha, numero, datos) for numero, datos in enumerate(entradas, start=1)]


def totales(partida: Partida) -> tuple[Decimal, Decimal]:
    """Suma de débitos y créditos en quetzales."""
    return (
        sum((linea.debe for linea in partida.lineas), Decimal(0)),
        sum((linea.haber for linea in partida.lineas), Decimal(0)),
    )


def _exigir_cuadre(partida: Partida) -> None:
    debe, haber = totales(partida)
    if len(partida.lineas) < 2:
        raise ErrorNegocio("La partida necesita al menos un débito y un crédito")
    if debe != haber:
        raise ErrorNegocio(
            f"La partida no cuadra: débitos {debe:.6f}, créditos {haber:.6f}, "
            f"diferencia {abs(debe - haber):.6f}"
        )


def _obtener(db: Session, partida_id: int, *, bloquear: bool = False) -> Partida:
    consulta = select(Partida).where(Partida.id == partida_id)
    if bloquear:
        # Releer también las líneas después del candado: la sesión puede tener datos obsoletos.
        consulta = consulta.with_for_update().execution_options(populate_existing=True)
    partida = db.scalar(consulta)
    if partida is None:
        raise ErrorNegocio(f"No existe la partida {partida_id}", 404)
    return partida


def _exigir_estado(partida: Partida, *estados: str, accion: str) -> None:
    if partida.estado not in estados:
        raise ErrorNegocio(f"No se puede {accion} una partida {partida.estado.replace('_', ' ')}", 409)


def _contabilizar(db: Session, partida: Partida, usuario_id: int | None) -> None:
    # El candado dura hasta el commit: dos contabilizaciones simultáneas no repiten ni saltan número.
    db.execute(select(func.pg_advisory_xact_lock(_BLOQUEO_CORRELATIVO)))
    siguiente = db.scalar(select(func.coalesce(func.max(Partida.numero), 0) + 1))
    partida.numero = siguiente
    partida.estado = "contabilizada"
    partida.contabilizada_por = usuario_id
    partida.contabilizada_en = datetime.now(UTC)
    db.flush()  # la base revisa el cuadre al pasar a contabilizada


# ── HU-2.01 y HU-2.02: partida manual y su revisión ───────────────────────────


def crear_borrador(db: Session, datos: PartidaEntrada, usuario_id: int | None = None) -> Partida:
    """Guarda la partida manual en borrador. Puede quedar descuadrada: se exige al enviarla."""
    partida = Partida(
        fecha=datos.fecha,
        concepto=datos.concepto,
        documento_soporte=datos.documento_soporte or None,
        creado_por=usuario_id,
        lineas=_lineas(db, datos.fecha, datos.lineas),
    )
    db.add(partida)
    db.commit()
    db.refresh(partida)
    return partida


def corregir(db: Session, partida_id: int, datos: PartidaEntrada) -> Partida:
    """Reemplaza el contenido de un borrador o de una partida devuelta."""
    partida = _obtener(db, partida_id, bloquear=True)
    _exigir_estado(partida, "borrador", "devuelta", accion="editar")
    nuevas = _lineas(db, datos.fecha, datos.lineas)  # valida todo antes de tocar la partida
    partida.fecha, partida.concepto = datos.fecha, datos.concepto
    partida.documento_soporte = datos.documento_soporte or None
    partida.lineas.clear()
    db.flush()  # borrar antes de insertar: (partida, número de línea) es único
    partida.lineas = nuevas
    db.commit()
    db.refresh(partida)
    return partida


def enviar_a_revision(db: Session, partida_id: int) -> Partida:
    partida = _obtener(db, partida_id, bloquear=True)
    _exigir_estado(partida, "borrador", "devuelta", accion="enviar a revisión")
    _exigir_cuadre(partida)
    partida.estado, partida.comentario = "en_revision", None
    db.commit()
    db.refresh(partida)
    return partida


def contabilizar(db: Session, partida_id: int, usuario_id: int | None = None) -> Partida:
    partida = _obtener(db, partida_id, bloquear=True)
    _exigir_estado(partida, "en_revision", accion="contabilizar")
    _exigir_cuadre(partida)
    _contabilizar(db, partida, usuario_id)
    db.commit()
    db.refresh(partida)
    return partida


def devolver(db: Session, partida_id: int, comentario: str) -> Partida:
    partida = _obtener(db, partida_id, bloquear=True)
    _exigir_estado(partida, "en_revision", accion="devolver")
    if not comentario.strip():
        raise ErrorNegocio("La devolución necesita un comentario")
    partida.estado, partida.comentario = "devuelta", comentario.strip()
    db.commit()
    db.refresh(partida)
    return partida


def obtener_partida(db: Session, partida_id: int) -> Partida:
    return _obtener(db, partida_id)


def listar_partidas(db: Session, estado: str | None = None) -> list[Partida]:
    consulta = select(Partida).order_by(Partida.fecha.desc(), Partida.id.desc())
    if estado:
        consulta = consulta.where(Partida.estado == estado)
    return list(db.scalars(consulta))


# ── HU-2.03: partida automática desde otro módulo ─────────────────────────────


def registrar_automatica(
    db: Session,
    fecha: date,
    concepto: str,
    lineas: list[LineaEntrada],
    documento_tipo: str,
    documento_id: str | int,
    usuario_id: int | None = None,
) -> Partida:
    """Crea la partida contabilizada de un documento, sin confirmar la transacción.

    La llama el módulo dueño del documento (compras, taller…) y confirma él, una sola vez, el
    documento y la partida. Si no cuadra o una línea es inválida, lanza `ErrorNegocio` y no
    queda nada pendiente de guardar; el llamador debe revertir su transacción.
    """
    documento_id = str(documento_id)
    if db.scalar(
        select(Partida.id).where(
            Partida.documento_tipo == documento_tipo, Partida.documento_id == documento_id
        )
    ):
        raise ErrorNegocio(f"El documento {documento_tipo} {documento_id} ya tiene su partida", 409)
    partida = Partida(
        fecha=fecha,
        concepto=concepto,
        origen="automatica",
        documento_tipo=documento_tipo,
        documento_id=documento_id,
        creado_por=usuario_id,
        lineas=_lineas(db, fecha, lineas),
    )
    _exigir_cuadre(partida)
    db.add(partida)
    try:
        db.flush()
        _contabilizar(db, partida, usuario_id)
    except IntegrityError as error:
        db.rollback()
        if (
            getattr(error.orig, "sqlstate", None) == "23505"
            and getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "uq_partida_documento"
        ):
            raise ErrorNegocio(
                f"El documento {documento_tipo} {documento_id} ya tiene su partida", 409
            ) from error
        raise
    return partida
