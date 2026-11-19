"""HU-2.05: reversión de una partida contabilizada.

La opción más chica y segura: el vínculo vive en la partida NUEVA (`revierte_a`), no en la
original. Así la original no se toca y el trigger `proteger_partida` de 0010 queda igual: una
partida contabilizada sigue sin poder modificarse. "Revertida" se deduce de que exista una
partida que la revierte, y la restricción única sobre `revierte_a` impide revertirla dos veces
aun con dos peticiones simultáneas.

La reversión de una partida automática conserva el documento de origen (la pide el módulo dueño
del documento), así que "una partida por documento" pasa a ser un índice único parcial que solo
cuenta las partidas que no son reversiones. La bitácora de `partida` se vuelve a crear para copiar
también `revierte_a`.

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

COLUMNAS = (
    "id", "numero", "fecha", "concepto", "documento_soporte", "estado", "origen",
    "documento_tipo", "documento_id", "comentario", "creado_por", "contabilizada_por",
    "contabilizada_en",
)  # fmt: skip


def _auditar(columnas: tuple[str, ...]) -> None:
    op.execute("DROP TRIGGER auditar_partida ON partida")
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute(f"""
        CREATE TRIGGER auditar_partida AFTER INSERT OR UPDATE OR DELETE ON partida
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.add_column(
        "partida", sa.Column("revierte_a", sa.Integer(), sa.ForeignKey("partida.id"), nullable=True)
    )
    op.create_unique_constraint("uq_partida_revierte_a", "partida", ["revierte_a"])
    op.drop_constraint("uq_partida_documento", "partida")
    op.create_index(
        "uq_partida_documento",
        "partida",
        ["documento_tipo", "documento_id"],
        unique=True,
        postgresql_where=sa.text("revierte_a IS NULL"),
    )
    _auditar((*COLUMNAS, "revierte_a"))


def downgrade() -> None:
    _auditar(COLUMNAS)
    op.drop_index("uq_partida_documento", "partida")
    # Falla si una reversión comparte documento con su original: las contabilizadas no se borran.
    op.create_unique_constraint("uq_partida_documento", "partida", ["documento_tipo", "documento_id"])
    op.drop_constraint("uq_partida_revierte_a", "partida")
    op.drop_column("partida", "revierte_a")
