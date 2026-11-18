"""HU-3.07: depósitos en garantía de los contratos de alquiler.

- `deposito_garantia`: ligado al contrato (y al VIN), en la moneda recibida, con su cuenta
  bancaria y su saldo; o una autorización de tarjeta sin cobro, solo como referencia.
- `movimiento_deposito`: aplicación a los cargos del contrato o devolución al cliente.
- Reglas de contabilización del pasivo por moneda y de la cuenta por cobrar a la que se aplica.
- Bitácora (HU-1.11) en las dos tablas nuevas; en `deposito_garantia` se copia el VIN.

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

REGLAS = (
    ("deposito_garantia", "pasivo_gtq", "Depósitos en garantía recibidos en quetzales (pasivo)", "2.1.03"),
    ("deposito_garantia", "pasivo_usd", "Depósitos en garantía recibidos en dólares (pasivo)", "2.1.04"),
    ("aplicacion_deposito", "por_cobrar_gtq", "Cuenta por cobrar al cliente a la que se aplica el depósito en quetzales", "1.1.02.01"),
    ("aplicacion_deposito", "por_cobrar_usd", "Cuenta por cobrar al cliente a la que se aplica el depósito en dólares", "1.1.02.02"),
)  # fmt: skip

COLUMNAS = {
    "deposito_garantia": (
        "id", "contrato_id", "vin", "tipo", "fecha", "moneda", "monto", "saldo", "cuenta_bancaria_id",
        "referencia", "usuario_id", "creado_en",
    ),
    "movimiento_deposito": (
        "id", "deposito_id", "tipo", "fecha", "monto", "cuenta_bancaria_id", "usuario_id", "creado_en",
    ),
}  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "deposito_garantia",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("contrato_id", sa.Integer(), sa.ForeignKey("contrato_alquiler.id"), nullable=False),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_deposito_garantia_vin_unidad"),
            nullable=False,
        ),
        sa.Column("tipo", sa.String(25), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("saldo", MONTO, nullable=False),
        sa.Column("cuenta_bancaria_id", sa.Integer(), sa.ForeignKey("cuenta_bancaria.id"), nullable=True),
        sa.Column("referencia", sa.String(100), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("tipo IN ('deposito', 'autorizacion_tarjeta')", name="ck_deposito_garantia_tipo"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_deposito_garantia_moneda"),
        sa.CheckConstraint("monto > 0 AND saldo >= 0 AND saldo <= monto", name="ck_deposito_garantia_saldo"),
        sa.CheckConstraint(
            "(tipo = 'deposito' AND cuenta_bancaria_id IS NOT NULL)"
            " OR (tipo = 'autorizacion_tarjeta' AND cuenta_bancaria_id IS NULL AND referencia IS NOT NULL"
            " AND saldo = 0)",
            name="ck_deposito_garantia_forma",
        ),
    )
    op.create_index("ix_deposito_garantia_contrato_id", "deposito_garantia", ["contrato_id"])
    op.create_table(
        "movimiento_deposito",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("deposito_id", sa.Integer(), sa.ForeignKey("deposito_garantia.id"), nullable=False),
        sa.Column("tipo", sa.String(15), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("cuenta_bancaria_id", sa.Integer(), sa.ForeignKey("cuenta_bancaria.id"), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("tipo IN ('aplicacion', 'devolucion')", name="ck_movimiento_deposito_tipo"),
        sa.CheckConstraint("monto > 0", name="ck_movimiento_deposito_monto"),
        sa.CheckConstraint(
            "tipo = 'aplicacion' OR cuenta_bancaria_id IS NOT NULL", name="ck_movimiento_deposito_banco"
        ),
    )
    op.create_index("ix_movimiento_deposito_deposito_id", "movimiento_deposito", ["deposito_id"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    reglas = sa.table(
        "regla_contabilizacion",
        sa.column("documento_tipo", sa.String),
        sa.column("concepto", sa.String),
        sa.column("descripcion", sa.String),
        sa.column("cuenta_codigo", sa.String),
    )
    op.bulk_insert(
        reglas,
        [
            {
                "documento_tipo": tipo,
                "concepto": concepto,
                "descripcion": descripcion,
                "cuenta_codigo": cuenta,
            }
            for tipo, concepto, descripcion, cuenta in REGLAS
        ],
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM regla_contabilizacion WHERE documento_tipo IN ('deposito_garantia', 'aplicacion_deposito')"
    )
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
        op.drop_table(tabla)
