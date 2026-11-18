"""Tablas del módulo de taller (Sprint 2, versión delgada)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import MONTO


class TarifaManoObra(Base):
    """Tarifa horaria de costo (HU-5.02). Un cambio es una fila nueva: nunca se edita una vigente."""

    __tablename__ = "tarifa_mano_obra"
    __table_args__ = (CheckConstraint("tarifa_hora > 0", name="ck_tarifa_mano_obra_tarifa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tarifa_hora: Mapped[Decimal] = mapped_column(MONTO)
    vigente_desde: Mapped[date] = mapped_column(Date, unique=True)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
