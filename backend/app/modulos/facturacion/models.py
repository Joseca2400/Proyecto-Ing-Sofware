"""Tablas del módulo de facturación y cuentas por cobrar (Sprint 2: clientes, HU-6.01; facturas FEL
y su cuenta por cobrar, HU-6.02)."""

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
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.comun.db import Base
from app.comun.dinero import MONTO, TIPO_CAMBIO


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


class Factura(Base):
    """Factura FEL emitida (HU-6.02). Se guarda antes de enviarla al certificador (`pendiente`) y
    queda `certificada`, con serie, número, autorización y XML, o `rechazada`, con el motivo y sin
    efecto contable. Montos en la moneda de la factura; `total_gtq` es su equivalente en quetzales.
    Sin cliente es a Consumidor Final."""

    __tablename__ = "factura"
    __table_args__ = (
        UniqueConstraint("partida_id", name="uq_factura_partida"),
        CheckConstraint("estado IN ('pendiente', 'certificada', 'rechazada')", name="ck_factura_estado"),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_factura_moneda"),
        CheckConstraint(
            "(moneda = 'USD' AND tipo_cambio > 0) OR (moneda = 'GTQ' AND tipo_cambio IS NULL)",
            name="ck_factura_tipo_cambio",
        ),
        CheckConstraint("total > 0 AND total = base + iva", name="ck_factura_total"),
        CheckConstraint("(origen_tipo IS NULL) = (origen_id IS NULL)", name="ck_factura_origen"),
        CheckConstraint("partida_id IS NULL OR estado = 'certificada'", name="ck_factura_partida"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"), nullable=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    moneda: Mapped[str] = mapped_column(String(3))
    tipo_cambio: Mapped[Decimal | None] = mapped_column(TIPO_CAMBIO, nullable=True)
    origen_tipo: Mapped[str | None] = mapped_column(String(20), nullable=True)
    origen_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dias_credito: Mapped[int] = mapped_column(Integer)
    emisor_nit: Mapped[str] = mapped_column(String(13))
    emisor_nombre: Mapped[str] = mapped_column(String(200))
    receptor_id: Mapped[str] = mapped_column(String(30))
    receptor_nombre: Mapped[str] = mapped_column(String(200))
    base: Mapped[Decimal] = mapped_column(MONTO)
    iva: Mapped[Decimal] = mapped_column(MONTO)
    total: Mapped[Decimal] = mapped_column(MONTO)
    total_gtq: Mapped[Decimal] = mapped_column(MONTO)
    estado: Mapped[str] = mapped_column(String(12), default="pendiente")
    serie: Mapped[str | None] = mapped_column(String(20), nullable=True)
    numero: Mapped[str | None] = mapped_column(String(20), nullable=True)
    autorizacion: Mapped[str | None] = mapped_column(String(36), nullable=True)
    certificada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    xml: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_rechazo: Mapped[str | None] = mapped_column(String(500), nullable=True)
    partida_id: Mapped[int | None] = mapped_column(
        ForeignKey("partida.id", name="fk_factura_partida"), nullable=True
    )
    creado_por: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lineas: Mapped[list["LineaFactura"]] = relationship(
        order_by="LineaFactura.numero_linea", cascade="all, delete-orphan", lazy="selectin"
    )
    cuenta_por_cobrar: Mapped["CuentaPorCobrar | None"] = relationship(
        back_populates="factura", uselist=False, lazy="selectin"
    )


class LineaFactura(Base):
    """Línea de la factura. El precio unitario incluye IVA; total = cantidad × precio, redondeado,
    y de él se derivan la base y el IVA."""

    __tablename__ = "linea_factura"
    __table_args__ = (
        UniqueConstraint("factura_id", "numero_linea", name="uq_linea_factura_numero"),
        CheckConstraint("cantidad > 0 AND precio_unitario > 0", name="ck_linea_factura_cantidad"),
        CheckConstraint("total = base + iva", name="ck_linea_factura_total"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("factura.id"), index=True)
    numero_linea: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(String(300))
    cantidad: Mapped[Decimal] = mapped_column(MONTO)
    precio_unitario: Mapped[Decimal] = mapped_column(MONTO)
    total: Mapped[Decimal] = mapped_column(MONTO)
    base: Mapped[Decimal] = mapped_column(MONTO)
    iva: Mapped[Decimal] = mapped_column(MONTO)
    linea_negocio: Mapped[str] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True)


class CuentaPorCobrar(Base):
    """Saldo a cargo del cliente que nace de una factura certificada, por su total y en su moneda.
    Los cobros (HU-6.07) llegan después."""

    __tablename__ = "cuenta_por_cobrar"
    __table_args__ = (
        UniqueConstraint("factura_id", name="uq_cuenta_por_cobrar_factura"),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_cuenta_por_cobrar_moneda"),
        CheckConstraint("monto > 0", name="ck_cuenta_por_cobrar_monto"),
        CheckConstraint("saldo >= 0 AND saldo <= monto", name="ck_cuenta_por_cobrar_saldo"),
        CheckConstraint("fecha_vencimiento >= fecha", name="ck_cuenta_por_cobrar_vencimiento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("factura.id"))
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("cliente.id"), nullable=True, index=True)
    fecha: Mapped[date] = mapped_column(Date)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, index=True)
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    saldo: Mapped[Decimal] = mapped_column(MONTO)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    factura: Mapped[Factura] = relationship(back_populates="cuenta_por_cobrar")
