"""HU-4.09: facturas de compras y gastos locales (DTE) con su cuenta por pagar.

También agrega el régimen de IVA del proveedor local (HU-4.01, criterio 2), que decide si la
factura da crédito fiscal. Los proveedores locales ya registrados quedan en régimen general.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)


def upgrade() -> None:
    op.add_column("proveedor", sa.Column("regimen", sa.String(25), nullable=True))
    op.execute("UPDATE proveedor SET regimen = 'general' WHERE tipo = 'local'")
    op.create_check_constraint(
        "ck_proveedor_regimen",
        "proveedor",
        "(tipo = 'local' AND regimen IN ('general', 'pequeno_contribuyente'))"
        " OR (tipo = 'exterior' AND regimen IS NULL)",
    )

    op.create_table(
        "factura_compra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedor.id"), nullable=False),
        sa.Column("serie", sa.String(20), nullable=False),
        sa.Column("numero", sa.String(20), nullable=False),
        sa.Column("autorizacion", sa.String(36), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("regimen_proveedor", sa.String(25), nullable=False),
        sa.Column("total_base", MONTO, nullable=False),
        sa.Column("total_iva", MONTO, nullable=False),
        sa.Column("credito_fiscal", MONTO, nullable=False),
        sa.Column("total", MONTO, nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("proveedor_id", "serie", "numero", name="uq_factura_compra_serie_numero"),
        sa.UniqueConstraint("proveedor_id", "autorizacion", name="uq_factura_compra_autorizacion"),
        sa.CheckConstraint(
            "regimen_proveedor IN ('general', 'pequeno_contribuyente')",
            name="ck_factura_compra_regimen",
        ),
        sa.CheckConstraint("total_base > 0 AND total_iva >= 0", name="ck_factura_compra_montos"),
        sa.CheckConstraint("total = total_base + total_iva", name="ck_factura_compra_total"),
        sa.CheckConstraint(
            "(regimen_proveedor = 'general' AND credito_fiscal = total_iva)"
            " OR (regimen_proveedor = 'pequeno_contribuyente' AND credito_fiscal = 0)",
            name="ck_factura_compra_credito_fiscal",
        ),
    )
    op.create_index("ix_factura_compra_proveedor_id", "factura_compra", ["proveedor_id"])
    op.create_index("ix_factura_compra_fecha", "factura_compra", ["fecha"])

    op.create_table(
        "linea_factura_compra",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "factura_id",
            sa.Integer(),
            sa.ForeignKey("factura_compra.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero_linea", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=False),
        sa.Column("cuenta", sa.String(20), nullable=False),
        sa.Column("linea_negocio", sa.String(20), nullable=False),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.Column("base", MONTO, nullable=False),
        sa.Column("iva", MONTO, nullable=False),
        sa.UniqueConstraint("factura_id", "numero_linea", name="uq_linea_factura_compra_numero"),
        sa.CheckConstraint(
            "linea_negocio IN ('alquiler', 'venta', 'taller', 'financiamiento', 'administracion')",
            name="ck_linea_factura_compra_linea_negocio",
        ),
        sa.CheckConstraint("base > 0 AND iva >= 0", name="ck_linea_factura_compra_montos"),
        sa.CheckConstraint("vin IS NULL OR length(vin) = 17", name="ck_linea_factura_compra_vin"),
    )
    op.create_index("ix_linea_factura_compra_vin", "linea_factura_compra", ["vin"])

    op.create_table(
        "cuenta_por_pagar",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedor.id"), nullable=False),
        sa.Column("factura_compra_id", sa.Integer(), sa.ForeignKey("factura_compra.id"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("saldo", MONTO, nullable=False),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("factura_compra_id", name="uq_cuenta_por_pagar_factura"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_cuenta_por_pagar_moneda"),
        sa.CheckConstraint("monto > 0", name="ck_cuenta_por_pagar_monto"),
        sa.CheckConstraint("saldo >= 0 AND saldo <= monto", name="ck_cuenta_por_pagar_saldo"),
        sa.CheckConstraint("fecha_vencimiento >= fecha", name="ck_cuenta_por_pagar_vencimiento"),
    )
    op.create_index("ix_cuenta_por_pagar_proveedor_id", "cuenta_por_pagar", ["proveedor_id"])
    op.create_index("ix_cuenta_por_pagar_fecha_vencimiento", "cuenta_por_pagar", ["fecha_vencimiento"])


def downgrade() -> None:
    op.drop_index("ix_cuenta_por_pagar_fecha_vencimiento", table_name="cuenta_por_pagar")
    op.drop_index("ix_cuenta_por_pagar_proveedor_id", table_name="cuenta_por_pagar")
    op.drop_table("cuenta_por_pagar")
    op.drop_index("ix_linea_factura_compra_vin", table_name="linea_factura_compra")
    op.drop_table("linea_factura_compra")
    op.drop_index("ix_factura_compra_fecha", table_name="factura_compra")
    op.drop_index("ix_factura_compra_proveedor_id", table_name="factura_compra")
    op.drop_table("factura_compra")
    op.drop_constraint("ck_proveedor_regimen", "proveedor", type_="check")
    op.drop_column("proveedor", "regimen")
