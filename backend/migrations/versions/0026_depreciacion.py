"""HU-3.02: parámetros de depreciación por unidad (versionados) y valores por defecto por tipo.

- `depreciacion_tipo_vehiculo`: vida útil, residual (% del costo) y porcentaje fiscal anual que se
  proponen al dar de alta la unidad; sembrados para cada tipo con 60 meses, 10 % y 20 % (BORRADOR
  que valida el contador).
- `parametro_depreciacion`: versiones con su vigencia; un cambio es una fila nueva (prospectivo).
- Bitácora (HU-1.11) en las dos tablas; en `parametro_depreciacion` se copia el VIN.

Revision ID: 0026
Revises: 0025
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: str | None = "0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)
PORCENTAJE = sa.Numeric(5, 2)

TIPOS = ("sedan", "hatchback", "suv", "pickup", "camioneta", "microbus", "motocicleta", "otro")
COLUMNAS = {
    "depreciacion_tipo_vehiculo": (
        "id", "tipo_vehiculo", "vida_util_meses", "porcentaje_residual", "porcentaje_fiscal", "actualizado_por",
    ),
    "parametro_depreciacion": (
        "id", "vin", "vigente_desde", "vida_util_meses", "valor_residual", "porcentaje_fiscal", "usuario_id",
        "creado_en",
    ),
}  # fmt: skip


def upgrade() -> None:
    tipos = op.create_table(
        "depreciacion_tipo_vehiculo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo_vehiculo", sa.String(20), nullable=False),
        sa.Column("vida_util_meses", sa.Integer(), nullable=False),
        sa.Column("porcentaje_residual", PORCENTAJE, nullable=False),
        sa.Column("porcentaje_fiscal", PORCENTAJE, nullable=False),
        sa.Column("actualizado_por", sa.Integer(), nullable=True),
        sa.UniqueConstraint("tipo_vehiculo", name="uq_depreciacion_tipo_vehiculo"),
        sa.CheckConstraint(
            "vida_util_meses > 0 AND porcentaje_residual >= 0 AND porcentaje_residual < 100"
            " AND porcentaje_fiscal > 0 AND porcentaje_fiscal <= 100",
            name="ck_depreciacion_tipo_vehiculo_valores",
        ),
    )
    op.create_table(
        "parametro_depreciacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_parametro_depreciacion_vin_unidad"),
            nullable=False,
        ),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("vida_util_meses", sa.Integer(), nullable=False),
        sa.Column("valor_residual", MONTO, nullable=False),
        sa.Column("porcentaje_fiscal", PORCENTAJE, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vin", "vigente_desde", name="uq_parametro_depreciacion_vigencia"),
        sa.CheckConstraint(
            "vida_util_meses > 0 AND valor_residual >= 0 AND porcentaje_fiscal > 0 AND porcentaje_fiscal <= 100",
            name="ck_parametro_depreciacion_valores",
        ),
    )
    op.create_index("ix_parametro_depreciacion_vin", "parametro_depreciacion", ["vin"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.bulk_insert(
        tipos,
        [
            {"tipo_vehiculo": tipo, "vida_util_meses": 60, "porcentaje_residual": 10, "porcentaje_fiscal": 20}
            for tipo in TIPOS
        ],
    )


def downgrade() -> None:
    op.drop_table("parametro_depreciacion")
    op.drop_table("depreciacion_tipo_vehiculo")
