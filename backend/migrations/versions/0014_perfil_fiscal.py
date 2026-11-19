"""HU-1.01: perfil fiscal de la empresa con vigencia por cambio.

- `perfil_fiscal`: una fila por versión; `vigente_desde` es único y un cambio agrega otra fila.
- Bitácora (HU-1.11) en la tabla nueva, como en `0011`.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = (
    "id", "vigente_desde", "razon_social", "nombre_comercial", "nit", "direccion_fiscal",
    "establecimiento", "regimen_isr", "agente_retencion_iva", "agente_retencion_isr", "creado_en",
)  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "perfil_fiscal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("razon_social", sa.String(200), nullable=False),
        sa.Column("nombre_comercial", sa.String(200), nullable=False),
        sa.Column("nit", sa.String(13), nullable=False),
        sa.Column("direccion_fiscal", sa.String(300), nullable=False),
        sa.Column("establecimiento", sa.String(100), nullable=False),
        sa.Column("regimen_isr", sa.String(20), nullable=False),
        sa.Column("agente_retencion_iva", sa.Boolean(), nullable=False),
        sa.Column("agente_retencion_isr", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vigente_desde"),
        sa.CheckConstraint("regimen_isr IN ('utilidades', 'simplificado')", name="ck_perfil_fiscal_regimen"),
    )
    argumentos = ", ".join(f"'{c}'" for c in COLUMNAS)
    op.execute(f"""
        CREATE TRIGGER auditar_perfil_fiscal AFTER INSERT OR UPDATE OR DELETE ON perfil_fiscal
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_perfil_fiscal ON perfil_fiscal")
    op.drop_table("perfil_fiscal")
