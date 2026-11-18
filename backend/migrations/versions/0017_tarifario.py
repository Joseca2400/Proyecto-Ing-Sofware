"""HU-3.05: tarifario de alquiler por tipo de vehículo o por unidad (módulo de alquileres).

- `tarifa`: modalidad, moneda, monto, kilometraje incluido, precio por kilómetro adicional y
  vigencia; aplica a un tipo de vehículo o, como excepción, a un VIN (uno solo de los dos).
- Bitácora (HU-1.11) en la tabla nueva, con el VIN copiado para filtrarla por unidad.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

TARIFA = (
    "id", "tipo_vehiculo", "vin", "modalidad", "moneda", "monto", "km_incluido",
    "precio_km_adicional", "vigente_desde", "vigente_hasta", "creado_en",
)  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "tarifa",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo_vehiculo", sa.String(20), nullable=True),
        sa.Column(
            "vin", sa.String(17), sa.ForeignKey("unidad.vin", name="fk_tarifa_vin_unidad"), nullable=True
        ),
        sa.Column("modalidad", sa.String(20), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", MONTO, nullable=False),
        sa.Column("km_incluido", sa.Integer(), nullable=False),
        sa.Column("precio_km_adicional", MONTO, nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vigente_hasta", sa.Date(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')", name="ck_tarifa_modalidad"
        ),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_tarifa_moneda"),
        sa.CheckConstraint(
            "(tipo_vehiculo IS NOT NULL AND vin IS NULL) OR (tipo_vehiculo IS NULL AND vin IS NOT NULL)",
            name="ck_tarifa_aplica_a",
        ),
        sa.CheckConstraint(
            "monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0", name="ck_tarifa_montos"
        ),
        sa.CheckConstraint(
            "vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="ck_tarifa_vigencia"
        ),
    )
    op.create_index("ix_tarifa_tipo_vehiculo", "tarifa", ["tipo_vehiculo"])
    op.create_index("ix_tarifa_vin", "tarifa", ["vin"])
    argumentos = ", ".join(f"'{columna}'" for columna in TARIFA)
    op.execute(f"""
        CREATE TRIGGER auditar_tarifa AFTER INSERT OR UPDATE OR DELETE ON tarifa
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_tarifa ON tarifa")
    op.drop_index("ix_tarifa_vin", table_name="tarifa")
    op.drop_index("ix_tarifa_tipo_vehiculo", table_name="tarifa")
    op.drop_table("tarifa")
