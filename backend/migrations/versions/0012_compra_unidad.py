"""HU-4.02: compra de la unidad en EE. UU. con su cuenta por pagar en USD y su partida.

- `compra_unidad`: una por unidad (VIN único, llave foránea a `unidad.vin`), a un proveedor, con
  el precio y los cargos de la subasta en USD, el tipo de cambio de la fecha y el equivalente en
  quetzales; ligada por llave foránea a la partida que crea `contabilidad` (HU-2.03).
- `cuenta_por_pagar` puede nacer también de la compra: se agrega `compra_unidad_id` y el origen
  sigue siendo uno solo de los tres documentos.
- Bitácora (HU-1.11) en la tabla nueva, como en `0011`; el trigger de `cuenta_por_pagar` se vuelve
  a crear para copiar también `compra_unidad_id`. En `compra_unidad` se copia `vin`, así la
  bitácora queda filtrable por VIN.

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
TIPO_CAMBIO = sa.Numeric(18, 8)

COMPRA_UNIDAD = (
    "id", "vin", "proveedor_id", "fecha", "documento", "precio_usd", "comision_usd",
    "documentacion_usd", "arrastre_usd", "total_usd", "tipo_cambio", "total_gtq", "partida_id",
    "creado_en",
)  # fmt: skip
CUENTA_POR_PAGAR = (
    "id", "proveedor_id", "factura_compra_id", "gasto_importacion_id", "fecha", "fecha_vencimiento",
    "moneda", "monto", "saldo", "creado_en",
)  # fmt: skip


def _trigger(tabla: str, columnas: Sequence[str]) -> None:
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.create_table(
        "compra_unidad",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_compra_unidad_vin_unidad"),
            nullable=False,
        ),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedor.id"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("documento", sa.String(50), nullable=False),
        sa.Column("precio_usd", MONTO, nullable=False),
        sa.Column("comision_usd", MONTO, nullable=False),
        sa.Column("documentacion_usd", MONTO, nullable=False),
        sa.Column("arrastre_usd", MONTO, nullable=False),
        sa.Column("total_usd", MONTO, nullable=False),
        sa.Column("tipo_cambio", TIPO_CAMBIO, nullable=False),
        sa.Column("total_gtq", MONTO, nullable=False),
        sa.Column(
            "partida_id",
            sa.Integer(),
            sa.ForeignKey("partida.id", name="fk_compra_unidad_partida"),
            nullable=False,
        ),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vin", name="uq_compra_unidad_vin"),
        sa.UniqueConstraint("partida_id", name="uq_compra_unidad_partida"),
        sa.CheckConstraint(
            "precio_usd > 0 AND comision_usd >= 0 AND documentacion_usd >= 0 AND arrastre_usd >= 0",
            name="ck_compra_unidad_montos",
        ),
        sa.CheckConstraint(
            "total_usd = precio_usd + comision_usd + documentacion_usd + arrastre_usd",
            name="ck_compra_unidad_total",
        ),
        sa.CheckConstraint("tipo_cambio > 0 AND total_gtq > 0", name="ck_compra_unidad_tipo_cambio"),
    )
    op.create_index("ix_compra_unidad_proveedor_id", "compra_unidad", ["proveedor_id"])
    op.create_index("ix_compra_unidad_fecha", "compra_unidad", ["fecha"])

    op.add_column(
        "cuenta_por_pagar",
        sa.Column("compra_unidad_id", sa.Integer(), sa.ForeignKey("compra_unidad.id"), nullable=True),
    )
    op.create_unique_constraint("uq_cuenta_por_pagar_compra_unidad", "cuenta_por_pagar", ["compra_unidad_id"])
    op.drop_constraint("ck_cuenta_por_pagar_origen", "cuenta_por_pagar", type_="check")
    op.create_check_constraint(
        "ck_cuenta_por_pagar_origen",
        "cuenta_por_pagar",
        "num_nonnulls(factura_compra_id, gasto_importacion_id, compra_unidad_id) = 1",
    )

    _trigger("compra_unidad", COMPRA_UNIDAD)
    op.execute("DROP TRIGGER auditar_cuenta_por_pagar ON cuenta_por_pagar")
    _trigger("cuenta_por_pagar", (*CUENTA_POR_PAGAR, "compra_unidad_id"))


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cuenta_por_pagar ON cuenta_por_pagar")
    _trigger("cuenta_por_pagar", CUENTA_POR_PAGAR)
    op.execute("DROP TRIGGER auditar_compra_unidad ON compra_unidad")

    # Las cuentas por pagar de compras desaparecen con su tabla.
    op.execute("DELETE FROM cuenta_por_pagar WHERE compra_unidad_id IS NOT NULL")
    op.drop_constraint("ck_cuenta_por_pagar_origen", "cuenta_por_pagar", type_="check")
    op.create_check_constraint(
        "ck_cuenta_por_pagar_origen",
        "cuenta_por_pagar",
        "num_nonnulls(factura_compra_id, gasto_importacion_id) = 1",
    )
    op.drop_constraint("uq_cuenta_por_pagar_compra_unidad", "cuenta_por_pagar", type_="unique")
    op.drop_column("cuenta_por_pagar", "compra_unidad_id")

    op.drop_table("compra_unidad")
