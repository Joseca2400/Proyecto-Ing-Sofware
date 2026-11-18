"""Taller (versión delgada): tarifas de mano de obra, órdenes de trabajo y horas.

- `tarifa_mano_obra` (HU-5.02): tarifa horaria de costo con vigencia; un cambio es una fila nueva.
- `orden_trabajo` (HU-5.01 y HU-5.07): una orden abierta por VIN (índice parcial único), con las
  columnas del cierre y la llave a la partida que crea `contabilidad`; el tipo de trabajo es un
  texto con CHECK, para agregar tipos en los Sprints 5 y 6 sin rediseñar.
- `hora_trabajo` (HU-5.03): horas por orden con la tarifa y el costo con que se calcularon.
- Bitácora (HU-1.11) en cada tabla nueva, como en `0011`.

Revision ID: 0020
Revises: 0013
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

TARIFA = ("id", "tarifa_hora", "vigente_desde", "creado_por", "creado_en")
ORDEN = (
    "id", "vin", "tipo", "estado", "fecha_apertura", "kilometraje", "descripcion", "responsable",
    "abierta_por", "creado_en", "fecha_cierre", "cerrada_por", "costo_total", "justificacion",
    "partida_id",
)  # fmt: skip
HORA = (
    "id", "orden_id", "mecanico", "fecha", "horas", "tarea", "tarifa_hora", "costo", "registrado_por",
    "creado_en",
)  # fmt: skip


def _trigger(tabla: str, columnas: Sequence[str]) -> None:
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.create_table(
        "tarifa_mano_obra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tarifa_hora", MONTO, nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("creado_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vigente_desde", name="uq_tarifa_mano_obra_vigente_desde"),
        sa.CheckConstraint("tarifa_hora > 0", name="ck_tarifa_mano_obra_tarifa"),
    )
    _trigger("tarifa_mano_obra", TARIFA)

    op.create_table(
        "orden_trabajo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_orden_trabajo_vin_unidad"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(10), nullable=False),
        sa.Column("fecha_apertura", sa.Date(), nullable=False),
        sa.Column("kilometraje", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(500), nullable=False),
        sa.Column("responsable", sa.String(100), nullable=False),
        sa.Column("abierta_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("fecha_cierre", sa.Date(), nullable=True),
        sa.Column("cerrada_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("costo_total", MONTO, nullable=True),
        sa.Column("justificacion", sa.String(300), nullable=True),
        sa.Column(
            "partida_id",
            sa.Integer(),
            sa.ForeignKey("partida.id", name="fk_orden_trabajo_partida"),
            nullable=True,
        ),
        sa.UniqueConstraint("partida_id", name="uq_orden_trabajo_partida"),
        sa.CheckConstraint("tipo IN ('reacondicionamiento')", name="ck_orden_trabajo_tipo"),
        sa.CheckConstraint("estado IN ('abierta', 'cerrada')", name="ck_orden_trabajo_estado"),
        sa.CheckConstraint("kilometraje >= 0", name="ck_orden_trabajo_kilometraje"),
        sa.CheckConstraint(
            "(estado = 'abierta' AND fecha_cierre IS NULL AND costo_total IS NULL)"
            " OR (estado = 'cerrada' AND fecha_cierre IS NOT NULL AND costo_total IS NOT NULL)",
            name="ck_orden_trabajo_cierre",
        ),
    )
    op.create_index("ix_orden_trabajo_vin", "orden_trabajo", ["vin"])
    op.create_index(
        "uq_orden_trabajo_abierta_vin",
        "orden_trabajo",
        ["vin"],
        unique=True,
        postgresql_where=sa.text("estado = 'abierta'"),
    )
    _trigger("orden_trabajo", ORDEN)

    op.create_table(
        "hora_trabajo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("orden_id", sa.Integer(), sa.ForeignKey("orden_trabajo.id"), nullable=False),
        sa.Column("mecanico", sa.String(100), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("horas", sa.Numeric(5, 2), nullable=False),
        sa.Column("tarea", sa.String(300), nullable=False),
        sa.Column("tarifa_hora", MONTO, nullable=False),
        sa.Column("costo", MONTO, nullable=False),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuarios.id"), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("horas > 0 AND horas <= 24", name="ck_hora_trabajo_horas"),
        sa.CheckConstraint("tarifa_hora > 0 AND costo > 0", name="ck_hora_trabajo_montos"),
    )
    op.create_index("ix_hora_trabajo_orden_id", "hora_trabajo", ["orden_id"])
    _trigger("hora_trabajo", HORA)


def downgrade() -> None:
    op.drop_table("hora_trabajo")
    op.drop_table("orden_trabajo")
    op.drop_table("tarifa_mano_obra")
