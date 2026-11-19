"""HU-2.09: reglas de las cuentas de ganancia y pérdida por diferencial cambiario realizado.

Las usará la partida de los pagos y cobros en USD (Sprint 3) a través de
`contabilidad.service.diferencial_cambiario`; el contador puede cambiarlas desde la pantalla.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-18
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO regla_contabilizacion (documento_tipo, concepto, descripcion, cuenta_codigo) VALUES
        ('diferencial_cambiario', 'ganancia', 'Ganancia cambiaria realizada al pagar o cobrar en USD', '4.4'),
        ('diferencial_cambiario', 'perdida', 'Pérdida cambiaria realizada al pagar o cobrar en USD', '6.3')
    """)


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'diferencial_cambiario'")
