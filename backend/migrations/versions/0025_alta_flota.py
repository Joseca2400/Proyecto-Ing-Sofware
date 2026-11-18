"""HU-3.01: alta de la unidad como activo fijo de la flota.

- `alta_flota`: una por VIN, con la fecha, el costo de la hoja de costo (HU-4.08), la partida que lo
  traslada y quién la registró. Bitácora (HU-1.11) con el VIN.
- Reglas de contabilización de `alta_flota`: activo fijo – flota 1.2.01 y unidades en proceso
  1.1.04.01 (las del catálogo semilla); el contador las ajusta después.

Revision ID: 0025
Revises: 0023
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: str | None = "0023"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MONTO = sa.Numeric(18, 6)

ALTA = ("id", "vin", "fecha", "costo", "partida_id", "usuario_id", "creado_en")
REGLAS = (
    ("alta_flota", "activo_flota", "Costo de la unidad dada de alta (activo fijo – flota)", "1.2.01"),
    ("alta_flota", "unidad_en_proceso", "Costo trasladado desde unidades en proceso", "1.1.04.01"),
)


def upgrade() -> None:
    op.create_table(
        "alta_flota",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vin", sa.String(17), sa.ForeignKey("unidad.vin", name="fk_alta_flota_vin_unidad"), nullable=False
        ),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("costo", MONTO, nullable=False),
        sa.Column(
            "partida_id",
            sa.Integer(),
            sa.ForeignKey("partida.id", name="fk_alta_flota_partida"),
            nullable=False,
        ),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vin", name="uq_alta_flota_vin"),
        sa.UniqueConstraint("partida_id", name="uq_alta_flota_partida"),
        sa.CheckConstraint("costo > 0", name="ck_alta_flota_costo"),
    )
    argumentos = ", ".join(f"'{columna}'" for columna in ALTA)
    op.execute(f"""
        CREATE TRIGGER auditar_alta_flota AFTER INSERT OR UPDATE OR DELETE ON alta_flota
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)
    for tipo, concepto, descripcion, cuenta in REGLAS:
        op.execute(
            sa.text(
                "INSERT INTO regla_contabilizacion (documento_tipo, concepto, descripcion, cuenta_codigo)"
                " VALUES (:tipo, :concepto, :descripcion, :cuenta)"
            ).bindparams(tipo=tipo, concepto=concepto, descripcion=descripcion, cuenta=cuenta)
        )


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'alta_flota'")
    op.drop_table("alta_flota")
