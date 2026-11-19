"""HU-2.12: cierre de un período mensual.

`periodo_cerrado` guarda un mes cerrado con su usuario, fecha e instantánea del balance de
comprobación. El motor contable rechaza partidas, reversiones y documentos con fecha en un mes
cerrado. Bitácora (HU-1.11) sin la instantánea, que ya queda en la propia tabla.

Revision ID: 0030
Revises: 0029
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0030"
down_revision: str | None = "0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "periodo_cerrado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("cerrado_por", sa.Integer(), nullable=True),
        sa.Column("cerrado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("balance", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("anio", "mes", name="uq_periodo_cerrado"),
        sa.UniqueConstraint("fecha", name="periodo_cerrado_fecha_key"),
        sa.CheckConstraint("mes BETWEEN 1 AND 12", name="ck_periodo_cerrado_mes"),
    )
    op.execute("""
        CREATE TRIGGER auditar_periodo_cerrado AFTER INSERT OR UPDATE OR DELETE ON periodo_cerrado
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio(
            'id', 'anio', 'mes', 'fecha', 'cerrado_por', 'cerrado_en')
    """)


def downgrade() -> None:
    op.drop_table("periodo_cerrado")
