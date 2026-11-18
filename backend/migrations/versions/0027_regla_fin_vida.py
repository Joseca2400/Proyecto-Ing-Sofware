"""HU-3.14: regla de fin de vida útil en flota (una sola fila, auditada).

Sin regla sembrada: qué define el fin de vida está pendiente (pregunta 5 de las épicas); la define
el gerente financiero o el contador desde la pantalla.

Revision ID: 0027
Revises: 0026
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: str | None = "0026"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = (
    "id",
    "kilometraje_limite",
    "meses_limite",
    "porcentaje_aviso",
    "actualizado_por",
    "actualizado_en",
)


def upgrade() -> None:
    op.create_table(
        "regla_fin_vida",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kilometraje_limite", sa.Integer(), nullable=True),
        sa.Column("meses_limite", sa.Integer(), nullable=True),
        sa.Column("porcentaje_aviso", sa.Numeric(5, 2), nullable=False),
        sa.Column("actualizado_por", sa.Integer(), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_regla_fin_vida_unica"),
        sa.CheckConstraint(
            "num_nonnulls(kilometraje_limite, meses_limite) >= 1"
            " AND (kilometraje_limite IS NULL OR kilometraje_limite > 0)"
            " AND (meses_limite IS NULL OR meses_limite > 0)"
            " AND porcentaje_aviso > 0 AND porcentaje_aviso <= 100",
            name="ck_regla_fin_vida_valores",
        ),
    )
    argumentos = ", ".join(f"'{columna}'" for columna in COLUMNAS)
    op.execute(f"""
        CREATE TRIGGER auditar_regla_fin_vida AFTER INSERT OR UPDATE OR DELETE ON regla_fin_vida
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.drop_table("regla_fin_vida")
