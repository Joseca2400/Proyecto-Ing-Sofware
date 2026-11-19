"""HU-1.01: perfil fiscal de la empresa y tasas impositivas, ambos en versiones con vigencia.

Carga las tasas iniciales con vigencia desde el 01/01/2015: es la fecha de carga, anterior a
cualquier operación del sistema, no la fecha legal de cada tasa. Los cambios de ley se registran
como filas nuevas desde la pantalla. Incluye los triggers de auditoría (HU-1.11).

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-19
"""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = {
    "perfil_fiscal": (
        "id", "vigente_desde", "razon_social", "nombre_comercial", "nit", "direccion_fiscal",
        "establecimiento_sat", "regimen_isr", "agente_retencion_iva", "agente_retencion_isr",
        "creado_en",
    ),
    "tasa_impositiva": ("id", "tipo", "tasa", "monto_limite", "vigente_desde", "creado_en"),
}  # fmt: skip

CARGA_INICIAL = date(2015, 1, 1)
TASAS_INICIALES = (
    ("IVA_GENERAL", Decimal("0.12"), None),
    ("ISR_SIMPLIFICADO_1", Decimal("0.05"), Decimal("30000")),  # 5 % hasta Q30,000 al mes
    ("ISR_SIMPLIFICADO_2", Decimal("0.07"), None),  # 7 % sobre el excedente
    ("ISR_UTILIDADES", Decimal("0.25"), None),
    ("ISO", Decimal("0.01"), None),
    ("UMBRAL_CF", None, Decimal("2500")),  # desde este total la factura exige NIT o CUI
)


def upgrade() -> None:
    op.create_table(
        "perfil_fiscal",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("razon_social", sa.String(200), nullable=False),
        sa.Column("nombre_comercial", sa.String(200), nullable=False),
        sa.Column("nit", sa.String(13), nullable=False),
        sa.Column("direccion_fiscal", sa.String(300), nullable=False),
        sa.Column("establecimiento_sat", sa.Integer(), nullable=False),
        sa.Column("regimen_isr", sa.String(25), nullable=False),
        sa.Column("agente_retencion_iva", sa.Boolean(), nullable=False),
        sa.Column("agente_retencion_isr", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("vigente_desde"),
        sa.CheckConstraint(
            "regimen_isr IN ('opcional_simplificado', 'sobre_utilidades')",
            name="ck_perfil_fiscal_regimen",
        ),
        sa.CheckConstraint("establecimiento_sat >= 1", name="ck_perfil_fiscal_establecimiento"),
    )
    tasas = op.create_table(
        "tasa_impositiva",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(25), nullable=False),
        sa.Column("tasa", sa.Numeric(9, 6), nullable=True),
        sa.Column("monto_limite", sa.Numeric(18, 6), nullable=True),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tipo", "vigente_desde", name="uq_tasa_impositiva_tipo_fecha"),
        sa.CheckConstraint(
            "tipo IN ('IVA_GENERAL', 'ISR_SIMPLIFICADO_1', 'ISR_SIMPLIFICADO_2', 'ISR_UTILIDADES', "
            "'ISO', 'UMBRAL_CF')",
            name="ck_tasa_impositiva_tipo",
        ),
        sa.CheckConstraint("tasa IS NULL OR (tasa > 0 AND tasa <= 1)", name="ck_tasa_impositiva_tasa"),
        sa.CheckConstraint("monto_limite IS NULL OR monto_limite > 0", name="ck_tasa_impositiva_limite"),
        sa.CheckConstraint("tasa IS NOT NULL OR monto_limite IS NOT NULL", name="ck_tasa_impositiva_valor"),
    )
    op.create_index("ix_tasa_impositiva_tipo", "tasa_impositiva", ["tipo"])

    for tabla, columnas in COLUMNAS.items():
        argumentos = ", ".join(f"'{columna}'" for columna in columnas)
        op.execute(f"""
            CREATE TRIGGER auditar_{tabla} AFTER INSERT OR UPDATE OR DELETE ON {tabla}
            FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
        """)

    op.bulk_insert(
        tasas,
        [
            {"tipo": tipo, "tasa": tasa, "monto_limite": limite, "vigente_desde": CARGA_INICIAL}
            for tipo, tasa, limite in TASAS_INICIALES
        ],
    )


def downgrade() -> None:
    for tabla in reversed(COLUMNAS):
        op.execute(f"DROP TRIGGER auditar_{tabla} ON {tabla}")
    op.drop_index("ix_tasa_impositiva_tipo", table_name="tasa_impositiva")
    op.drop_table("tasa_impositiva")
    op.drop_table("perfil_fiscal")
