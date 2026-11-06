"""Conexión a la base de datos. Cada módulo declara sus tablas heredando de `Base`."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.comun import config

engine = create_engine(config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


@event.listens_for(Session, "after_begin")
def _actor_de_transaccion(sesion, transaccion, conexion) -> None:
    """HU-1.11: el actor no se filtra a la siguiente conexión del pool."""
    conexion.execute(
        text("SELECT set_config('app.usuario_id', :actor, true)"),
        {"actor": str(sesion.info.get("usuario_id", ""))},
    )


def fijar_actor(sesion: Session, usuario_id: int) -> None:
    """Identidad obtenida por seguridad; aplica a las transacciones de esta sesión."""
    sesion.info["usuario_id"] = usuario_id
    sesion.execute(text("SELECT set_config('app.usuario_id', :actor, true)"), {"actor": str(usuario_id)})


def get_db() -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por petición."""
    with SessionLocal() as sesion:
        yield sesion
