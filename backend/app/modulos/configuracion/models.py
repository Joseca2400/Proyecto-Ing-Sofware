"""Tablas del módulo de configuración.

Equipo A: catálogo de cuentas y dimensiones analíticas (HU-1.02, HU-1.04).
Equipo B: tipo de cambio (HU-1.06) y transacciones en USD (HU-1.07).
Equipo C: perfil fiscal de la empresa y tasas impositivas con vigencia (HU-1.01).
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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base
from app.comun.dinero import MONTO, TIPO_CAMBIO

# ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────


class Cuenta(Base):
    """Cuenta contable. Las de detalle reciben movimientos; las de agrupación suman a sus hijas."""

    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    naturaleza: Mapped[str] = mapped_column(String(20))
    nivel: Mapped[int]
    padre_id: Mapped[int | None] = mapped_column(ForeignKey("cuentas.id"), index=True)
    es_detalle: Mapped[bool] = mapped_column(default=True)
    monetaria_usd: Mapped[bool] = mapped_column(default=False)
    # Dimensiones analíticas (HU-1.04): solo tienen sentido en cuentas de detalle.
    linea_obligatoria: Mapped[bool] = mapped_column(default=False)
    vin: Mapped[str] = mapped_column(String(20), default="no_aplica")
    linea_defecto: Mapped[str | None] = mapped_column(String(20))


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────

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


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────


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


# ── HU-1.01: perfil fiscal de la empresa ──────────────────────────────────────

REGIMENES_ISR = ("opcional_simplificado", "sobre_utilidades")
TIPOS_TASA = (
    "IVA_GENERAL",
    "ISR_SIMPLIFICADO_1",
    "ISR_SIMPLIFICADO_2",
    "ISR_UTILIDADES",
    "ISO",
    "UMBRAL_CF",
)


class PerfilFiscal(Base):
    """Una versión del perfil fiscal, vigente desde `vigente_desde` hasta la siguiente versión.

    Las versiones no se modifican: cada cambio agrega una fila nueva (criterio 4), así una
    transacción anterior a la fecha de un cambio sigue usando el perfil que tenía.
    """

    __tablename__ = "perfil_fiscal"
    __table_args__ = (
        CheckConstraint(
            "regimen_isr IN ('opcional_simplificado', 'sobre_utilidades')",
            name="ck_perfil_fiscal_regimen",
        ),
        CheckConstraint("establecimiento_sat >= 1", name="ck_perfil_fiscal_establecimiento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vigente_desde: Mapped[date] = mapped_column(Date, unique=True)
    razon_social: Mapped[str] = mapped_column(String(200))
    nombre_comercial: Mapped[str] = mapped_column(String(200))
    nit: Mapped[str] = mapped_column(String(13))
    direccion_fiscal: Mapped[str] = mapped_column(String(300))
    establecimiento_sat: Mapped[int] = mapped_column(Integer)
    regimen_isr: Mapped[str] = mapped_column(String(25))
    agente_retencion_iva: Mapped[bool] = mapped_column(Boolean)
    agente_retencion_isr: Mapped[bool] = mapped_column(Boolean)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TasaImpositiva(Base):
    """Tasa (fracción: 0.12 es el 12 %) o monto límite de un impuesto, vigente desde una fecha.

    Igual que el perfil, cada cambio de ley agrega una fila: las facturas y las cuotas de
    crédito ya calculadas conservan la tasa de su fecha. `monto_limite` es el tope del primer
    tramo del ISR simplificado (Q30,000) y el umbral para facturar a Consumidor Final.
    """

    __tablename__ = "tasa_impositiva"
    __table_args__ = (
        UniqueConstraint("tipo", "vigente_desde", name="uq_tasa_impositiva_tipo_fecha"),
        CheckConstraint(
            "tipo IN ('IVA_GENERAL', 'ISR_SIMPLIFICADO_1', 'ISR_SIMPLIFICADO_2', 'ISR_UTILIDADES', "
            "'ISO', 'UMBRAL_CF')",
            name="ck_tasa_impositiva_tipo",
        ),
        CheckConstraint("tasa IS NULL OR (tasa > 0 AND tasa <= 1)", name="ck_tasa_impositiva_tasa"),
        CheckConstraint("monto_limite IS NULL OR monto_limite > 0", name="ck_tasa_impositiva_limite"),
        CheckConstraint("tasa IS NOT NULL OR monto_limite IS NOT NULL", name="ck_tasa_impositiva_valor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String(25), index=True)
    tasa: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    monto_limite: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    vigente_desde: Mapped[date] = mapped_column(Date)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
