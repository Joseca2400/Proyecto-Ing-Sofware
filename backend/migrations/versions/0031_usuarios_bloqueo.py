"""HU-1.09: bloqueo por intentos fallidos y baja de usuarios.

La bitácora de `usuarios` pasa a mostrar también los intentos fallidos, el bloqueo y la baja
(nunca la contraseña): sin ellos, un intento fallido dejaba un registro sin ningún cambio visible.

Revision ID: 0031
Revises: 0030
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0031"
down_revision: str | None = "0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


COLUMNAS = ("id", "correo", "nombre", "rol", "activo", "creado_en")


def _auditar(*columnas: str) -> None:
    argumentos = ", ".join(f"'{columna}'" for columna in columnas)
    op.execute("DROP TRIGGER auditar_usuarios ON usuarios")
    op.execute(f"""
        CREATE TRIGGER auditar_usuarios AFTER INSERT OR UPDATE OR DELETE ON usuarios
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio({argumentos})
    """)


def upgrade() -> None:
    op.add_column(
        "usuarios", sa.Column("intentos_fallidos", sa.Integer(), server_default="0", nullable=False)
    )
    op.add_column("usuarios", sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True))
    op.add_column("usuarios", sa.Column("baja_en", sa.DateTime(timezone=True), nullable=True))
    _auditar(*COLUMNAS, "intentos_fallidos", "bloqueado_hasta", "baja_en")


def downgrade() -> None:
    _auditar(*COLUMNAS)
    op.drop_column("usuarios", "baja_en")
    op.drop_column("usuarios", "bloqueado_hasta")
    op.drop_column("usuarios", "intentos_fallidos")
