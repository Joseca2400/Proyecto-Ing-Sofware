"""Tablas del módulo de facturación y cuentas por cobrar (Sprint 2: clientes, HU-6.01)."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base


class Cliente(Base):
    """Cliente de alquiler, venta o taller, individual o empresa.

    Se identifica con un solo documento: NIT (normalizado, `comun/nit.py`), CUI (13 dígitos) o
    pasaporte con su país. La restricción UNIQUE sobre (tipo, identificación) evita duplicados
    aun con altas simultáneas.
    """

    __tablename__ = "cliente"
    __table_args__ = (
        UniqueConstraint("tipo_identificacion", "identificacion", name="uq_cliente_identificacion"),
        CheckConstraint("tipo IN ('individual', 'empresa')", name="ck_cliente_tipo"),
        CheckConstraint(
            "tipo_identificacion IN ('nit', 'cui', 'pasaporte')", name="ck_cliente_tipo_identificacion"
        ),
        CheckConstraint(
            "(tipo_identificacion = 'pasaporte' AND pais IS NOT NULL)"
            " OR (tipo_identificacion <> 'pasaporte' AND pais IS NULL)",
            name="ck_cliente_pais",
        ),
        CheckConstraint("tipo = 'individual' OR tipo_identificacion = 'nit'", name="ck_cliente_empresa_nit"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    tipo_identificacion: Mapped[str] = mapped_column(String(10))
    identificacion: Mapped[str] = mapped_column(String(30))
    pais: Mapped[str | None] = mapped_column(String(2), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    correo: Mapped[str | None] = mapped_column(String(120), nullable=True)
    agente_retencion_iva: Mapped[bool] = mapped_column(Boolean, default=False)
    agente_retencion_isr: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
