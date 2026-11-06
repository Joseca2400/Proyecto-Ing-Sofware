"""Guardas de integración entre equipos: una sola cadena de migraciones y auditoría en cada tabla."""

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from app.comun.db import Base, SessionLocal

# Tablas que la bitácora no copia a propósito (HU-1.11): sesiones guarda hashes de tokens.
SIN_AUDITORIA = {"sesiones", "bitacora"}


def test_las_migraciones_tienen_una_sola_cabeza():
    """Dos ramas que migran desde la misma base dejan dos cabezas y `alembic upgrade head` falla."""
    cabezas = ScriptDirectory.from_config(Config("alembic.ini")).get_heads()
    assert len(cabezas) == 1, f"Hay varias cabezas de migración: {cabezas}. Rebasa la migración nueva."


def test_toda_tabla_de_negocio_tiene_trigger_de_auditoria():
    """Una tabla nueva sin `public.registrar_cambio` no deja rastro en la bitácora (HU-1.11)."""
    with SessionLocal() as db:
        auditadas = set(
            db.scalars(
                text(
                    """
                    SELECT c.relname FROM pg_trigger t
                    JOIN pg_class c ON c.oid = t.tgrelid
                    JOIN pg_proc p ON p.oid = t.tgfoid
                    WHERE NOT t.tgisinternal AND p.proname = 'registrar_cambio'
                    """
                )
            )
        )
    faltan = set(Base.metadata.tables) - SIN_AUDITORIA - auditadas
    assert not faltan, f"Sin trigger de auditoría: {sorted(faltan)}. Ver backend/README.md (HU-1.11)."
