"""Tablas del módulo de alquileres (equipo C).

Sprint 1: tarifario (HU-3.05). Después llegan el contrato (HU-3.06), los depósitos (HU-3.07) y el
cierre (HU-3.08), que copian el precio del tarifario al firmarse: cambiar una tarifa después no
toca los contratos ya firmados (criterio 4).
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.comun.db import Base
from app.comun.dinero import MONTO

MODALIDADES = ("diaria", "semanal", "mensual", "kilometraje")
NATURALEZAS_CONCEPTO = ("ingreso", "deposito", "reintegro")


class TemporadaAlquiler(Base):
    """Lista de precios con fechas (temporada alta, promoción, tarifa corporativa…).

    Las tarifas sin temporada son la lista base; una temporada activa la reemplaza en sus
    fechas. Dos temporadas activas no se traslapan, para que la tarifa aplicable sea única.
    """

    __tablename__ = "temporada_alquiler"
    __table_args__ = (CheckConstraint("fecha_fin >= fecha_inicio", name="ck_temporada_alquiler_fechas"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TarifaAlquiler(Base):
    """Precio de alquiler por tipo de vehículo o, como excepción, por unidad (VIN).

    El monto incluye IVA, como exige la ley para precios al público; la factura (HU-6.02) separa
    base e IVA con la tasa del perfil fiscal. Las tarifas no se modifican: un cambio agrega una
    fila con su `vigente_desde`, igual que el perfil fiscal.
    """

    __tablename__ = "tarifa_alquiler"
    __table_args__ = (
        CheckConstraint("(tipo_vehiculo IS NULL) <> (vin IS NULL)", name="ck_tarifa_alquiler_alcance"),
        CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'kilometraje')",
            name="ck_tarifa_alquiler_modalidad",
        ),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_tarifa_alquiler_moneda"),
        CheckConstraint("monto > 0", name="ck_tarifa_alquiler_monto"),
        CheckConstraint("km_incluido IS NULL OR km_incluido >= 0", name="ck_tarifa_alquiler_km"),
        CheckConstraint(
            "costo_km_adicional IS NULL OR costo_km_adicional >= 0", name="ck_tarifa_alquiler_costo_km"
        ),
        CheckConstraint(
            "modalidad <> 'kilometraje' OR (km_incluido IS NOT NULL AND costo_km_adicional IS NOT NULL)",
            name="ck_tarifa_alquiler_kilometraje",
        ),
        UniqueConstraint(
            "temporada_id",
            "tipo_vehiculo",
            "vin",
            "modalidad",
            "moneda",
            "vigente_desde",
            name="uq_tarifa_alquiler_version",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    temporada_id: Mapped[int | None] = mapped_column(
        ForeignKey("temporada_alquiler.id"), nullable=True, index=True
    )
    tipo_vehiculo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, index=True)
    modalidad: Mapped[str] = mapped_column(String(15))
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    # Kilómetros incluidos por período (por contrato en la modalidad por kilometraje); vacío es
    # kilometraje libre.
    km_incluido: Mapped[int | None] = mapped_column(Integer, nullable=True)
    costo_km_adicional: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    temporada: Mapped[TemporadaAlquiler | None] = relationship(lazy="joined")


class ConceptoAlquiler(Base):
    """Cargo adicional del contrato (GPS, silla de bebé, combustible, depósito, multas…) y cómo
    tributa: un ingreso puede llevar IVA o no; un depósito es un pasivo y un reintegro es dinero
    de terceros: ninguno de los dos es ingreso ni lleva IVA."""

    __tablename__ = "concepto_alquiler"
    __table_args__ = (
        CheckConstraint(
            "naturaleza IN ('ingreso', 'deposito', 'reintegro')", name="ck_concepto_alquiler_naturaleza"
        ),
        CheckConstraint("naturaleza = 'ingreso' OR NOT aplica_iva", name="ck_concepto_alquiler_iva"),
        CheckConstraint(
            "(precio_sugerido IS NULL) = (moneda IS NULL)", name="ck_concepto_alquiler_precio_moneda"
        ),
        CheckConstraint("precio_sugerido IS NULL OR precio_sugerido > 0", name="ck_concepto_alquiler_precio"),
        CheckConstraint("moneda IS NULL OR moneda IN ('GTQ', 'USD')", name="ck_concepto_alquiler_moneda"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    naturaleza: Mapped[str] = mapped_column(String(10))
    aplica_iva: Mapped[bool] = mapped_column(Boolean)
    # Vacío cuando el monto cambia cada vez (una multa); el contrato lo captura.
    precio_sugerido: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    moneda: Mapped[str | None] = mapped_column(String(3), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
