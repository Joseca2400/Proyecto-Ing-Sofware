"""HU-4.01: proveedores locales (con NIT único) y del exterior (identificación fiscal y país).

El régimen y las retenciones del proveedor local (criterio 2) se difieren; se agregan en otra
revisión junto con HU-4.11.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "proveedor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("nit", sa.String(13), nullable=True),
        sa.Column("identificacion_fiscal", sa.String(50), nullable=True),
        sa.Column("pais", sa.String(2), nullable=True),
        sa.Column("rubro", sa.String(20), nullable=False),
        sa.Column("moneda_habitual", sa.String(3), nullable=False),
        sa.Column("dias_credito", sa.Integer(), nullable=False),
        sa.Column("banco", sa.String(100), nullable=True),
        sa.Column("cuenta_bancaria", sa.String(50), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("nit"),
        sa.CheckConstraint("tipo IN ('local', 'exterior')", name="ck_proveedor_tipo"),
        sa.CheckConstraint(
            "rubro IN ('subasta', 'dealer', 'naviera', 'agente_aduanal', 'repuestos', 'seguros', "
            "'servicios', 'otros')",
            name="ck_proveedor_rubro",
        ),
        sa.CheckConstraint("moneda_habitual IN ('GTQ', 'USD')", name="ck_proveedor_moneda"),
        sa.CheckConstraint("dias_credito >= 0", name="ck_proveedor_dias_credito"),
        sa.CheckConstraint(
            "(tipo = 'local' AND nit IS NOT NULL AND identificacion_fiscal IS NULL AND pais IS NULL)"
            " OR (tipo = 'exterior' AND nit IS NULL AND identificacion_fiscal IS NOT NULL"
            " AND pais IS NOT NULL)",
            name="ck_proveedor_identificacion",
        ),
    )
    op.create_index("ix_proveedor_nombre", "proveedor", ["nombre"])


def downgrade() -> None:
    op.drop_index("ix_proveedor_nombre", table_name="proveedor")
    op.drop_table("proveedor")
