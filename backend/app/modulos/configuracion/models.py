"""Tablas del módulo de configuración.

Equipo B: tipo de cambio (HU-1.06) y transacciones en USD (HU-1.07). El equipo A agrega aquí
el catálogo, las dimensiones y los bancos; el equipo C, el perfil fiscal.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import MONTO, TIPO_CAMBIO

ORIGENES_TIPO_CAMBIO = ("manual", "automatico")


class TipoCambio(Base):
    """Tipo de cambio de referencia del Banguat (quetzales por un dólar) para una fecha."""

    __tablename__ = "tipo_cambio"
    __table_args__ = (
        CheckConstraint("valor > 0", name="ck_tipo_cambio_valor_positivo"),
        CheckConstraint("origen IN ('manual', 'automatico')", name="ck_tipo_cambio_origen"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True, index=True)
    valor: Mapped[Decimal] = mapped_column(TIPO_CAMBIO)
    origen: Mapped[str] = mapped_column(String(10))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TransaccionUSD(Base):
    """Registro de un monto en USD con su tipo de cambio aplicado y el equivalente en quetzales.

    Guarda el triple (monto_usd, tipo_cambio_aplicado, monto_gtq) que exige HU-1.07.
    Cuando se usa un tipo personalizado (distinto del Banguat), la justificación es obligatoria.
    """

    __tablename__ = "transaccion_usd"
    __table_args__ = (
        CheckConstraint("monto_usd > 0", name="ck_transaccion_usd_monto_positivo"),
        CheckConstraint("tipo_cambio_aplicado > 0", name="ck_transaccion_usd_tipo_positivo"),
        CheckConstraint("monto_gtq > 0", name="ck_transaccion_usd_gtq_positivo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    monto_usd: Mapped[Decimal] = mapped_column(MONTO)
    tipo_cambio_aplicado: Mapped[Decimal] = mapped_column(TIPO_CAMBIO)
    monto_gtq: Mapped[Decimal] = mapped_column(MONTO)
    justificacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
