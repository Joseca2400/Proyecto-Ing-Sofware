"""HU-2.08: revaluación de los saldos en dólares al cierre del mes.

- `revaluacion`: una por mes, con el tipo de cambio de cierre, la política (revertir el primer día
  del mes siguiente o mantener el saldo revaluado), su partida y su reversión.
- `revaluacion_linea`: el reporte por cuenta (y línea de negocio y VIN): saldo en USD, tipo de
  cambio anterior y diferencial.
- Reglas de contabilización de `revaluacion`: ganancia 4.4 y pérdida 6.3 (las del diferencial
  realizado; el contador puede separarlas desde la pantalla).
- Bitácora (HU-1.11) en las dos tablas.

Revision ID: 0029
Revises: 0028
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
TIPO_CAMBIO = sa.Numeric(18, 8)
COLUMNAS = {
    "revaluacion": (
        "id", "anio", "mes", "fecha", "tipo_cambio", "politica", "partida_id", "reversion_id", "usuario_id",
        "creado_en",
    ),
    "revaluacion_linea": (
        "id", "revaluacion_id", "cuenta_id", "linea_negocio", "vin", "saldo_usd", "tipo_cambio_anterior",
        "diferencial",
    ),
}  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "revaluacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("anio", sa.Integer(), nullable=False),
        sa.Column("mes", sa.Integer(), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("tipo_cambio", TIPO_CAMBIO, nullable=False),
        sa.Column("politica", sa.String(10), nullable=False),
        sa.Column(
            "partida_id", sa.Integer(), sa.ForeignKey("partida.id", name="fk_revaluacion_partida"), nullable=False
        ),
        sa.Column(
            "reversion_id", sa.Integer(), sa.ForeignKey("partida.id", name="fk_revaluacion_reversion"), nullable=True
        ),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("anio", "mes", name="uq_revaluacion_mes"),
        sa.CheckConstraint("mes BETWEEN 1 AND 12", name="ck_revaluacion_mes"),
        sa.CheckConstraint("politica IN ('revertir', 'mantener')", name="ck_revaluacion_politica"),
    )  # fmt: skip
    op.create_table(
        "revaluacion_linea",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "revaluacion_id",
            sa.Integer(),
            sa.ForeignKey("revaluacion.id", name="fk_revaluacion_linea", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id", name="fk_revaluacion_linea_cuenta"), nullable=False
        ),
        sa.Column("linea_negocio", sa.String(20), nullable=True),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.Column("saldo_usd", MONTO, nullable=False),
        sa.Column("tipo_cambio_anterior", TIPO_CAMBIO, nullable=False),
        sa.Column("diferencial", MONTO, nullable=False),
    )  # fmt: skip
    op.create_index("ix_revaluacion_linea_revaluacion_id", "revaluacion_linea", ["revaluacion_id"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.execute("""
        INSERT INTO regla_contabilizacion (documento_tipo, concepto, descripcion, cuenta_codigo) VALUES
        ('revaluacion', 'ganancia', 'Ganancia cambiaria no realizada al revaluar saldos en USD', '4.4'),
        ('revaluacion', 'perdida', 'Pérdida cambiaria no realizada al revaluar saldos en USD', '6.3')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'revaluacion'")
    op.drop_table("revaluacion_linea")
    op.drop_table("revaluacion")
