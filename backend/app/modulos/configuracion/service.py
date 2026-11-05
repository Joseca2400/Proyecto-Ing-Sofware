"""Reglas del tipo de cambio (HU-1.06, versión delgada del Sprint 1).

Incluido: carga manual de un valor positivo por fecha y bloqueo cuando falta el de una fecha.
Diferido: consulta automática al servicio del Banguat (adaptador en `comun/`) y corrección
de un tipo ya usado en partidas, con aprobación del gerente financiero.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import TipoCambio

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
