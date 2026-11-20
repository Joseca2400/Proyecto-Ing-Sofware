"""HU-3.05: tarifario de alquiler (temporadas, tarifas con vigencia y conceptos con su tratamiento
fiscal). Carga los conceptos más comunes sin precio; el gerente financiero les pone precio desde
la pantalla. Incluye los triggers de auditoría (HU-1.11).

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = {
    "temporada_alquiler": ("id", "nombre", "fecha_inicio", "fecha_fin", "activa", "creado_en"),
    "tarifa_alquiler": (
        "id", "temporada_id", "tipo_vehiculo", "vin", "modalidad", "moneda", "monto", "km_incluido",
        "costo_km_adicional", "vigente_desde", "creado_en",
    ),
    "concepto_alquiler": (
        "id", "nombre", "naturaleza", "aplica_iva", "precio_sugerido", "moneda", "activo", "creado_en",
    ),
}  # fmt: skip

CONCEPTOS_INICIALES = (
    ("Depósito en garantía", "deposito", False),
    ("GPS", "ingreso", True),
    ("Silla para bebé", "ingreso", True),
    ("Conductor adicional", "ingreso", True),
    ("Entrega con tanque incompleto", "ingreso", True),
    ("Reintegro de multa de tránsito", "reintegro", False),
)


def upgrade() -> None:
    op.create_table(
        "temporada_alquiler",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=False),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("fecha_fin >= fecha_inicio", name="ck_temporada_alquiler_fechas"),
    )
    op.create_table(
        "tarifa_alquiler",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("temporada_id", sa.Integer(), sa.ForeignKey("temporada_alquiler.id"), nullable=True),
        sa.Column("tipo_vehiculo", sa.String(20), nullable=True),
        sa.Column("vin", sa.String(17), nullable=True),
        sa.Column("modalidad", sa.String(15), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("monto", sa.Numeric(18, 6), nullable=False),
        sa.Column("km_incluido", sa.Integer(), nullable=True),
        sa.Column("costo_km_adicional", sa.Numeric(18, 6), nullable=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("(tipo_vehiculo IS NULL) <> (vin IS NULL)", name="ck_tarifa_alquiler_alcance"),
        sa.CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'kilometraje')",
            name="ck_tarifa_alquiler_modalidad",
        ),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_tarifa_alquiler_moneda"),
        sa.CheckConstraint("monto > 0", name="ck_tarifa_alquiler_monto"),
        sa.CheckConstraint("km_incluido IS NULL OR km_incluido >= 0", name="ck_tarifa_alquiler_km"),
        sa.CheckConstraint(
            "costo_km_adicional IS NULL OR costo_km_adicional >= 0", name="ck_tarifa_alquiler_costo_km"
        ),
        sa.CheckConstraint(
            "modalidad <> 'kilometraje' OR (km_incluido IS NOT NULL AND costo_km_adicional IS NOT NULL)",
            name="ck_tarifa_alquiler_kilometraje",
        ),
        sa.UniqueConstraint(
            "temporada_id",
            "tipo_vehiculo",
            "vin",
            "modalidad",
            "moneda",
            "vigente_desde",
            name="uq_tarifa_alquiler_version",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index("ix_tarifa_alquiler_temporada_id", "tarifa_alquiler", ["temporada_id"])
    op.create_index("ix_tarifa_alquiler_vin", "tarifa_alquiler", ["vin"])
    conceptos = op.create_table(
        "concepto_alquiler",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column("naturaleza", sa.String(10), nullable=False),
        sa.Column("aplica_iva", sa.Boolean(), nullable=False),
        sa.Column("precio_sugerido", sa.Numeric(18, 6), nullable=True),
        sa.Column("moneda", sa.String(3), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("nombre"),
        sa.CheckConstraint(
            "naturaleza IN ('ingreso', 'deposito', 'reintegro')", name="ck_concepto_alquiler_naturaleza"
        ),
        sa.CheckConstraint("naturaleza = 'ingreso' OR NOT aplica_iva", name="ck_concepto_alquiler_iva"),
        sa.CheckConstraint(
            "(precio_sugerido IS NULL) = (moneda IS NULL)", name="ck_concepto_alquiler_precio_moneda"
        ),
        sa.CheckConstraint(
            "precio_sugerido IS NULL OR precio_sugerido > 0", name="ck_concepto_alquiler_precio"
        ),
        sa.CheckConstraint("moneda IS NULL OR moneda IN ('GTQ', 'USD')", name="ck_concepto_alquiler_moneda"),
    )

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.bulk_insert(
        conceptos,
        [
            {"nombre": nombre, "naturaleza": naturaleza, "aplica_iva": iva, "activo": True}
            for nombre, naturaleza, iva in CONCEPTOS_INICIALES
        ],
    )


def downgrade() -> None:
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    op.drop_table("concepto_alquiler")
    op.drop_index("ix_tarifa_alquiler_vin", table_name="tarifa_alquiler")
    op.drop_index("ix_tarifa_alquiler_temporada_id", table_name="tarifa_alquiler")
    op.drop_table("tarifa_alquiler")
    op.drop_table("temporada_alquiler")
