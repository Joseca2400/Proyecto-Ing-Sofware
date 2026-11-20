"""HU-3.13: reglas de las cuentas que lee el reporte de rentabilidad por unidad.

El reporte no crea partidas: lee del mayor, por VIN, las cuentas que estas reglas le asignan a
cada concepto (ingreso de alquiler 4.1, depreciación 6.4 y mantenimiento 6.2). Seguro y marchamo
nacen sin cuenta porque el catálogo aún no tiene la suya: el reporte los muestra como pendientes
hasta que el contador les asigne una desde la pantalla de reglas.

Revision ID: 0034
Revises: 0033
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0034"
down_revision: str | None = "0033"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REGLAS = (
    ("rentabilidad", "ingreso_alquiler", "Ingreso de alquiler de la unidad (reporte de rentabilidad)", "4.1"),
    ("rentabilidad", "depreciacion", "Depreciación de la unidad (reporte de rentabilidad)", "6.4"),
    ("rentabilidad", "mantenimiento", "Mantenimiento de la unidad (reporte de rentabilidad)", "6.2"),
    ("rentabilidad", "seguro", "Seguro de la unidad (reporte de rentabilidad); sin cuenta aún", None),
    ("rentabilidad", "marchamo", "Marchamo de la unidad (reporte de rentabilidad); sin cuenta aún", None),
)  # fmt: skip


def upgrade() -> None:
    for tipo, concepto, descripcion, cuenta in REGLAS:
        op.execute(
            sa.text(
                "INSERT INTO regla_contabilizacion (documento_tipo, concepto, descripcion, cuenta_codigo)"
                " VALUES (:tipo, :concepto, :descripcion, :cuenta)"
            ).bindparams(tipo=tipo, concepto=concepto, descripcion=descripcion, cuenta=cuenta)
        )


def downgrade() -> None:
    op.execute("DELETE FROM regla_contabilizacion WHERE documento_tipo = 'rentabilidad'")
