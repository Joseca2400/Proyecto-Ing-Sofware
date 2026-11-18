"""Tablas del módulo de taller (Sprint 2, versión delgada)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.comun.db import Base
from app.comun.dinero import MONTO


class TarifaManoObra(Base):
    """Tarifa horaria de costo (HU-5.02). Un cambio es una fila nueva: nunca se edita una vigente."""

    __tablename__ = "tarifa_mano_obra"
    __table_args__ = (CheckConstraint("tarifa_hora > 0", name="ck_tarifa_mano_obra_tarifa"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tarifa_hora: Mapped[Decimal] = mapped_column(MONTO)
    vigente_desde: Mapped[date] = mapped_column(Date, unique=True)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Tipos de trabajo: hoy solo reacondicionamiento (Sprint 2). Los demás (mantenimiento, mejora,
# garantía, postventa facturable) se agregan en los Sprints 5 y 6 ampliando esta lista y su CHECK.
TIPOS_ORDEN = ("reacondicionamiento",)
_TIPOS_SQL = ", ".join(f"'{tipo}'" for tipo in TIPOS_ORDEN)


class OrdenTrabajo(Base):
    """Orden de trabajo ligada a un VIN (HU-5.01). Su número correlativo es su id."""

    __tablename__ = "orden_trabajo"
    __table_args__ = (
        CheckConstraint(f"tipo IN ({_TIPOS_SQL})", name="ck_orden_trabajo_tipo"),
        CheckConstraint("estado IN ('abierta', 'cerrada')", name="ck_orden_trabajo_estado"),
        CheckConstraint("kilometraje >= 0", name="ck_orden_trabajo_kilometraje"),
        CheckConstraint(
            "(estado = 'abierta' AND fecha_cierre IS NULL AND costo_total IS NULL)"
            " OR (estado = 'cerrada' AND fecha_cierre IS NOT NULL AND costo_total IS NOT NULL)",
            name="ck_orden_trabajo_cierre",
        ),
        UniqueConstraint("partida_id", name="uq_orden_trabajo_partida"),
        # Una sola orden abierta por unidad.
        Index(
            "uq_orden_trabajo_abierta_vin", "vin", unique=True, postgresql_where=text("estado = 'abierta'")
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vin: Mapped[str] = mapped_column(
        String(17), ForeignKey("unidad.vin", name="fk_orden_trabajo_vin_unidad"), index=True
    )
    tipo: Mapped[str] = mapped_column(String(30))
    estado: Mapped[str] = mapped_column(String(10), default="abierta")
    fecha_apertura: Mapped[date] = mapped_column(Date)
    kilometraje: Mapped[int]
    descripcion: Mapped[str] = mapped_column(String(500))
    responsable: Mapped[str] = mapped_column(String(100))
    abierta_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Cierre (HU-5.07)
    fecha_cierre: Mapped[date | None] = mapped_column(Date, nullable=True)
    cerrada_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    costo_total: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    justificacion: Mapped[str | None] = mapped_column(String(300), nullable=True)
    partida_id: Mapped[int | None] = mapped_column(
        ForeignKey("partida.id", name="fk_orden_trabajo_partida"), nullable=True
    )

    @property
    def numero(self) -> str:
        return f"OT-{self.id:05d}"

    @property
    def dias(self) -> int:
        """Antigüedad: días desde la apertura hasta el cierre o, si sigue abierta, hasta hoy."""
        return ((self.fecha_cierre or date.today()) - self.fecha_apertura).days

    horas: Mapped[list["HoraTrabajo"]] = relationship(
        back_populates="orden", order_by="HoraTrabajo.id", lazy="selectin"
    )

    @property
    def costo_acumulado(self) -> Decimal:
        """Mano de obra registrada hasta hoy; por ahora es todo el costo de la orden."""
        return sum((hora.costo for hora in self.horas), Decimal(0))


class HoraTrabajo(Base):
    """Mano de obra de una orden (HU-5.03): guarda la tarifa y el costo con que se calculó, así un
    cambio de tarifa posterior no altera lo ya costeado."""

    __tablename__ = "hora_trabajo"
    __table_args__ = (
        CheckConstraint("horas > 0 AND horas <= 24", name="ck_hora_trabajo_horas"),
        CheckConstraint("tarifa_hora > 0 AND costo > 0", name="ck_hora_trabajo_montos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("orden_trabajo.id"), index=True)
    mecanico: Mapped[str] = mapped_column(String(100))
    fecha: Mapped[date] = mapped_column(Date)
    horas: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    tarea: Mapped[str] = mapped_column(String(300))
    tarifa_hora: Mapped[Decimal] = mapped_column(MONTO)
    costo: Mapped[Decimal] = mapped_column(MONTO)
    registrado_por: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orden: Mapped[OrdenTrabajo] = relationship(back_populates="horas")
