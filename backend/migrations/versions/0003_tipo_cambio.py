"""HU-1.06: tipo de cambio de referencia por fecha.

Cuelga de la bitácora del equipo A (d5f18a6e0c47, HU-1.11) para que quede una sola cadena:
0001 → 0002 → c0a7e41d9b32 → d5f18a6e0c47 → 0003 → 0004 → 0005 → 0006.

Revision ID: 0003
Revises: d5f18a6e0c47
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "d5f18a6e0c47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tipo_cambio",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("valor", sa.Numeric(18, 8), nullable=False),
        sa.Column("origen", sa.String(length=10), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("valor > 0", name="ck_tipo_cambio_valor_positivo"),
        sa.CheckConstraint("origen IN ('manual', 'automatico')", name="ck_tipo_cambio_origen"),
    )
    op.create_index("ix_tipo_cambio_fecha", "tipo_cambio", ["fecha"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_tipo_cambio_fecha", table_name="tipo_cambio")
    op.drop_table("tipo_cambio")
