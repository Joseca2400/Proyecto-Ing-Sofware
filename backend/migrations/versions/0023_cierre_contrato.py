"""HU-3.08: cierre del contrato de alquiler y kilometraje de la unidad.

- `contrato_alquiler`: devolución (fecha y hora, kilometraje, combustible en octavos, daños) y el
  cálculo del cierre (días efectivos, km recorridos y excedentes, combustible faltante, monto
  final). Un contrato cerrado los tiene todos.
- `unidad.kilometraje` (módulo `unidades`): lo actualiza la devolución.
- Los triggers de bitácora (HU-1.11) de las dos tablas se vuelven a crear con las columnas nuevas.

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: str | None = "0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

UNIDAD = (
    "id", "vin", "marca", "linea", "modelo", "color", "tipo_vehiculo", "linea_negocio", "estado",
    "creado_en",
)  # fmt: skip
CONTRATO = (
    "id", "numero", "cliente_id", "vin", "salida", "devolucion_prevista", "tarifa_id", "modalidad",
    "moneda", "tarifa_monto", "km_incluido", "precio_km_adicional", "km_salida", "combustible_salida",
    "deposito_esperado", "dias_previstos", "monto_estimado", "estado", "usuario_id", "creado_en",
)  # fmt: skip
CIERRE = (
    "devolucion", "km_devolucion", "combustible_devolucion", "observaciones_danos", "dias_efectivos",
    "km_recorridos", "km_excedentes", "combustible_faltante", "monto_final", "cerrado_por",
)  # fmt: skip


def _trigger(tabla: str, columnas: Sequence[str]) -> None:
    op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.add_column("unidad", sa.Column("kilometraje", sa.Integer(), nullable=True))
    op.create_check_constraint("ck_unidad_kilometraje", "unidad", "kilometraje IS NULL OR kilometraje >= 0")

    op.add_column("contrato_alquiler", sa.Column("devolucion", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("km_devolucion", sa.Integer(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("combustible_devolucion", sa.SmallInteger(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("observaciones_danos", sa.String(1000), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("dias_efectivos", sa.Integer(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("km_recorridos", sa.Integer(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("km_excedentes", sa.Integer(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("combustible_faltante", sa.SmallInteger(), nullable=True))
    op.add_column("contrato_alquiler", sa.Column("monto_final", MONTO, nullable=True))
    op.add_column("contrato_alquiler", sa.Column("cerrado_por", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_contrato_alquiler_cierre",
        "contrato_alquiler",
        "estado = 'abierto' OR (devolucion IS NOT NULL AND km_devolucion >= km_salida"
        " AND combustible_devolucion BETWEEN 0 AND 8 AND dias_efectivos >= 1 AND km_recorridos >= 0"
        " AND km_excedentes >= 0 AND combustible_faltante >= 0 AND monto_final > 0)",
    )

    _trigger("unidad", (*UNIDAD, "kilometraje"))
    _trigger("contrato_alquiler", (*CONTRATO, *CIERRE))


def downgrade() -> None:
    _trigger("contrato_alquiler", CONTRATO)
    _trigger("unidad", UNIDAD)
    op.drop_constraint("ck_contrato_alquiler_cierre", "contrato_alquiler", type_="check")
    for columna in reversed(CIERRE):
        op.drop_column("contrato_alquiler", columna)
    op.drop_constraint("ck_unidad_kilometraje", "unidad", type_="check")
    op.drop_column("unidad", "kilometraje")
