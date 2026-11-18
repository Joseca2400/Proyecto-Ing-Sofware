"""Motor contable (Sprint 1, equipo A): el único lugar donde nacen las partidas.

Contrato para los demás módulos (compras, taller, unidades…): llamar a `registrar_automatica`
dentro de su propia transacción, con el documento que la origina. El servicio no confirma:
el documento y su partida se confirman juntos, o ninguno (regla 3 de la arquitectura).

HU-2.01 (incluido): partida manual en borrador, líneas en quetzales o dólares con su equivalente,
validación de dimensiones contra la cuenta, cuadre al enviar a revisión y correlativo al contabilizar.
HU-2.02 (incluido): borrador → en revisión → contabilizada, o devuelta con comentario y reenvío.
HU-2.03 (incluido): partida automática ligada a su documento, una por documento; cada tipo de
documento toma sus cuentas de una regla configurable (`cuenta_regla`) y, si falta, no hay partida;
el contador cambia la cuenta de una regla desde su pantalla. Navegación en ambos sentidos: la
partida guarda tipo e id de su documento y `partida_de_documento` va del documento a su partida.
Una automática nace contabilizada: no se edita, envía, devuelve ni revierte a mano; se corrige
desde su documento (el módulo dueño llama a `revertir_automatica`).
HU-2.03 (diferido): reglas con línea de negocio y origen del VIN propios; hoy cada módulo pone
VIN y línea en sus líneas y el catálogo valida las dimensiones de cada cuenta.
HU-1.10 (incluido): quien registra una partida manual no la contabiliza ni otro la corrige por él.
HU-2.16 (incluido): balance de comprobación y mayor sobre partidas contabilizadas, con filtros de
fechas, línea de negocio y VIN; `saldo_cuenta` para que otros módulos concilien contra el mayor.
Pendiente: exportar el balance y el mayor (Sprint 5, con HU-7.09).
HU-2.05 (incluido): reversión con motivo y fecha elegida, en una partida nueva contabilizada que
invierte las líneas y apunta a la original (`revierte_a`); la original no se toca y no se revierte
dos veces. Solo el contador revierte a mano y solo partidas manuales; la de un documento la pide
su módulo con `revertir_automatica`.
HU-2.09 (incluido, pieza del motor): `diferencial_cambiario` calcula la ganancia o pérdida
realizada de un pago o cobro en USD (proporcional al monto aplicado, desde el tipo de cambio en
libros) y da su línea; una `LineaAutomatica` lleva la línea en USD del saldo a su tasa en libros.
HU-2.09 (diferido): la partida de pagos y cobros la arma su módulo en el Sprint 3.
Pendiente: límites monetarios de aprobación; lotes; adjuntos; impedir fechas en período cerrado
(HU-2.05 criterio 2, llega con los períodos de HU-2.12 en el Sprint 3).
"""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Literal

from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad.models import LineaPartida, Partida, ReglaContabilizacion
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
        # Una `LineaAutomatica` puede traer su tipo de cambio (saldo en libros, HU-2.09).
        tipo_cambio = getattr(datos, "tipo_cambio", None)
        if tipo_cambio is None:
            tipo_cambio = configuracion.tipo_cambio_de(db, fecha)
        elif tipo_cambio <= 0 or -tipo_cambio.as_tuple().exponent > 8:  # type: ignore[operator]
            raise ErrorNegocio(f"Línea {numero}: el tipo de cambio debe ser positivo con hasta 8 decimales")
        monto_usd = monto
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


def corregir(db: Session, partida_id: int, datos: PartidaEntrada, usuario_id: int | None = None) -> Partida:
    """Reemplaza el contenido de un borrador o de una partida devuelta."""
    partida = _obtener(db, partida_id, bloquear=True)
    _exigir_estado(partida, "borrador", "devuelta", accion="editar")
    # Si otro pudiera editarla, podría escribir el contenido y luego aprobarlo (HU-1.10).
    if usuario_id is not None and partida.creado_por != usuario_id:
        raise ErrorNegocio("Solo quien registró la partida puede corregirla", 403)
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
    if usuario_id is not None and partida.creado_por == usuario_id:
        raise ErrorNegocio("No puedes contabilizar una partida que registraste tú", 403)
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


# ── HU-2.05: reversión de una partida contabilizada ───────────────────────────


def _revertir(db: Session, original: Partida, fecha: date, motivo: str, usuario_id: int | None) -> Partida:
    """Crea y contabiliza la reversión, sin confirmar. `original` debe venir bloqueada."""
    _exigir_estado(original, "contabilizada", accion="revertir")
    if original.revierte_a is not None:
        raise ErrorNegocio("Una partida de reversión no se revierte", 409)
    # Consulta fresca tras el candado: la relación cargada en la sesión puede estar vieja.
    previa = db.scalar(select(Partida.numero).where(Partida.revierte_a == original.id))
    if previa is not None:
        raise ErrorNegocio(f"La partida No. {original.numero} ya fue revertida por la No. {previa}", 409)
    motivo = motivo.strip()
    if not motivo:
        raise ErrorNegocio("La reversión necesita un motivo")
    if fecha > date.today():
        raise ErrorNegocio("La fecha de la reversión no puede ser futura")
    if fecha < original.fecha:
        raise ErrorNegocio("La reversión no puede tener fecha anterior a la partida original")
    reversion = Partida(
        fecha=fecha,
        concepto=f"Reversión de la partida No. {original.numero}",
        comentario=motivo,
        origen=original.origen,
        documento_tipo=original.documento_tipo,
        documento_id=original.documento_id,
        revierte_a=original.id,
        creado_por=usuario_id,
        # Mismos quetzales invertidos: una línea en USD no se vuelve a convertir con otra tasa.
        lineas=[
            LineaPartida(
                numero_linea=linea.numero_linea,
                cuenta_id=linea.cuenta_id,
                debe=linea.haber,
                haber=linea.debe,
                moneda=linea.moneda,
                monto_usd=linea.monto_usd,
                tipo_cambio=linea.tipo_cambio,
                linea_negocio=linea.linea_negocio,
                vin=linea.vin,
            )
            for linea in original.lineas
        ],
    )
    db.add(reversion)
    db.flush()
    _contabilizar(db, reversion, usuario_id)
    return reversion


def revertir(
    db: Session, partida_id: int, fecha: date, motivo: str, usuario_id: int | None = None
) -> Partida:
    """Reversión manual por el contador. Las automáticas se revierten desde su documento."""
    original = _obtener(db, partida_id, bloquear=True)
    if original.origen == "automatica":
        raise ErrorNegocio(
            "Una partida automática no se revierte a mano: anule o corrija el documento "
            f"{original.documento_tipo} {original.documento_id}",
            409,
        )
    reversion = _revertir(db, original, fecha, motivo, usuario_id)
    db.commit()
    db.refresh(reversion)
    return reversion


def revertir_automatica(
    db: Session,
    documento_tipo: str,
    documento_id: str | int,
    fecha: date,
    motivo: str,
    usuario_id: int | None = None,
) -> Partida:
    """Revierte la partida de un documento, sin confirmar (como `registrar_automatica`).

    La llama el módulo dueño del documento al anularlo; él confirma la anulación y la reversión
    juntas, o revierte todo si esto lanza `ErrorNegocio`.
    """
    original = partida_de_documento(db, documento_tipo, documento_id)
    return _revertir(db, _obtener(db, original.id, bloquear=True), fecha, motivo, usuario_id)


def partida_de_documento(db: Session, documento_tipo: str, documento_id: str | int) -> Partida:
    """La partida automática que originó un documento (no su reversión)."""
    partida = db.scalar(
        select(Partida).where(
            Partida.documento_tipo == documento_tipo,
            Partida.documento_id == str(documento_id),
            Partida.revierte_a.is_(None),
        )
    )
    if partida is None:
        raise ErrorNegocio(f"El documento {documento_tipo} {documento_id} no tiene partida", 404)
    return partida


# ── HU-2.03: reglas de contabilización ────────────────────────────────────────


def cuenta_regla(db: Session, documento_tipo: str, concepto: str) -> int:
    """Id de la cuenta que la regla asigna a `concepto` del documento.

    La llama el módulo dueño del documento antes de pedir su partida. Si la regla no tiene una
    cuenta de detalle del catálogo, avisa cuál falta y el documento no se registra (criterio 3).
    """
    codigo = db.scalar(
        select(ReglaContabilizacion.cuenta_codigo).where(
            ReglaContabilizacion.documento_tipo == documento_tipo,
            ReglaContabilizacion.concepto == concepto,
        )
    )
    cuenta = configuracion.buscar_cuenta(db, codigo) if codigo else None
    if cuenta is None or not cuenta.es_detalle:
        raise ErrorNegocio(
            f"Falta la regla de contabilización «{documento_tipo} · {concepto}»: "
            "asígnele una cuenta de detalle del catálogo antes de registrar el documento",
            409,
        )
    return cuenta.id


def listar_reglas(db: Session) -> list[ReglaContabilizacion]:
    return list(
        db.scalars(
            select(ReglaContabilizacion).order_by(
                ReglaContabilizacion.documento_tipo, ReglaContabilizacion.concepto
            )
        )
    )


def definir_regla(db: Session, regla_id: int, cuenta_codigo: str) -> ReglaContabilizacion:
    regla = db.get(ReglaContabilizacion, regla_id)
    if regla is None:
        raise ErrorNegocio("La regla de contabilización no existe", 404)
    cuenta = configuracion.buscar_cuenta(db, cuenta_codigo)
    if cuenta is None or not cuenta.es_detalle:
        raise ErrorNegocio(f"La cuenta {cuenta_codigo} no es una cuenta de detalle del catálogo")
    regla.cuenta_codigo = cuenta.codigo
    db.commit()
    return regla


# ── HU-2.09: diferencial cambiario realizado ──────────────────────────────────


def diferencial_cambiario(
    db: Session,
    monto_usd: Decimal | str,
    tipo_cambio_libros: Decimal | str,
    tipo_cambio_liquidacion: Decimal | str,
    saldo: Literal["por_pagar", "por_cobrar"],
    linea_negocio: str | None = None,
    vin: str | None = None,
) -> tuple[Decimal, LineaEntrada | None]:
    """Diferencial realizado al pagar o cobrar `monto_usd` de un saldo en dólares.

    - `monto_usd`: lo que se aplica ahora; un pago parcial da un diferencial proporcional.
    - `tipo_cambio_libros`: al que está el saldo en los libros: el del documento o, si ya se
      revaluó (HU-2.08), el de la última revaluación, para no contar dos veces el efecto.
    - `tipo_cambio_liquidacion`: el del pago o cobro; para que la partida cuadre al centavo debe
      ser el mismo con que `registrar_automatica` convierta la línea del banco (el de la fecha).

    Devuelve el diferencial en quetzales (positivo ganancia, negativo pérdida) y la línea lista
    para la partida, o `(0, None)` si no hay diferencia. Redondea igual que el motor (mitad hacia
    arriba, 6 decimales) para componer con las líneas en USD. La cuenta sale de las reglas
    `diferencial_cambiario · ganancia/perdida`; si falta, lanza `ErrorNegocio` (409).
    """
    usd, libros, liquidacion = (
        a_decimal(valor) for valor in (monto_usd, tipo_cambio_libros, tipo_cambio_liquidacion)
    )
    if usd <= 0 or libros <= 0 or liquidacion <= 0:
        raise ErrorNegocio("El monto en USD y los tipos de cambio deben ser mayores que cero")
    if saldo not in ("por_pagar", "por_cobrar"):
        raise ErrorNegocio("El saldo debe ser por_pagar o por_cobrar")
    diferencia = redondear(convertir(usd, liquidacion), DECIMALES) - redondear(
        convertir(usd, libros), DECIMALES
    )
    # Cobrar a una tasa mayor es ganancia; pagar a una tasa mayor es pérdida.
    resultado = diferencia if saldo == "por_cobrar" else -diferencia
    if resultado == 0:
        return Decimal(0), None
    concepto, lado = ("ganancia", "haber") if resultado > 0 else ("perdida", "debe")
    linea = LineaEntrada(
        cuenta_id=cuenta_regla(db, "diferencial_cambiario", concepto),
        lado=lado,
        monto=f"{abs(resultado):f}",
        linea_negocio=linea_negocio,
        vin=vin,
    )
    return resultado, linea


# ── HU-2.16: balance de comprobación y mayor (solo partidas contabilizadas) ───


def _contabilizadas(consulta, hasta: date | None, linea_negocio: str | None, vin: str | None):
    consulta = consulta.join(Partida, LineaPartida.partida_id == Partida.id).where(
        Partida.estado == "contabilizada"
    )
    if hasta is not None:
        consulta = consulta.where(Partida.fecha <= hasta)
    if linea_negocio:
        consulta = consulta.where(LineaPartida.linea_negocio == linea_negocio)
    if vin and vin.strip():
        consulta = consulta.where(LineaPartida.vin == vin.strip().upper())
    return consulta


def _signo(naturaleza: str) -> int:
    """Saldo positivo en el lado normal de la cuenta: débito en deudoras, crédito en acreedoras."""
    return 1 if naturaleza == "deudora" else -1


def saldo_cuenta(
    db: Session,
    cuenta_id: int,
    hasta: date | None = None,
    vin: str | None = None,
    linea_negocio: str | None = None,
) -> Decimal:
    """Saldo en quetzales de una cuenta según el mayor, para que otros módulos concilien.

    Positivo en el lado normal de la cuenta (débito en deudoras, crédito en acreedoras). Ejemplo:
    la hoja de costo de una unidad (HU-4.08) compara su total con el saldo de unidades en proceso
    para su VIN.
    """
    cuenta = configuracion.obtener_cuenta(db, cuenta_id)
    neto = db.scalar(
        _contabilizadas(
            select(func.coalesce(func.sum(LineaPartida.debe - LineaPartida.haber), 0)).where(
                LineaPartida.cuenta_id == cuenta_id
            ),
            hasta,
            linea_negocio,
            vin,
        )
    )
    return Decimal(neto) * _signo(cuenta.naturaleza)


def balance_comprobacion(
    db: Session,
    desde: date | None = None,
    hasta: date | None = None,
    linea_negocio: str | None = None,
    vin: str | None = None,
) -> dict:
    """Por cuenta: saldo inicial (antes de `desde`), débitos y créditos del rango y saldo final.

    Los saldos van con el signo de la naturaleza de la cuenta; los totales del rango los suma el
    servidor (el front no suma).
    """
    antes = Partida.fecha < (desde or date.min)
    cero = Decimal(0)
    filas = db.execute(
        _contabilizadas(
            select(
                LineaPartida.cuenta_id,
                func.sum(case((antes, LineaPartida.debe - LineaPartida.haber), else_=cero)),
                func.sum(case((antes, cero), else_=LineaPartida.debe)),
                func.sum(case((antes, cero), else_=LineaPartida.haber)),
            ),
            hasta,
            linea_negocio,
            vin,
        ).group_by(LineaPartida.cuenta_id)
    ).all()
    cuentas = {cuenta.id: cuenta for cuenta in configuracion.listar_cuentas(db, solo_detalle=True)}
    resultado = []
    for cuenta_id, previo, debe, haber in filas:
        cuenta = cuentas[cuenta_id]
        signo = _signo(cuenta.naturaleza)
        resultado.append(
            {
                "cuenta_id": cuenta_id,
                "codigo": cuenta.codigo,
                "nombre": cuenta.nombre,
                "naturaleza": cuenta.naturaleza,
                "saldo_inicial": previo * signo,
                "debe": debe,
                "haber": haber,
                "saldo_final": (previo + debe - haber) * signo,
            }
        )
    resultado.sort(key=lambda fila: fila["codigo"])
    return {
        "filas": resultado,
        "total_debe": sum((fila["debe"] for fila in resultado), cero),
        "total_haber": sum((fila["haber"] for fila in resultado), cero),
    }


def mayor(
    db: Session,
    cuenta_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    linea_negocio: str | None = None,
    vin: str | None = None,
) -> dict:
    """Mayor de una cuenta: saldo inicial, cada movimiento con su saldo acumulado y saldo final."""
    cuenta = configuracion.obtener_cuenta(db, cuenta_id)
    signo = _signo(cuenta.naturaleza)
    inicial = (
        saldo_cuenta(db, cuenta_id, desde - timedelta(days=1), vin, linea_negocio) if desde else Decimal(0)
    )
    consulta = _contabilizadas(
        select(LineaPartida, Partida).where(LineaPartida.cuenta_id == cuenta_id), hasta, linea_negocio, vin
    )
    if desde is not None:
        consulta = consulta.where(Partida.fecha >= desde)
    saldo = inicial
    movimientos = []
    for linea, partida in db.execute(
        consulta.order_by(Partida.fecha, Partida.numero, LineaPartida.numero_linea)
    ).all():
        saldo += (linea.debe - linea.haber) * signo
        movimientos.append(
            {
                "fecha": partida.fecha,
                "partida_id": partida.id,
                "numero": partida.numero,
                "concepto": partida.concepto,
                "documento_tipo": partida.documento_tipo,
                "documento_id": partida.documento_id,
                "debe": linea.debe,
                "haber": linea.haber,
                "saldo": saldo,
                "moneda": linea.moneda,
                "monto_usd": linea.monto_usd,
                "tipo_cambio": linea.tipo_cambio,
                "linea_negocio": linea.linea_negocio,
                "vin": linea.vin,
            }
        )
    return {
        "cuenta_id": cuenta.id,
        "codigo": cuenta.codigo,
        "nombre": cuenta.nombre,
        "naturaleza": cuenta.naturaleza,
        "monetaria_usd": cuenta.monetaria_usd,
        "saldo_inicial": inicial,
        "movimientos": movimientos,
        "saldo_final": saldo,
    }
