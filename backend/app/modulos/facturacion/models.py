"""Tablas del módulo de facturación (equipo C).

Sprint 1: clientes (HU-6.01). Después llegan la factura FEL (HU-6.02) y las cuentas por cobrar,
todas ligadas a un cliente.
"""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base

TIPOS_CLIENTE = ("individual", "empresa")


class Cliente(Base):
    """Cliente de alquiler, venta o taller: persona individual o empresa.

    Se identifica con NIT o CUI, o con pasaporte y país si es extranjero. El NIT se guarda
    normalizado (`comun/nit.py`); NIT, CUI y pasaporte por país son únicos (criterio 5).
    PostgreSQL permite varios NULL en una columna UNIQUE, así que los campos vacíos no chocan.
    """

    __tablename__ = "cliente"
    __table_args__ = (
        CheckConstraint("tipo IN ('individual', 'empresa')", name="ck_cliente_tipo"),
        CheckConstraint(
            "nit IS NOT NULL OR cui IS NOT NULL OR pasaporte IS NOT NULL",
            name="ck_cliente_identificacion",
        ),
        CheckConstraint("(pasaporte IS NULL) = (pais IS NULL)", name="ck_cliente_pasaporte_pais"),
        CheckConstraint("tipo = 'individual' OR nit IS NOT NULL", name="ck_cliente_empresa_nit"),
        CheckConstraint("cui IS NULL OR cui ~ '^[0-9]{13}$'", name="ck_cliente_cui"),
        UniqueConstraint("pais", "pasaporte", name="uq_cliente_pasaporte"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    nit: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True)
    cui: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True)
    pasaporte: Mapped[str | None] = mapped_column(String(30), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(2), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # Criterio 3: si el cliente nos retiene IVA o ISR, las retenciones que nos haga se registran
    # al cobrarle (HU-6.07).
    agente_retencion_iva: Mapped[bool] = mapped_column(Boolean, default=False)
    agente_retencion_isr: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
