"""Reglas del módulo de taller (Sprint 2, versión delgada).

HU-5.02 (incluido): tarifa horaria de costo general en quetzales con vigencia. Un cambio es una
fila nueva y aplica solo a las horas con fecha igual o posterior a su `vigente_desde` (criterio 3).
HU-5.02 (diferido): tarifa por mecánico o especialidad (criterio 1) y tarifa de venta para la
postventa facturable (criterio 2), con la postventa (Sprint 5).
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.modulos.taller.models import TarifaManoObra
from app.modulos.taller.schemas import TarifaEntrada

_LIMITE_MONTO = Decimal(10) ** 12


def _monto(texto: str, campo: str) -> Decimal:
    """Número positivo enviado como texto, con hasta 6 decimales; nunca float."""
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio(f"{campo} no es un número válido") from None
    if not valor.is_finite():
        raise ErrorNegocio(f"{campo} no es un número válido")
    if -valor.as_tuple().exponent > 6:  # type: ignore[operator]
        raise ErrorNegocio(f"{campo} admite hasta 6 decimales")
    if valor <= 0:
        raise ErrorNegocio(f"{campo} debe ser mayor que cero")
    if valor >= _LIMITE_MONTO:
        raise ErrorNegocio(f"{campo} excede el máximo permitido")
    return valor


# ── HU-5.02: tarifas de mano de obra ──────────────────────────────────────────


def crear_tarifa(db: Session, datos: TarifaEntrada, usuario_id: int | None = None) -> TarifaManoObra:
    tarifa_hora = _monto(datos.tarifa_hora, "La tarifa por hora")
    if db.scalar(select(TarifaManoObra.id).where(TarifaManoObra.vigente_desde == datos.vigente_desde)):
        raise ErrorNegocio(f"Ya existe una tarifa vigente desde el {datos.vigente_desde}", 409)
    tarifa = TarifaManoObra(tarifa_hora=tarifa_hora, vigente_desde=datos.vigente_desde, creado_por=usuario_id)
    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)
    return tarifa


def listar_tarifas(db: Session) -> list[TarifaManoObra]:
    """De la vigencia más reciente a la más antigua."""
    return list(db.scalars(select(TarifaManoObra).order_by(TarifaManoObra.vigente_desde.desc())))


def tarifa_costo_vigente(db: Session, fecha: date) -> Decimal:
    """Tarifa horaria de costo en vigor en `fecha` (la de `vigente_desde` más reciente hasta ella)."""
    tarifa = db.scalar(
        select(TarifaManoObra.tarifa_hora)
        .where(TarifaManoObra.vigente_desde <= fecha)
        .order_by(TarifaManoObra.vigente_desde.desc())
        .limit(1)
    )
    if tarifa is None:
        raise ErrorNegocio(
            f"No hay tarifa de mano de obra vigente al {fecha}: defínala en las tarifas de taller", 409
        )
    return tarifa
