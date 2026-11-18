"""Taller (versión delgada): tarifas de mano de obra, órdenes de trabajo y horas.

- `tarifa_mano_obra` (HU-5.02): tarifa horaria de costo con vigencia; un cambio es una fila nueva.
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


def downgrade() -> None:
    op.drop_table("tarifa_mano_obra")
