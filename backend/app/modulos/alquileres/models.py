"""Tablas del módulo de alquileres (Sprint 2: tarifario, HU-3.05; contratos, HU-3.06)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, SmallInteger, String, func
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


class ContratoAlquiler(Base):
    """Contrato de alquiler de una unidad (VIN) a un cliente.

    Copia los valores de la tarifa vigente el día de salida (`tarifa_*`, `km_incluido`,
    `precio_km_adicional`): un cambio posterior del tarifario no lo altera. `tarifa_id` queda solo
    como referencia. El combustible se mide en octavos de tanque (0 a 8).
    """

    __tablename__ = "contrato_alquiler"
    __table_args__ = (
        CheckConstraint("estado IN ('abierto', 'cerrado')", name="ck_contrato_alquiler_estado"),
        CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')",
            name="ck_contrato_alquiler_modalidad",
        ),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_contrato_alquiler_moneda"),
        CheckConstraint(
            "combustible_salida BETWEEN 0 AND 8 AND km_salida >= 0", name="ck_contrato_alquiler_salida"
        ),
        CheckConstraint(
            "tarifa_monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0 AND deposito_esperado >= 0"
            " AND dias_previstos >= 1 AND monto_estimado > 0",
            name="ck_contrato_alquiler_montos",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    vin: Mapped[str] = mapped_column(ForeignKey("unidad.vin"), index=True)
    salida: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    devolucion_prevista: Mapped[date] = mapped_column(Date)
    tarifa_id: Mapped[int] = mapped_column(ForeignKey("tarifa.id"))
    modalidad: Mapped[str] = mapped_column(String(20))
    moneda: Mapped[str] = mapped_column(String(3))
    tarifa_monto: Mapped[Decimal] = mapped_column(MONTO)
    km_incluido: Mapped[int] = mapped_column(Integer)
    precio_km_adicional: Mapped[Decimal] = mapped_column(MONTO)
    km_salida: Mapped[int] = mapped_column(Integer)
    combustible_salida: Mapped[int] = mapped_column(SmallInteger)
    deposito_esperado: Mapped[Decimal] = mapped_column(MONTO)
    dias_previstos: Mapped[int] = mapped_column(Integer)
    monto_estimado: Mapped[Decimal] = mapped_column(MONTO)
    estado: Mapped[str] = mapped_column(String(10), default="abierto", index=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
