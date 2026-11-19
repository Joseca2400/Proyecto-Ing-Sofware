"""HU-6.01: clientes individuales o empresas, con NIT, CUI o pasaporte y país, sin duplicados.

Incluye el trigger de auditoría (HU-1.11) con la lista explícita de columnas.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = (
    "id", "tipo", "nombre", "nit", "cui", "pasaporte", "pais", "direccion", "telefono", "correo",
    "agente_retencion_iva", "agente_retencion_isr", "exento_iva", "motivo_exencion", "creado_en",
)  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("nit", sa.String(13), nullable=True),
        sa.Column("cui", sa.String(13), nullable=True),
        sa.Column("pasaporte", sa.String(30), nullable=True),
        sa.Column("pais", sa.String(2), nullable=True),
        sa.Column("direccion", sa.String(300), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(100), nullable=True),
        sa.Column("agente_retencion_iva", sa.Boolean(), nullable=False),
        sa.Column("agente_retencion_isr", sa.Boolean(), nullable=False),
        sa.Column("exento_iva", sa.Boolean(), nullable=False),
        sa.Column("motivo_exencion", sa.String(15), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("nit"),
        sa.UniqueConstraint("cui"),
        sa.UniqueConstraint("pais", "pasaporte", name="uq_cliente_pasaporte"),
        sa.CheckConstraint("tipo IN ('individual', 'empresa')", name="ck_cliente_tipo"),
        sa.CheckConstraint(
            "nit IS NOT NULL OR cui IS NOT NULL OR pasaporte IS NOT NULL",
            name="ck_cliente_identificacion",
        ),
        sa.CheckConstraint("(pasaporte IS NULL) = (pais IS NULL)", name="ck_cliente_pasaporte_pais"),
        sa.CheckConstraint("tipo = 'individual' OR nit IS NOT NULL", name="ck_cliente_empresa_nit"),
        sa.CheckConstraint("cui IS NULL OR cui ~ '^[0-9]{13}$'", name="ck_cliente_cui"),
        sa.CheckConstraint(
            "(exento_iva AND motivo_exencion IN ('diplomatico', 'ong', 'estado', 'otro'))"
            " OR (NOT exento_iva AND motivo_exencion IS NULL)",
            name="ck_cliente_exencion",
        ),
    )
    op.create_index("ix_cliente_nombre", "cliente", ["nombre"])
    argumentos = ", ".join(f"'{columna}'" for columna in COLUMNAS)
    op.execute(f"""
        CREATE TRIGGER auditar_cliente AFTER INSERT OR UPDATE OR DELETE ON cliente
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cliente ON cliente")
    op.drop_index("ix_cliente_nombre", table_name="cliente")
    op.drop_table("cliente")
