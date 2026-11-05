"""Reglas del módulo de configuración (Sprint 1, equipo B).

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
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal, convertir, redondear
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import TipoCambio, TransaccionUSD

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
    consulta = select(TransaccionUSD).order_by(
        TransaccionUSD.fecha.desc(), TransaccionUSD.id.desc()
    )
    if desde:
        consulta = consulta.where(TransaccionUSD.fecha >= desde)
    if hasta:
        consulta = consulta.where(TransaccionUSD.fecha <= hasta)
    return list(db.scalars(consulta))
