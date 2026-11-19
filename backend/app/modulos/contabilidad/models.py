"""Tablas del motor contable: partidas de diario y sus líneas (HU-2.01, HU-2.02, HU-2.03).

Solo este módulo crea partidas (regla 3 de la arquitectura). La cuenta de cada línea es una
llave foránea a `cuentas`, sin importar los models de `configuracion`.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.comun.db import Base
from app.comun.dinero import MONTO, TIPO_CAMBIO

ESTADOS = ("borrador", "en_revision", "contabilizada", "devuelta")
ORIGENES = ("manual", "automatica")


class Partida(Base):
    """Partida de diario. Nace en borrador; el correlativo se asigna al contabilizarse.

    Las automáticas (HU-2.03) quedan ligadas al documento que las originó y no se repiten
    para el mismo documento. Una vez contabilizada, la base impide modificarla o borrarla.
    """

    __tablename__ = "partida"
    __table_args__ = (
        # Una por documento; la reversión (HU-2.05) conserva el documento de la original.
        Index(
            "uq_partida_documento",
            "documento_tipo",
            "documento_id",
            unique=True,
            postgresql_where=text("revierte_a IS NULL"),
        ),
        UniqueConstraint("revierte_a", name="uq_partida_revierte_a"),
        CheckConstraint(
            "estado IN ('borrador', 'en_revision', 'contabilizada', 'devuelta')", name="ck_partida_estado"
        ),
        CheckConstraint("origen IN ('manual', 'automatica')", name="ck_partida_origen"),
        CheckConstraint("(estado = 'contabilizada') = (numero IS NOT NULL)", name="ck_partida_numero"),
        CheckConstraint(
            "(origen = 'automatica') = (documento_tipo IS NOT NULL AND documento_id IS NOT NULL)",
            name="ck_partida_documento",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int | None] = mapped_column(Integer, unique=True)
    fecha: Mapped[date] = mapped_column(Date, index=True)
    concepto: Mapped[str] = mapped_column(String(300))
    documento_soporte: Mapped[str | None] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(15), default="borrador", index=True)
    origen: Mapped[str] = mapped_column(String(10), default="manual")
    documento_tipo: Mapped[str | None] = mapped_column(String(30))
    documento_id: Mapped[str | None] = mapped_column(String(50))
    comentario: Mapped[str | None] = mapped_column(String(300))
    creado_por: Mapped[int | None] = mapped_column(Integer)
    contabilizada_por: Mapped[int | None] = mapped_column(Integer)
    contabilizada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # HU-2.05: el vínculo vive en la reversión; la original contabilizada no se modifica.
    revierte_a: Mapped[int | None] = mapped_column(ForeignKey("partida.id"))

    lineas: Mapped[list["LineaPartida"]] = relationship(
        back_populates="partida",
        order_by="LineaPartida.numero_linea",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reversion: Mapped["Partida | None"] = relationship(
        remote_side="Partida.revierte_a", uselist=False, viewonly=True, lazy="selectin"
    )

    @property
    def revertida_por(self) -> int | None:
        """Id de la partida que revierte a esta, si la hay."""
        return self.reversion.id if self.reversion else None


class LineaPartida(Base):
    """Línea con su cuenta, el lado (debe o haber) y siempre el equivalente en quetzales.

    En una línea en USD se conserva el monto original y el tipo de cambio aplicado.
    """

    __tablename__ = "linea_partida"
    __table_args__ = (
        UniqueConstraint("partida_id", "numero_linea", name="uq_linea_partida_numero"),
        CheckConstraint(
            "(debe > 0 AND haber = 0) OR (haber > 0 AND debe = 0)", name="ck_linea_partida_un_lado"
        ),
        CheckConstraint(
            "(moneda = 'GTQ' AND monto_usd IS NULL AND tipo_cambio IS NULL)"
            " OR (moneda = 'USD' AND monto_usd IS NOT NULL AND tipo_cambio IS NOT NULL"
            " AND monto_usd > 0 AND tipo_cambio > 0)",
            name="ck_linea_partida_moneda",
        ),
        CheckConstraint("vin IS NULL OR length(vin) = 17", name="ck_linea_partida_vin"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partida.id", ondelete="CASCADE"))
    numero_linea: Mapped[int] = mapped_column(Integer)
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"), index=True)
    debe: Mapped[Decimal] = mapped_column(MONTO)
    haber: Mapped[Decimal] = mapped_column(MONTO)
    moneda: Mapped[str] = mapped_column(String(3), default="GTQ")
    monto_usd: Mapped[Decimal | None] = mapped_column(MONTO)
    tipo_cambio: Mapped[Decimal | None] = mapped_column(TIPO_CAMBIO)
    linea_negocio: Mapped[str | None] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17), index=True)

    partida: Mapped[Partida] = relationship(back_populates="lineas")


class ReglaContabilizacion(Base):
    """Cuenta que usa un tipo de documento para un concepto de su partida automática (HU-2.03).

    Guarda el código de la cuenta y no su id: las reglas se siembran en las migraciones, antes de
    que exista el catálogo, y el contador las ajusta después. Sin cuenta válida no hay documento.
    """

    __tablename__ = "regla_contabilizacion"
    __table_args__ = (UniqueConstraint("documento_tipo", "concepto", name="uq_regla_contabilizacion"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_tipo: Mapped[str] = mapped_column(String(30))
    concepto: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str] = mapped_column(String(200))
    cuenta_codigo: Mapped[str | None] = mapped_column(String(30))


class DepreciacionMes(Base):
    """Cálculo de la depreciación de un mes (HU-2.07): su partida y el detalle por unidad."""

    __tablename__ = "depreciacion_mes"
    __table_args__ = (
        UniqueConstraint("anio", "mes", name="uq_depreciacion_mes"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_depreciacion_mes_mes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partida.id", name="fk_depreciacion_mes_partida"))
    calculado_por: Mapped[int | None] = mapped_column(Integer)
    calculado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    partida: Mapped[Partida] = relationship(lazy="selectin")
    lineas: Mapped[list["DepreciacionMesLinea"]] = relationship(
        order_by="DepreciacionMesLinea.vin", cascade="all, delete-orphan", lazy="selectin"
    )


class DepreciacionMesLinea(Base):
    """Depreciación financiera (la de la partida) y fiscal de una unidad en el mes; su diferencia
    es la base de la conciliación fiscal del ISR (criterio 3)."""

    __tablename__ = "depreciacion_mes_linea"
    __table_args__ = (UniqueConstraint("depreciacion_id", "vin", name="uq_depreciacion_mes_linea"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    depreciacion_id: Mapped[int] = mapped_column(
        ForeignKey("depreciacion_mes.id", name="fk_depreciacion_mes_linea", ondelete="CASCADE")
    )
    vin: Mapped[str] = mapped_column(String(17), index=True)
    financiera: Mapped[Decimal] = mapped_column(MONTO)
    fiscal: Mapped[Decimal] = mapped_column(MONTO)


class Revaluacion(Base):
    """Revaluación de los saldos en USD al cierre de un mes (HU-2.08), con su partida y, si la
    política es revertir, la reversión del primer día del mes siguiente."""

    __tablename__ = "revaluacion"
    __table_args__ = (
        UniqueConstraint("anio", "mes", name="uq_revaluacion_mes"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_revaluacion_mes"),
        CheckConstraint("politica IN ('revertir', 'mantener')", name="ck_revaluacion_politica"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[date] = mapped_column(Date)  # último día del mes
    tipo_cambio: Mapped[Decimal] = mapped_column(TIPO_CAMBIO)
    politica: Mapped[str] = mapped_column(String(10))
    partida_id: Mapped[int] = mapped_column(ForeignKey("partida.id", name="fk_revaluacion_partida"))
    reversion_id: Mapped[int | None] = mapped_column(
        ForeignKey("partida.id", name="fk_revaluacion_reversion")
    )
    usuario_id: Mapped[int | None] = mapped_column(Integer)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    lineas: Mapped[list["RevaluacionLinea"]] = relationship(
        order_by="RevaluacionLinea.id", cascade="all, delete-orphan", lazy="selectin"
    )


class RevaluacionLinea(Base):
    """Saldo revaluado: una cuenta monetaria en USD con su línea de negocio y VIN. El diferencial
    es positivo si es ganancia y negativo si es pérdida."""

    __tablename__ = "revaluacion_linea"

    id: Mapped[int] = mapped_column(primary_key=True)
    revaluacion_id: Mapped[int] = mapped_column(
        ForeignKey("revaluacion.id", name="fk_revaluacion_linea", ondelete="CASCADE"), index=True
    )
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id", name="fk_revaluacion_linea_cuenta"))
    linea_negocio: Mapped[str | None] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17))
    saldo_usd: Mapped[Decimal] = mapped_column(MONTO)
    tipo_cambio_anterior: Mapped[Decimal] = mapped_column(TIPO_CAMBIO)
    diferencial: Mapped[Decimal] = mapped_column(MONTO)


class PeriodoCerrado(Base):
    """Mes cerrado (HU-2.12): quién y cuándo lo cerró y la instantánea de su balance de
    comprobación. Los meses se cierran en orden, así que todo lo anterior al último también lo está."""

    __tablename__ = "periodo_cerrado"
    __table_args__ = (
        UniqueConstraint("anio", "mes", name="uq_periodo_cerrado"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="ck_periodo_cerrado_mes"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    anio: Mapped[int] = mapped_column(Integer)
    mes: Mapped[int] = mapped_column(Integer)
    fecha: Mapped[date] = mapped_column(Date, unique=True)  # último día del mes
    cerrado_por: Mapped[int | None] = mapped_column(Integer)
    cerrado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    balance: Mapped[dict] = mapped_column(JSONB)
