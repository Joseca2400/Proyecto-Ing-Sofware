"""HU-4.13: programación y aprobación de pagos a proveedores.

- `programacion_pago`: la propuesta, con su fecha prevista y quién la propuso.
- `pago_programado`: cada pago propuesto (cuenta por pagar, cuenta bancaria y monto en la moneda
  del documento), con la decisión del gerente financiero. Una cuenta por pagar no está en dos pagos
  propuestos o aprobados a la vez.
- Bitácora (HU-1.11) en las dos tablas nuevas.

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0032"
down_revision: str | None = "0031"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

COLUMNAS = {
    "programacion_pago": ("id", "fecha", "descripcion", "propuesta_por", "creado_en"),
    "pago_programado": (
        "id", "programacion_id", "cuenta_por_pagar_id", "cuenta_bancaria_id", "monto_propuesto", "monto",
        "estado", "decidido_por", "decidido_en", "comentario", "creado_en",
    ),
}  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "programacion_pago",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=True),
        sa.Column("propuesta_por", sa.Integer(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_programacion_pago_fecha", "programacion_pago", ["fecha"])
    op.create_table(
        "pago_programado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("programacion_id", sa.Integer(), sa.ForeignKey("programacion_pago.id"), nullable=False),
        sa.Column("cuenta_por_pagar_id", sa.Integer(), sa.ForeignKey("cuenta_por_pagar.id"), nullable=False),
        sa.Column("cuenta_bancaria_id", sa.Integer(), sa.ForeignKey("cuenta_bancaria.id"), nullable=False),
        sa.Column("monto_propuesto", MONTO, nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("estado", sa.String(10), nullable=False),
        sa.Column("decidido_por", sa.Integer(), nullable=True),
        sa.Column("decidido_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("comentario", sa.String(300), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "estado IN ('propuesto', 'aprobado', 'rechazado', 'ejecutado')", name="ck_pago_programado_estado"
        ),
        sa.CheckConstraint("monto > 0 AND monto_propuesto > 0", name="ck_pago_programado_monto"),
        sa.CheckConstraint(
            "(estado = 'propuesto' AND decidido_por IS NULL AND decidido_en IS NULL)"
            " OR (estado <> 'propuesto' AND decidido_por IS NOT NULL AND decidido_en IS NOT NULL)",
            name="ck_pago_programado_decision",
        ),
    )
    op.create_index("ix_pago_programado_programacion_id", "pago_programado", ["programacion_id"])
    op.create_index("ix_pago_programado_cuenta_por_pagar_id", "pago_programado", ["cuenta_por_pagar_id"])
    op.create_index(
        "uq_pago_programado_activo",
        "pago_programado",
        ["cuenta_por_pagar_id"],
        unique=True,
        postgresql_where=sa.text("estado IN ('propuesto', 'aprobado')"),
    )

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)


def downgrade() -> None:
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
        op.drop_table(tabla)
