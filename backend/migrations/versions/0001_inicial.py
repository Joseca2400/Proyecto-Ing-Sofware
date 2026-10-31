"""Línea base del esquema (Sprint 0).

No crea tablas de negocio: deja registrada la primera revisión para que cada módulo
agregue las suyas con `alembic revision --autogenerate -m "..."`.

Revision ID: 0001
Revises:
Create Date: 2026-10-30
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
