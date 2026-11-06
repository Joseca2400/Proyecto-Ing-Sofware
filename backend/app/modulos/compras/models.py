"""Tablas del módulo de compras (equipo B).

Sprint 1: proveedores (HU-4.01). Después llegan la compra en EE. UU. (HU-4.02), los gastos de
importación (HU-4.04) y las facturas locales (HU-4.09), todas ligadas a un proveedor.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base

TIPOS_PROVEEDOR = ("local", "exterior")
RUBROS_PROVEEDOR = (
    "subasta",
    "dealer",
    "naviera",
    "agente_aduanal",
    "repuestos",
    "seguros",
    "servicios",
    "otros",
)


class Proveedor(Base):
    """Proveedor local (con NIT) o del exterior (con identificación fiscal y país).

    El NIT se guarda normalizado (`comun/nit.py`) y es único; PostgreSQL permite varios NULL en
    una columna UNIQUE, así que los proveedores del exterior no chocan entre sí.
    """

    __tablename__ = "proveedor"
    __table_args__ = (
        CheckConstraint("tipo IN ('local', 'exterior')", name="ck_proveedor_tipo"),
        CheckConstraint(
            "rubro IN ('subasta', 'dealer', 'naviera', 'agente_aduanal', 'repuestos', 'seguros', "
            "'servicios', 'otros')",
            name="ck_proveedor_rubro",
        ),
        CheckConstraint("moneda_habitual IN ('GTQ', 'USD')", name="ck_proveedor_moneda"),
        CheckConstraint("dias_credito >= 0", name="ck_proveedor_dias_credito"),
        CheckConstraint(
            "(tipo = 'local' AND nit IS NOT NULL AND identificacion_fiscal IS NULL AND pais IS NULL)"
            " OR (tipo = 'exterior' AND nit IS NULL AND identificacion_fiscal IS NOT NULL"
            " AND pais IS NOT NULL)",
            name="ck_proveedor_identificacion",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    nit: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True)
    identificacion_fiscal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(2), nullable=True)
    rubro: Mapped[str] = mapped_column(String(20))
    moneda_habitual: Mapped[str] = mapped_column(String(3))
    dias_credito: Mapped[int] = mapped_column(Integer)
    banco: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cuenta_bancaria: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
