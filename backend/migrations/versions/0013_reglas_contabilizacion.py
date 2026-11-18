"""HU-2.03: reglas de contabilización por tipo de documento, con las de compras sembradas.

Cada módulo siembra en su migración las reglas de sus documentos (tipo, concepto, descripción y
código de cuenta del catálogo semilla); el contador las ajusta después desde la pantalla.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REGLAS = (
    ("compra_unidad", "unidad_en_transito", "Costo de la unidad comprada (unidades en proceso)", "1.1.04.01"),
    ("compra_unidad", "por_pagar_usd", "Deuda con el proveedor del exterior, en dólares", "2.1.01.01"),
    ("gasto_importacion", "por_pagar_usd", "Deuda del gasto de importación en dólares", "2.1.01.01"),
    ("gasto_importacion", "por_pagar_gtq", "Deuda del gasto de importación en quetzales", "2.1.01.02"),
    ("factura_compra", "iva_credito_fiscal", "IVA crédito fiscal de la factura de un proveedor local", "1.1.03.01"),
    ("factura_compra", "por_pagar_gtq", "Deuda con el proveedor local", "2.1.01.02"),
)  # fmt: skip


def upgrade() -> None:
    reglas = op.create_table(
        "regla_contabilizacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("documento_tipo", sa.String(30), nullable=False),
        sa.Column("concepto", sa.String(40), nullable=False),
        sa.Column("descripcion", sa.String(200), nullable=False),
        sa.Column("cuenta_codigo", sa.String(30), nullable=True),
        sa.UniqueConstraint("documento_tipo", "concepto", name="uq_regla_contabilizacion"),
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
    op.execute("""
        CREATE TRIGGER auditar_regla_contabilizacion AFTER INSERT OR UPDATE OR DELETE ON regla_contabilizacion
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio(
            'id', 'documento_tipo', 'concepto', 'descripcion', 'cuenta_codigo')
    """)


def downgrade() -> None:
    op.drop_table("regla_contabilizacion")
