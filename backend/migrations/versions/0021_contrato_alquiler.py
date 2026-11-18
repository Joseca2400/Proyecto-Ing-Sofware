"""HU-3.06: contrato de alquiler y estado "alquilada" de la unidad.

- `contrato_alquiler`: cliente, unidad (VIN), salida, devolución prevista, copia de la tarifa
  vigente, kilometraje y combustible de salida (octavos), depósito esperado, días previstos,
  monto estimado y número correlativo.
- `unidad` y `cambio_estado_unidad` admiten el estado nuevo "alquilada" (módulo `unidades`).
- Bitácora (HU-1.11) en la tabla nueva, con el VIN copiado para filtrarla por unidad.

Revision ID: 0021
Revises: 0024
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: str | None = "0024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

ANTES = "'en_transito', 'en_aduana', 'en_taller', 'lista', 'en_flota', 'en_venta', 'vendida', 'recuperada'"
DESPUES = (
    "'en_transito', 'en_aduana', 'en_taller', 'lista', 'en_flota', 'alquilada', 'en_venta', 'vendida', "
    "'recuperada'"
)

CONTRATO = (
    "id", "numero", "cliente_id", "vin", "salida", "devolucion_prevista", "tarifa_id", "modalidad",
    "moneda", "tarifa_monto", "km_incluido", "precio_km_adicional", "km_salida", "combustible_salida",
    "deposito_esperado", "dias_previstos", "monto_estimado", "estado", "usuario_id", "creado_en",
)  # fmt: skip


def _estados(estados: str) -> None:
    for tabla, nombre, condicion in (
        ("unidad", "ck_unidad_estado", f"estado IN ({estados})"),
        ("cambio_estado_unidad", "ck_cambio_estado_unidad_nuevo", f"estado_nuevo IN ({estados})"),
        (
            "cambio_estado_unidad",
            "ck_cambio_estado_unidad_anterior",
            f"estado_anterior IS NULL OR (estado_anterior IN ({estados}) AND estado_anterior <> estado_nuevo)",
        ),
    ):
        op.drop_constraint(nombre, tabla, type_="check")
        op.create_check_constraint(nombre, tabla, condicion)


def upgrade() -> None:
    _estados(DESPUES)
    op.create_table(
        "contrato_alquiler",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("cliente.id"), nullable=False),
        sa.Column(
            "vin",
            sa.String(17),
            sa.ForeignKey("unidad.vin", name="fk_contrato_alquiler_vin_unidad"),
            nullable=False,
        ),
        sa.Column("salida", sa.DateTime(timezone=True), nullable=False),
        sa.Column("devolucion_prevista", sa.Date(), nullable=False),
        sa.Column("tarifa_id", sa.Integer(), sa.ForeignKey("tarifa.id"), nullable=False),
        sa.Column("modalidad", sa.String(20), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("tarifa_monto", MONTO, nullable=False),
        sa.Column("km_incluido", sa.Integer(), nullable=False),
        sa.Column("precio_km_adicional", MONTO, nullable=False),
        sa.Column("km_salida", sa.Integer(), nullable=False),
        sa.Column("combustible_salida", sa.SmallInteger(), nullable=False),
        sa.Column("deposito_esperado", MONTO, nullable=False),
        sa.Column("dias_previstos", sa.Integer(), nullable=False),
        sa.Column("monto_estimado", MONTO, nullable=False),
        sa.Column("estado", sa.String(10), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("numero", name="contrato_alquiler_numero_key"),
        sa.CheckConstraint("estado IN ('abierto', 'cerrado')", name="ck_contrato_alquiler_estado"),
        sa.CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')",
            name="ck_contrato_alquiler_modalidad",
        ),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_contrato_alquiler_moneda"),
        sa.CheckConstraint(
            "combustible_salida BETWEEN 0 AND 8 AND km_salida >= 0", name="ck_contrato_alquiler_salida"
        ),
        sa.CheckConstraint(
            "tarifa_monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0 AND deposito_esperado >= 0"
            " AND dias_previstos >= 1 AND monto_estimado > 0",
            name="ck_contrato_alquiler_montos",
        ),
    )
    op.create_index("ix_contrato_alquiler_cliente_id", "contrato_alquiler", ["cliente_id"])
    op.create_index("ix_contrato_alquiler_vin", "contrato_alquiler", ["vin"])
    op.create_index("ix_contrato_alquiler_estado", "contrato_alquiler", ["estado"])
    argumentos = ", ".join(f"'{columna}'" for columna in CONTRATO)
    op.execute(f"""
        CREATE TRIGGER auditar_contrato_alquiler AFTER INSERT OR UPDATE OR DELETE ON contrato_alquiler
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_contrato_alquiler ON contrato_alquiler")
    op.drop_table("contrato_alquiler")
    # Las unidades alquiladas vuelven a la flota para cumplir la restricción anterior.
    op.execute("UPDATE unidad SET estado = 'en_flota' WHERE estado = 'alquilada'")
    op.execute(
        "DELETE FROM cambio_estado_unidad WHERE 'alquilada' IN (estado_nuevo, coalesce(estado_anterior, ''))"
    )
    _estados(ANTES)
