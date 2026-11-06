"""Tablas del motor contable: partidas de diario y sus líneas (HU-2.01, HU-2.02, HU-2.03).

Solo este módulo crea partidas (regla 3 de la arquitectura). La cuenta de cada línea es una
llave foránea a `cuentas`, sin importar los models de `configuracion`.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
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
        UniqueConstraint("documento_tipo", "documento_id", name="uq_partida_documento"),
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

    lineas: Mapped[list["LineaPartida"]] = relationship(
        back_populates="partida",
        order_by="LineaPartida.numero_linea",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


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
            " OR (moneda = 'USD' AND monto_usd > 0 AND tipo_cambio > 0)",
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
