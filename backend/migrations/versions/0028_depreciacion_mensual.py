"""HU-2.07: depreciación mensual de la flota.

- `depreciacion_mes`: una por mes, con la partida que genera (en borrador hasta que se contabiliza).
- `depreciacion_mes_linea`: por unidad, la depreciación financiera (la de la partida) y la fiscal.
- Reglas de contabilización de `depreciacion`: gasto 6.4 y depreciación acumulada 1.2.02.
- Bitácora (HU-1.11) en las dos tablas.

Revision ID: 0028
Revises: 0027
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0028"
down_revision: str | None = "0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
COLUMNAS = {
    "depreciacion_mes": ("id", "anio", "mes", "partida_id", "calculado_por", "calculado_en"),
    "depreciacion_mes_linea": ("id", "depreciacion_id", "vin", "financiera", "fiscal"),
}


def upgrade() -> None:
    op.create_table(
        "depreciacion_mes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column(
            "partida_id",
            sa.Integer(),
            sa.ForeignKey("partida.id", name="fk_depreciacion_mes_partida"),
            nullable=False,
        ),
        sa.Column("calculado_por", sa.Integer(), nullable=True),
        sa.Column(
            "calculado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.UniqueConstraint("anio", "mes", name="uq_depreciacion_mes"),
        sa.CheckConstraint("mes BETWEEN 1 AND 12", name="ck_depreciacion_mes_mes"),
    )
    op.create_table(
        "depreciacion_mes_linea",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "depreciacion_id",
            sa.Integer(),
            sa.ForeignKey("depreciacion_mes.id", name="fk_depreciacion_mes_linea", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vin", sa.String(17), nullable=False),
        sa.Column("financiera", MONTO, nullable=False),
        sa.Column("fiscal", MONTO, nullable=False),
        sa.UniqueConstraint("depreciacion_id", "vin", name="uq_depreciacion_mes_linea"),
    )
    op.create_index("ix_depreciacion_mes_linea_vin", "depreciacion_mes_linea", ["vin"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.execute("""
        INSERT INTO regla_contabilizacion (documento_tipo, concepto, descripcion, cuenta_codigo) VALUES
        ('depreciacion', 'gasto', 'Gasto por depreciación de la flota, por unidad', '6.4'),
        ('depreciacion', 'acumulada', 'Depreciación acumulada de la flota, por unidad', '1.2.02')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'depreciacion'")
    op.drop_table("depreciacion_mes_linea")
    op.drop_table("depreciacion_mes")
