"""Tablas del módulo de unidades (equipo B): la unidad identificada por su VIN y el historial de sus
cambios de estado (HU-1.05). El VIN es el hilo conductor: compras, taller, alquiler y venta se ligan
a esta tabla por su VIN.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import MONTO

ESTADOS = (
    "en_transito",
    "en_aduana",
    "en_taller",
    "lista",
    "en_flota",
    "alquilada",
    "en_venta",
    "vendida",
    "recuperada",
)
_ESTADOS_SQL = ", ".join(f"'{estado}'" for estado in ESTADOS)


class Unidad(Base):
    """Vehículo con su ficha mínima y su estado vigente (uno solo a la vez).

    La línea de negocio se valida contra `configuracion` (HU-1.04) en el service, sin CHECK propio,
    para no mantener dos listas. Placa y número de motor llegan en un sprint posterior.
    """

    __tablename__ = "unidad"
    __table_args__ = (
        CheckConstraint("vin ~ '^[A-HJ-NPR-Z0-9]{17}$'", name="ck_unidad_vin"),
        CheckConstraint(f"estado IN ({_ESTADOS_SQL})", name="ck_unidad_estado"),
        CheckConstraint("modelo BETWEEN 1900 AND 2100", name="ck_unidad_modelo"),
        CheckConstraint("kilometraje IS NULL OR kilometraje >= 0", name="ck_unidad_kilometraje"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(String(17), unique=True)
    marca: Mapped[str] = mapped_column(String(50), index=True)
    linea: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[int] = mapped_column(Integer)
    color: Mapped[str] = mapped_column(String(30))
    tipo_vehiculo: Mapped[str] = mapped_column(String(20))
    linea_negocio: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), index=True)
    # Último kilometraje conocido; lo actualiza la devolución de un alquiler (HU-3.08).
    kilometraje: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CambioEstadoUnidad(Base):
    """Un renglón por cada estado que tuvo la unidad, desde el alta (sin estado anterior).

    `usuario_id` queda vacío mientras las rutas no exijan sesión; la bitácora (HU-1.11) también
    registra el cambio.
    """

    __tablename__ = "cambio_estado_unidad"
    __table_args__ = (
        CheckConstraint(f"estado_nuevo IN ({_ESTADOS_SQL})", name="ck_cambio_estado_unidad_nuevo"),
        CheckConstraint(
            f"estado_anterior IS NULL OR (estado_anterior IN ({_ESTADOS_SQL})"
            " AND estado_anterior <> estado_nuevo)",
            name="ck_cambio_estado_unidad_anterior",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidad.id", ondelete="CASCADE"), index=True)
    estado_anterior: Mapped[str | None] = mapped_column(String(20), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(20))
    documento: Mapped[str] = mapped_column(String(200))
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AltaFlota(Base):
    """Alta de la unidad como activo fijo de la flota (HU-3.01): una por VIN, con el costo de su
    hoja de costo (HU-4.08) congelado y la partida que lo trasladó a "activo fijo – flota"."""

    __tablename__ = "alta_flota"
    __table_args__ = (
        UniqueConstraint("vin", name="uq_alta_flota_vin"),
        UniqueConstraint("partida_id", name="uq_alta_flota_partida"),
        CheckConstraint("costo > 0", name="ck_alta_flota_costo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(String(17), ForeignKey("unidad.vin", name="fk_alta_flota_vin_unidad"))
    fecha: Mapped[date] = mapped_column(Date)
    costo: Mapped[Decimal] = mapped_column(MONTO)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partida.id", name="fk_alta_flota_partida"))
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
