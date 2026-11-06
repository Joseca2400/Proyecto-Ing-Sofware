"""Tablas del módulo de compras (equipo B).

Sprint 1: proveedores (HU-4.01) y facturas de compras y gastos locales con su cuenta por pagar
(HU-4.09). Después llegan la compra en EE. UU. (HU-4.02) y los gastos de importación (HU-4.04),
todas ligadas a un proveedor.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
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
REGIMENES_PROVEEDOR = ("general", "pequeno_contribuyente")
LINEAS_NEGOCIO = ("alquiler", "venta", "taller", "financiamiento", "administracion")


class Proveedor(Base):
    """Proveedor local (con NIT y régimen de IVA) o del exterior (con identificación fiscal y país).

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
        CheckConstraint(
            "(tipo = 'local' AND regimen IN ('general', 'pequeno_contribuyente'))"
            " OR (tipo = 'exterior' AND regimen IS NULL)",
            name="ck_proveedor_regimen",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(10))
    nombre: Mapped[str] = mapped_column(String(200), index=True)
    nit: Mapped[str | None] = mapped_column(String(13), unique=True, nullable=True)
    identificacion_fiscal: Mapped[str | None] = mapped_column(String(50), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(2), nullable=True)
    # Régimen de IVA del proveedor local (HU-4.01, criterio 2): el pequeño contribuyente no da
    # crédito fiscal (HU-4.09). Los del exterior no tienen régimen guatemalteco.
    regimen: Mapped[str | None] = mapped_column(String(25), nullable=True)
    rubro: Mapped[str] = mapped_column(String(20))
    moneda_habitual: Mapped[str] = mapped_column(String(3))
    dias_credito: Mapped[int] = mapped_column(Integer)
    banco: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cuenta_bancaria: Mapped[str | None] = mapped_column(String(50), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FacturaCompra(Base):
    """DTE FEL recibido de un proveedor local (HU-4.09), en quetzales.

    El mismo DTE no se registra dos veces para el mismo proveedor: ni por serie y número ni por
    número de autorización. El régimen del proveedor se copia al registrar, porque decide el
    crédito fiscal de esta factura aunque el proveedor cambie de régimen después.
    """

    __tablename__ = "factura_compra"
    __table_args__ = (
        UniqueConstraint("proveedor_id", "serie", "numero", name="uq_factura_compra_serie_numero"),
        UniqueConstraint("proveedor_id", "autorizacion", name="uq_factura_compra_autorizacion"),
        CheckConstraint(
            "regimen_proveedor IN ('general', 'pequeno_contribuyente')",
            name="ck_factura_compra_regimen",
        ),
        CheckConstraint("total_base > 0 AND total_iva >= 0", name="ck_factura_compra_montos"),
        CheckConstraint("total = total_base + total_iva", name="ck_factura_compra_total"),
        CheckConstraint(
            "(regimen_proveedor = 'general' AND credito_fiscal = total_iva)"
            " OR (regimen_proveedor = 'pequeno_contribuyente' AND credito_fiscal = 0)",
            name="ck_factura_compra_credito_fiscal",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedor.id"), index=True)
    serie: Mapped[str] = mapped_column(String(20))
    numero: Mapped[str] = mapped_column(String(20))
    autorizacion: Mapped[str] = mapped_column(String(36))
    fecha: Mapped[date] = mapped_column(Date, index=True)
    regimen_proveedor: Mapped[str] = mapped_column(String(25))
    total_base: Mapped[Decimal] = mapped_column(MONTO)
    total_iva: Mapped[Decimal] = mapped_column(MONTO)
    credito_fiscal: Mapped[Decimal] = mapped_column(MONTO)
    total: Mapped[Decimal] = mapped_column(MONTO)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    proveedor: Mapped[Proveedor] = relationship(lazy="joined")
    lineas: Mapped[list["LineaFacturaCompra"]] = relationship(
        back_populates="factura",
        order_by="LineaFacturaCompra.numero_linea",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    cuenta_por_pagar: Mapped["CuentaPorPagar"] = relationship(
        back_populates="factura", uselist=False, lazy="joined"
    )


class LineaFacturaCompra(Base):
    """Línea del DTE con su imputación: cuenta, línea de negocio y, cuando aplique, el VIN.

    Mientras no existan el catálogo (HU-1.02), las dimensiones (HU-1.04) ni las unidades
    (HU-1.05), la cuenta y el VIN se guardan como texto validado solo en su forma.
    """

    __tablename__ = "linea_factura_compra"
    __table_args__ = (
        UniqueConstraint("factura_id", "numero_linea", name="uq_linea_factura_compra_numero"),
        CheckConstraint(
            "linea_negocio IN ('alquiler', 'venta', 'taller', 'financiamiento', 'administracion')",
            name="ck_linea_factura_compra_linea_negocio",
        ),
        CheckConstraint("base > 0 AND iva >= 0", name="ck_linea_factura_compra_montos"),
        CheckConstraint("vin IS NULL OR length(vin) = 17", name="ck_linea_factura_compra_vin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("factura_compra.id", ondelete="CASCADE"))
    numero_linea: Mapped[int] = mapped_column(Integer)
    descripcion: Mapped[str] = mapped_column(String(300))
    cuenta: Mapped[str] = mapped_column(String(20))
    linea_negocio: Mapped[str] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, index=True)
    base: Mapped[Decimal] = mapped_column(MONTO)
    iva: Mapped[Decimal] = mapped_column(MONTO)

    factura: Mapped[FacturaCompra] = relationship(back_populates="lineas")


class CuentaPorPagar(Base):
    """Saldo a favor de un proveedor. Hoy nace solo de una factura local (HU-4.09) por su total;
    la compra en EE. UU. (HU-4.02, en USD) y los pagos (HU-4.14) llegan después."""

    __tablename__ = "cuenta_por_pagar"
    __table_args__ = (
        UniqueConstraint("factura_compra_id", name="uq_cuenta_por_pagar_factura"),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_cuenta_por_pagar_moneda"),
        CheckConstraint("monto > 0", name="ck_cuenta_por_pagar_monto"),
        CheckConstraint("saldo >= 0 AND saldo <= monto", name="ck_cuenta_por_pagar_saldo"),
        CheckConstraint("fecha_vencimiento >= fecha", name="ck_cuenta_por_pagar_vencimiento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedor.id"), index=True)
    factura_compra_id: Mapped[int] = mapped_column(ForeignKey("factura_compra.id"))
    fecha: Mapped[date] = mapped_column(Date)
    fecha_vencimiento: Mapped[date] = mapped_column(Date, index=True)
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    saldo: Mapped[Decimal] = mapped_column(MONTO)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    factura: Mapped[FacturaCompra] = relationship(back_populates="cuenta_por_pagar")
