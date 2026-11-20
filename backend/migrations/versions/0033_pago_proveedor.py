"""HU-4.14: pago a un proveedor.

- `pago_proveedor`: cuenta bancaria, forma de pago (cheque o transferencia), número de cheque o
  referencia, fecha, monto en la moneda del banco, tipo de cambio y diferencial realizado; se anula,
  no se borra. Un cheque no se repite en la misma cuenta bancaria mientras el pago esté vigente.
- `aplicacion_pago`: lo que el pago cancela de cada cuenta por pagar.
- `pago_programado.pago_id` y el estado `anulado`: el pago que ejecutó el pago programado.
- Bitácora (HU-1.11) en las dos tablas nuevas; `pago_programado` ya la tiene y se le agrega la
  columna nueva.

Revision ID: 0033
Revises: 0032
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0033"
down_revision: str | None = "0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
TIPO_CAMBIO = sa.Numeric(18, 8)

COLUMNAS = {
    "pago_proveedor": (
        "id", "proveedor_id", "cuenta_bancaria_id", "moneda", "forma_pago", "referencia", "fecha", "tipo_cambio",
        "monto", "diferencial", "estado", "usuario_id", "anulado_por", "fecha_anulacion", "motivo_anulacion",
        "creado_en",
    ),
    "aplicacion_pago": (
        "id", "pago_id", "cuenta_por_pagar_id", "pago_programado_id", "moneda_documento", "monto_documento",
        "monto_pago", "tipo_cambio_libros", "diferencial",
    ),
}  # fmt: skip
PAGO_PROGRAMADO = (
    "id", "programacion_id", "cuenta_por_pagar_id", "cuenta_bancaria_id", "monto_propuesto", "monto", "estado",
    "decidido_por", "decidido_en", "comentario", "creado_en",
)  # fmt: skip


def _auditar(tabla: str, columnas: Sequence[str]) -> None:
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.create_table(
        "pago_proveedor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedor.id"), nullable=False),
        sa.Column("cuenta_bancaria_id", sa.Integer(), sa.ForeignKey("cuenta_bancaria.id"), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("forma_pago", sa.String(15), nullable=False),
        sa.Column("referencia", sa.String(50), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("tipo_cambio", TIPO_CAMBIO, nullable=True),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("diferencial", MONTO, nullable=False),
        sa.Column("estado", sa.String(10), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("anulado_por", sa.Integer(), nullable=True),
        sa.Column("fecha_anulacion", sa.Date(), nullable=True),
        sa.Column("motivo_anulacion", sa.String(300), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("forma_pago IN ('cheque', 'transferencia')", name="ck_pago_proveedor_forma"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_pago_proveedor_moneda"),
        sa.CheckConstraint("monto > 0", name="ck_pago_proveedor_monto"),
        sa.CheckConstraint("tipo_cambio IS NULL OR tipo_cambio > 0", name="ck_pago_proveedor_tipo_cambio"),
        sa.CheckConstraint("estado IN ('registrado', 'anulado')", name="ck_pago_proveedor_estado"),
        sa.CheckConstraint(
            "(estado = 'registrado' AND anulado_por IS NULL AND fecha_anulacion IS NULL"
            " AND motivo_anulacion IS NULL)"
            " OR (estado = 'anulado' AND fecha_anulacion IS NOT NULL AND motivo_anulacion IS NOT NULL)",
            name="ck_pago_proveedor_anulacion",
        ),
    )
    op.create_index("ix_pago_proveedor_proveedor_id", "pago_proveedor", ["proveedor_id"])
    op.create_index("ix_pago_proveedor_fecha", "pago_proveedor", ["fecha"])
    op.create_index(
        "uq_pago_proveedor_cheque",
        "pago_proveedor",
        ["cuenta_bancaria_id", "referencia"],
        unique=True,
        postgresql_where=sa.text("forma_pago = 'cheque' AND estado = 'registrado'"),
    )
    op.create_table(
        "aplicacion_pago",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pago_id", sa.Integer(), sa.ForeignKey("pago_proveedor.id"), nullable=False),
        sa.Column("cuenta_por_pagar_id", sa.Integer(), sa.ForeignKey("cuenta_por_pagar.id"), nullable=False),
        sa.Column("pago_programado_id", sa.Integer(), sa.ForeignKey("pago_programado.id"), nullable=False),
        sa.Column("moneda_documento", sa.String(3), nullable=False),
        sa.Column("monto_documento", MONTO, nullable=False),
        sa.Column("monto_pago", MONTO, nullable=False),
        sa.Column("tipo_cambio_libros", TIPO_CAMBIO, nullable=True),
        sa.Column("diferencial", MONTO, nullable=False),
        sa.CheckConstraint("monto_documento > 0 AND monto_pago > 0", name="ck_aplicacion_pago_montos"),
        sa.CheckConstraint("moneda_documento IN ('GTQ', 'USD')", name="ck_aplicacion_pago_moneda"),
    )
    op.create_index("ix_aplicacion_pago_pago_id", "aplicacion_pago", ["pago_id"])
    op.create_index("ix_aplicacion_pago_cuenta_por_pagar_id", "aplicacion_pago", ["cuenta_por_pagar_id"])
    op.create_index("ix_aplicacion_pago_pago_programado_id", "aplicacion_pago", ["pago_programado_id"])

    op.add_column(
        "pago_programado",
        sa.Column("pago_id", sa.Integer(), sa.ForeignKey("pago_proveedor.id"), nullable=True),
    )
    op.create_index("ix_pago_programado_pago_id", "pago_programado", ["pago_id"])
    op.drop_constraint("ck_pago_programado_estado", "pago_programado", type_="check")
    op.create_check_constraint(
        "ck_pago_programado_estado",
        "pago_programado",
        "estado IN ('propuesto', 'aprobado', 'rechazado', 'ejecutado', 'anulado')",
    )
    op.create_check_constraint(
        "ck_pago_programado_pago",
        "pago_programado",
        "(estado IN ('ejecutado', 'anulado')) = (pago_id IS NOT NULL)",
    )
    op.execute("DROP TRIGGER auditar_pago_programado ON pago_programado")
    _auditar("pago_programado", (*PAGO_PROGRAMADO, "pago_id"))

    for tabla, columnas in COLUMNAS.items():
        _auditar(tabla, columnas)


def downgrade() -> None:
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    op.execute("DROP TRIGGER auditar_pago_programado ON pago_programado")
    _auditar("pago_programado", PAGO_PROGRAMADO)
    op.drop_constraint("ck_pago_programado_pago", "pago_programado", type_="check")
    op.drop_constraint("ck_pago_programado_estado", "pago_programado", type_="check")
    op.create_check_constraint(
        "ck_pago_programado_estado",
        "pago_programado",
        "estado IN ('propuesto', 'aprobado', 'rechazado', 'ejecutado')",
    )
    op.drop_index("ix_pago_programado_pago_id", "pago_programado")
    op.drop_column("pago_programado", "pago_id")
    for tabla in reversed(COLUMNAS):
        op.drop_table(tabla)
