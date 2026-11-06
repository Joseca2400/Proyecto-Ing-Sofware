"""Reglas del módulo de configuración.

Equipo A — catálogo de cuentas y dimensiones analíticas (HU-1.02, HU-1.04).
`resolver_dimensiones` es lo que el motor contable llama por cada línea de una partida.

Equipo B — tipo de cambio y transacciones en USD (Sprint 1):
HU-1.06 (incluido): carga manual del tipo de cambio positivo por fecha; bloqueo cuando falta.
HU-1.06 (diferido): consulta automática al Banguat (adaptador en `comun/`) y corrección con
aprobación del gerente financiero.
HU-1.07 (incluido): registro de transacciones en USD con monto original, tipo de cambio aplicado
y equivalente en quetzales; tipo personalizado positivo con justificación obligatoria.
HU-1.07 (diferido): reportes de saldos en USD.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import Cuenta, TipoCambio, TransaccionUSD

# ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────

TIPOS = ("activo", "pasivo", "patrimonio", "ingreso", "costo", "gasto")
NATURALEZAS = ("deudora", "acreedora")
LINEAS_NEGOCIO = ("alquiler", "venta", "taller", "financiamiento", "administracion")
VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA = "obligatorio", "opcional", "no_aplica"
MODOS_VIN = (VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA)


def listar_cuentas(db: Session, solo_detalle: bool = False) -> list[Cuenta]:
    """Ordenadas por código: con el nivel de cada una basta para dibujar el árbol."""
    consulta = select(Cuenta).order_by(Cuenta.codigo)
    if solo_detalle:
        consulta = consulta.where(Cuenta.es_detalle)
    return list(db.scalars(consulta))


def _cuenta(db: Session, cuenta_id: int) -> Cuenta:
    cuenta = db.get(Cuenta, cuenta_id)
    if cuenta is None:
        raise ErrorNegocio("La cuenta no existe", 404)
    return cuenta


def _fijar_dimensiones(cuenta: Cuenta, linea_obligatoria: bool, vin: str, linea_defecto: str | None) -> None:
    if vin not in MODOS_VIN:
        raise ErrorNegocio(f"VIN debe ser uno de: {', '.join(MODOS_VIN)}")
    if linea_defecto is not None and linea_defecto not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea_defecto}")
    if not cuenta.es_detalle and (linea_obligatoria or vin != VIN_NO_APLICA or linea_defecto):
        raise ErrorNegocio("Las dimensiones solo se definen en cuentas de detalle")
    cuenta.linea_obligatoria, cuenta.vin, cuenta.linea_defecto = linea_obligatoria, vin, linea_defecto


def crear_cuenta(
    db: Session,
    codigo: str,
    nombre: str,
    tipo: str,
    naturaleza: str,
    padre_id: int | None = None,
    es_detalle: bool = True,
    monetaria_usd: bool = False,
    linea_obligatoria: bool = False,
    vin: str = VIN_NO_APLICA,
    linea_defecto: str | None = None,
) -> Cuenta:
    codigo = codigo.strip()
    nombre = nombre.strip()
    if not codigo or not nombre:
        raise ErrorNegocio("El código y el nombre son obligatorios")
    if len(codigo) > 30 or len(nombre) > 200:
        raise ErrorNegocio("El código admite hasta 30 caracteres y el nombre hasta 200", 422)
    if tipo not in TIPOS or naturaleza not in NATURALEZAS:
        raise ErrorNegocio("Tipo o naturaleza desconocidos")
    if db.scalar(select(Cuenta.id).where(Cuenta.codigo == codigo)) is not None:
        raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409)
    nivel = 1
    if padre_id is not None:
        padre = _cuenta(db, padre_id)
        if padre.es_detalle:
            raise ErrorNegocio("Una cuenta de detalle no puede tener cuentas hijas")
        if padre.tipo != tipo:
            raise ErrorNegocio(f"La cuenta hija debe ser del mismo tipo que la cuenta padre ({padre.tipo})")
        nivel = padre.nivel + 1
    cuenta = Cuenta(
        codigo=codigo, nombre=nombre.strip(), tipo=tipo, naturaleza=naturaleza, nivel=nivel,
        padre_id=padre_id, es_detalle=es_detalle, monetaria_usd=monetaria_usd,
    )  # fmt: skip
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.add(cuenta)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if (
            getattr(exc.orig, "sqlstate", None) == "23505"
            and getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "cuentas_codigo_key"
        ):
            raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409) from exc
        raise
    return cuenta


def definir_dimensiones(
    db: Session, cuenta_id: int, linea_obligatoria: bool, vin: str, linea_defecto: str | None
) -> Cuenta:
    cuenta = _cuenta(db, cuenta_id)
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.commit()
    return cuenta


def resolver_dimensiones(db: Session, cuenta_id: int, linea: str | None, vin: str | None) -> str | None:
    """Valida una línea de partida contra su cuenta y devuelve la línea de negocio a guardar.

    Usa la línea por defecto de la cuenta si no se indicó una. Rechaza lo que la cuenta no admite.
    """
    cuenta = _cuenta(db, cuenta_id)
    if not cuenta.es_detalle:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} es de agrupación y no recibe movimientos")
    linea = linea or cuenta.linea_defecto
    if linea is not None and linea not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea}")
    if linea is None and cuenta.linea_obligatoria:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige línea de negocio")
    vin = (vin or "").strip()
    if not vin and cuenta.vin == VIN_OBLIGATORIO:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige el VIN de la unidad")
    if vin and cuenta.vin == VIN_NO_APLICA:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} no admite VIN")
    return linea


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────

DECIMALES_TIPO_CAMBIO = 8


def _validar_valor(texto: str) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio("El tipo de cambio debe ser un número, por ejemplo 7.75") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio("El tipo de cambio debe ser mayor que cero")
    if -valor.as_tuple().exponent > DECIMALES_TIPO_CAMBIO:
        raise ErrorNegocio(f"El tipo de cambio admite como máximo {DECIMALES_TIPO_CAMBIO} decimales")
    if valor >= Decimal("10000000000"):
        raise ErrorNegocio("El tipo de cambio es demasiado grande")
    return valor


def registrar_manual(db: Session, fecha: date, valor: str) -> TipoCambio:
    """Carga manual del tipo de cambio de una fecha. No reemplaza uno ya cargado."""
    if fecha > date.today():
        raise ErrorNegocio("No se puede cargar el tipo de cambio de una fecha futura")
    valor_decimal = _validar_valor(valor)
    if db.scalar(select(TipoCambio.id).where(TipoCambio.fecha == fecha)) is not None:
        raise ErrorNegocio(
            f"Ya existe el tipo de cambio del {fecha:%d/%m/%Y}; corregirlo requiere aprobación",
            status=409,
        )
    tipo = TipoCambio(fecha=fecha, valor=valor_decimal, origen="manual")
    db.add(tipo)
    db.commit()
    db.refresh(tipo)
    return tipo


def listar(db: Session, desde: date | None = None, hasta: date | None = None) -> list[TipoCambio]:
    consulta = select(TipoCambio).order_by(TipoCambio.fecha.desc())
    if desde:
        consulta = consulta.where(TipoCambio.fecha >= desde)
    if hasta:
        consulta = consulta.where(TipoCambio.fecha <= hasta)
    return list(db.scalars(consulta))


def buscar(db: Session, fecha: date) -> TipoCambio | None:
    return db.scalar(select(TipoCambio).where(TipoCambio.fecha == fecha))


def tipo_cambio_de(db: Session, fecha: date) -> Decimal:
    """Valor para convertir una transacción en USD de esa fecha (lo usa HU-1.07).

    Si no existe, rechaza la operación: la transacción no se guarda hasta que se cargue.
    """
    tipo = buscar(db, fecha)
    if tipo is None:
        raise ErrorNegocio(
            f"No existe tipo de cambio para el {fecha:%d/%m/%Y}; cárguelo antes de registrar "
            "la transacción en dólares",
            status=409,
        )
    return tipo.valor


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────

_MAX_DECIMALES_MONTO = 6


def _validar_monto_usd(texto: str) -> Decimal:
    try:
        valor = a_decimal(texto.strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio("El monto en USD debe ser un número, por ejemplo 8500.00") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio("El monto en USD debe ser mayor que cero")
    if -valor.as_tuple().exponent > _MAX_DECIMALES_MONTO:
        raise ErrorNegocio(f"El monto en USD admite como máximo {_MAX_DECIMALES_MONTO} decimales")
    return valor


def registrar_transaccion_usd(
    db: Session,
    fecha: date,
    monto_usd_texto: str,
    tipo_cambio_personalizado: str | None = None,
    justificacion: str | None = None,
) -> TransaccionUSD:
    """Registra una transacción en USD y calcula su equivalente en quetzales.

    Por defecto usa el tipo de cambio del Banguat de la fecha. Si se indica un tipo personalizado,
    debe ser positivo y la justificación es obligatoria (criterio 4 de HU-1.07).
    """
    monto_usd = _validar_monto_usd(monto_usd_texto)

    if tipo_cambio_personalizado is not None:
        tc = _validar_valor(tipo_cambio_personalizado)
        if not justificacion or not justificacion.strip():
            raise ErrorNegocio("El tipo de cambio personalizado requiere justificación")
        justificacion = justificacion.strip()
    else:
        tc = tipo_cambio_de(db, fecha)
        justificacion = None

    monto_gtq = redondear(convertir(monto_usd, tc), _MAX_DECIMALES_MONTO)

    transaccion = TransaccionUSD(
        fecha=fecha,
        monto_usd=monto_usd,
        tipo_cambio_aplicado=tc,
        monto_gtq=monto_gtq,
        justificacion=justificacion,
    )
    db.add(transaccion)
    db.commit()
    db.refresh(transaccion)
    return transaccion


def listar_transacciones_usd(
    db: Session,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[TransaccionUSD]:
    consulta = select(TransaccionUSD).order_by(TransaccionUSD.fecha.desc(), TransaccionUSD.id.desc())
    if desde:
        consulta = consulta.where(TransaccionUSD.fecha >= desde)
    if hasta:
        consulta = consulta.where(TransaccionUSD.fecha <= hasta)
    return list(db.scalars(consulta))
