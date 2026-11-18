"""HU-6.01: clientes de alquiler, venta y taller (módulo de facturación).

- `cliente`: individual o empresa, identificado por NIT, CUI o pasaporte con país; único por
  (tipo de identificación, identificación).
- Bitácora (HU-1.11) en la tabla nueva, como en `0011`/`0012`.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CLIENTE = (
    "id", "tipo", "nombre", "tipo_identificacion", "identificacion", "pais", "direccion", "telefono",
    "correo", "agente_retencion_iva", "agente_retencion_isr", "creado_en",
)  # fmt: skip


def upgrade() -> None:
    op.create_table(
        "cliente",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("tipo_identificacion", sa.String(10), nullable=False),
        sa.Column("identificacion", sa.String(30), nullable=False),
        sa.Column("pais", sa.String(2), nullable=True),
        sa.Column("direccion", sa.String(300), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("correo", sa.String(120), nullable=True),
        sa.Column("agente_retencion_iva", sa.Boolean(), nullable=False),
        sa.Column("agente_retencion_isr", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tipo_identificacion", "identificacion", name="uq_cliente_identificacion"),
        sa.CheckConstraint("tipo IN ('individual', 'empresa')", name="ck_cliente_tipo"),
        sa.CheckConstraint(
            "tipo_identificacion IN ('nit', 'cui', 'pasaporte')", name="ck_cliente_tipo_identificacion"
        ),
        sa.CheckConstraint(
            "(tipo_identificacion = 'pasaporte' AND pais IS NOT NULL)"
            " OR (tipo_identificacion <> 'pasaporte' AND pais IS NULL)",
            name="ck_cliente_pais",
        ),
        sa.CheckConstraint(
            "tipo = 'individual' OR tipo_identificacion = 'nit'", name="ck_cliente_empresa_nit"
        ),
    )
    op.create_index("ix_cliente_nombre", "cliente", ["nombre"])
    argumentos = ", ".join(f"'{columna}'" for columna in CLIENTE)
    op.execute(f"""
        CREATE TRIGGER auditar_cliente AFTER INSERT OR UPDATE OR DELETE ON cliente
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cliente ON cliente")
    op.drop_index("ix_cliente_nombre", table_name="cliente")
    op.drop_table("cliente")
