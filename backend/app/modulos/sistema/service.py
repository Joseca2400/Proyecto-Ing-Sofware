from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.comun import config
from app.modulos.sistema.schemas import EstadoBaseDatos, EstadoSistema


def estado_base_datos(db: Session) -> EstadoBaseDatos:
    """Prueba la conexión y lee la revisión aplicada por Alembic, si existe."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return EstadoBaseDatos(conectada=False, motor=None, revision_esquema=None)

    try:
        revision = db.execute(text("SELECT version_num FROM alembic_version")).scalar()
    except SQLAlchemyError:
        db.rollback()
        revision = None
    return EstadoBaseDatos(conectada=True, motor=db.get_bind().dialect.name, revision_esquema=revision)


def estado_sistema(db: Session) -> EstadoSistema:
    return EstadoSistema(
        aplicacion=config.APP_NOMBRE,
        version=config.APP_VERSION,
        mensaje="Hola, mundo: la API responde",
        base_datos=estado_base_datos(db),
    )
