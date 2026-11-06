"""HU-1.07: tabla de transacciones en USD con monto original, tipo de cambio y equivalente.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transaccion_usd",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("monto_usd", sa.Numeric(18, 6), nullable=False),
        sa.Column("tipo_cambio_aplicado", sa.Numeric(18, 8), nullable=False),
        sa.Column("monto_gtq", sa.Numeric(18, 6), nullable=False),
        sa.Column("justificacion", sa.Text(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("monto_usd > 0", name="ck_transaccion_usd_monto_positivo"),
        sa.CheckConstraint("tipo_cambio_aplicado > 0", name="ck_transaccion_usd_tipo_positivo"),
        sa.CheckConstraint("monto_gtq > 0", name="ck_transaccion_usd_gtq_positivo"),
    )
    op.create_index("ix_transaccion_usd_fecha", "transaccion_usd", ["fecha"])


def downgrade() -> None:
    op.drop_index("ix_transaccion_usd_fecha", table_name="transaccion_usd")
    op.drop_table("transaccion_usd")
