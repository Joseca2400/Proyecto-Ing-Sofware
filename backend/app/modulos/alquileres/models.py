"""Tablas del módulo de alquileres (Sprint 2: tarifario, HU-3.05)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import MONTO

MODALIDADES = ("diaria", "semanal", "mensual", "por_kilometraje")


class Tarifa(Base):
    """Tarifa de alquiler de un tipo de vehículo o, como excepción, de una unidad (VIN).

    Nunca se edita el monto: un cambio es otra tarifa con su propia vigencia, y la anterior se
    cierra (`vigente_hasta`). El contrato copia los valores al firmarse, así que no se altera.
    """

    __tablename__ = "tarifa"
    __table_args__ = (
        CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')", name="ck_tarifa_modalidad"
        ),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_tarifa_moneda"),
        CheckConstraint(
            "(tipo_vehiculo IS NOT NULL AND vin IS NULL) OR (tipo_vehiculo IS NULL AND vin IS NOT NULL)",
            name="ck_tarifa_aplica_a",
        ),
        CheckConstraint(
            "monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0", name="ck_tarifa_montos"
        ),
        CheckConstraint("vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="ck_tarifa_vigencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_vehiculo: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    vin: Mapped[str | None] = mapped_column(ForeignKey("unidad.vin"), nullable=True, index=True)
    modalidad: Mapped[str] = mapped_column(String(20))
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    km_incluido: Mapped[int] = mapped_column(Integer, default=0)
    precio_km_adicional: Mapped[Decimal] = mapped_column(MONTO)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
