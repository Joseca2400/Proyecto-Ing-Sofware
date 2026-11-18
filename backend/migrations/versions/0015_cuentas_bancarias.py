"""HU-1.08: cuentas bancarias en quetzales y dólares.

- `cuenta_bancaria`: banco, número, tipo, moneda (GTQ o USD) y llave foránea única a la cuenta
  contable `cuentas`; numeración de cheques opcional. Que una de USD se ligue a una cuenta
  monetaria en USD lo valida el service (depende de otra tabla).
- Bitácora (HU-1.11) en la tabla nueva, como en `0011`.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = ("id", "banco", "numero", "tipo", "moneda", "cuenta_id", "siguiente_cheque", "activa", "creado_en")


def upgrade() -> None:
    op.create_table(
        "cuenta_bancaria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("banco", sa.String(100), nullable=False),
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("moneda", sa.String(3), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), sa.ForeignKey("cuentas.id"), nullable=False),
        sa.Column("siguiente_cheque", sa.Integer(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cuenta_id"),
        sa.UniqueConstraint("banco", "numero", name="uq_cuenta_bancaria_banco_numero"),
        sa.CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_cuenta_bancaria_moneda"),
        sa.CheckConstraint("tipo IN ('monetaria', 'ahorro')", name="ck_cuenta_bancaria_tipo"),
        sa.CheckConstraint(
            "siguiente_cheque IS NULL OR siguiente_cheque >= 1", name="ck_cuenta_bancaria_cheque"
        ),
    )
    argumentos = ", ".join(f"'{c}'" for c in COLUMNAS)
    op.execute(f"""
        CREATE TRIGGER auditar_cuenta_bancaria AFTER INSERT OR UPDATE OR DELETE ON cuenta_bancaria
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER auditar_cuenta_bancaria ON cuenta_bancaria")
    op.drop_table("cuenta_bancaria")
