"""Tablas del módulo de configuración.

Equipo B: tipo de cambio (HU-1.06). El equipo A agrega aquí el catálogo, las dimensiones
y los bancos; el equipo C, el perfil fiscal.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import TIPO_CAMBIO

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
