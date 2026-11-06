"""HU-4.04: gastos de importación por VIN con su cuenta por pagar.

- `concepto_gasto_importacion`: catálogo sembrado aquí (flete, seguro de transporte, agente
  aduanal, almacenaje, DAI, IVA de importación, IPRIMA, placas y otros), cada concepto con su
  cuenta del catálogo semilla de HU-1.02 y su tratamiento. Solo el IVA de importación es crédito
  fiscal (1.1.03.02); los demás suman al costo de la unidad (1.1.04.01, vehículos en tránsito).
- `gasto_importacion`: ligado a la unidad por llave foránea a `unidad.vin`, en GTQ o USD, con el
  tipo de cambio aplicado y el equivalente en quetzales.
- `cuenta_por_pagar` puede nacer de una factura (HU-4.09) o de un gasto de importación, siempre de
  uno solo: `factura_compra_id` pasa a admitir NULL y se agrega `gasto_importacion_id`.
- Bitácora (HU-1.11) en las dos tablas nuevas, como en `0007` y `0008`; el trigger de
  `cuenta_por_pagar` se vuelve a crear para copiar también `gasto_importacion_id`. En
  `gasto_importacion` se copia `vin`, así la bitácora queda filtrable por VIN.

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
TIPO_CAMBIO = sa.Numeric(18, 8)

COSTO, CREDITO = "costo", "credito_fiscal"
EN_TRANSITO, IVA_IMPORTACION = "1.1.04.01", "1.1.03.02"
CONCEPTOS = (
    ("flete", "Flete", EN_TRANSITO, COSTO),
    ("seguro", "Seguro de transporte", EN_TRANSITO, COSTO),
    ("agente_aduanal", "Agente aduanal", EN_TRANSITO, COSTO),
    ("almacenaje", "Almacenaje", EN_TRANSITO, COSTO),
    ("dai", "DAI", EN_TRANSITO, COSTO),
    ("iva_importacion", "IVA de importación", IVA_IMPORTACION, CREDITO),
    ("iprima", "IPRIMA", EN_TRANSITO, COSTO),
    ("placas", "Placas", EN_TRANSITO, COSTO),
    ("otros", "Otros", EN_TRANSITO, COSTO),
)

COLUMNAS = {
    "concepto_gasto_importacion": ("id", "codigo", "nombre", "cuenta", "tratamiento", "orden"),
    "gasto_importacion": (
        "id", "vin", "concepto", "proveedor_id", "fecha", "documento", "descripcion", "moneda",
        "monto", "tipo_cambio", "monto_gtq", "cuenta", "tratamiento", "creado_en",
    ),
}  # fmt: skip
CUENTA_POR_PAGAR = (
    "id", "proveedor_id", "factura_compra_id", "fecha", "fecha_vencimiento", "moneda", "monto",
    "saldo", "creado_en",
)  # fmt: skip


def _trigger(tabla: str, columnas: Sequence[str]) -> None:
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    concepto = op.create_table(
        "concepto_gasto_importacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("cuenta", sa.String(20), nullable=False),
        sa.Column("tratamiento", sa.String(15), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.UniqueConstraint("codigo", name="concepto_gasto_importacion_codigo_key"),
        sa.CheckConstraint(
            "tratamiento IN ('costo', 'credito_fiscal')", name="ck_concepto_gasto_importacion_tratamiento"
        ),
    )

    op.create_table(
        "gasto_importacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_gasto_importacion_vin_unidad"),
            nullable=False,
        ),
        sa.Column(
            "concepto", sa.String(20), sa.ForeignKey("concepto_gasto_importacion.codigo"), nullable=False
        ),
        sa.Column("proveedor_id", sa.Integer(), sa.ForeignKey("proveedor.id"), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("documento", sa.String(50), nullable=False),
        sa.Column("descripcion", sa.String(300), nullable=True),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("tipo_cambio", TIPO_CAMBIO, nullable=True),
        sa.Column("monto_gtq", MONTO, nullable=False),
        sa.Column("cuenta", sa.String(20), nullable=False),
        sa.Column("tratamiento", sa.String(15), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_gasto_importacion_moneda"),
        sa.CheckConstraint("monto > 0 AND monto_gtq > 0", name="ck_gasto_importacion_montos"),
        sa.CheckConstraint(
            "(moneda = 'GTQ' AND tipo_cambio IS NULL AND monto_gtq = monto)"
            " OR (moneda = 'USD' AND tipo_cambio > 0)",
            name="ck_gasto_importacion_tipo_cambio",
        ),
        sa.CheckConstraint(
            "tratamiento IN ('costo', 'credito_fiscal')", name="ck_gasto_importacion_tratamiento"
        ),
    )
    op.create_index("ix_gasto_importacion_vin", "gasto_importacion", ["vin"])
    op.create_index("ix_gasto_importacion_proveedor_id", "gasto_importacion", ["proveedor_id"])
    op.create_index("ix_gasto_importacion_fecha", "gasto_importacion", ["fecha"])

    op.alter_column("cuenta_por_pagar", "factura_compra_id", existing_type=sa.Integer(), nullable=True)
    op.add_column(
        "cuenta_por_pagar",
        sa.Column("gasto_importacion_id", sa.Integer(), sa.ForeignKey("gasto_importacion.id"), nullable=True),
    )
    op.create_unique_constraint(
        "uq_cuenta_por_pagar_gasto_importacion", "cuenta_por_pagar", ["gasto_importacion_id"]
    )
    op.create_check_constraint(
        "ck_cuenta_por_pagar_origen",
        "cuenta_por_pagar",
        "num_nonnulls(factura_compra_id, gasto_importacion_id) = 1",
    )

    for tabla, columnas in COLUMNAS.items():
        _trigger(tabla, columnas)
    op.execute("DROP TRIGGER auditar_cuenta_por_pagar ON cuenta_por_pagar")
    _trigger("cuenta_por_pagar", (*CUENTA_POR_PAGAR, "gasto_importacion_id"))

    # Después de los triggers: la siembra del catálogo queda en la bitácora.
    op.bulk_insert(
        concepto,
        [
            {"codigo": codigo, "nombre": nombre, "cuenta": cuenta, "tratamiento": tratamiento, "orden": orden}
            for orden, (codigo, nombre, cuenta, tratamiento) in enumerate(CONCEPTOS, start=1)
        ],
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cuenta_por_pagar ON cuenta_por_pagar")
    _trigger("cuenta_por_pagar", CUENTA_POR_PAGAR)
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")

    # Las cuentas por pagar de gastos de importación desaparecen con su tabla.
    op.execute("DELETE FROM cuenta_por_pagar WHERE gasto_importacion_id IS NOT NULL")
    op.drop_constraint("ck_cuenta_por_pagar_origen", "cuenta_por_pagar", type_="check")
    op.drop_constraint("uq_cuenta_por_pagar_gasto_importacion", "cuenta_por_pagar", type_="unique")
    op.drop_column("cuenta_por_pagar", "gasto_importacion_id")
    op.alter_column("cuenta_por_pagar", "factura_compra_id", existing_type=sa.Integer(), nullable=False)

    op.drop_table("gasto_importacion")
    op.drop_table("concepto_gasto_importacion")
