"""Las pruebas corren siempre contra PostgreSQL, en una base aparte de la de desarrollo.

TEST_DATABASE_URL apunta a esa base (por defecto `sistema_pruebas` en localhost, la del
docker compose). Si no existe se crea, y en cada corrida se vacía y se migra desde cero.
"""

import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://sistema:sistema@localhost:5432/sistema_pruebas",
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.main import app


def _crear_base_si_falta(url: str) -> None:
    destino = make_url(url)
    servidor = create_engine(destino.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with servidor.connect() as conexion:
        existe = conexion.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"), {"nombre": destino.database}
        ).scalar()
        if not existe:
            conexion.execute(text(f'CREATE DATABASE "{destino.database}"'))
    servidor.dispose()


def _vaciar_esquema(url: str) -> None:
    motor = create_engine(url)
    with motor.begin() as conexion:
        conexion.execute(text("DROP SCHEMA public CASCADE"))
        conexion.execute(text("CREATE SCHEMA public"))
    motor.dispose()


@pytest.fixture(scope="session", autouse=True)
def esquema_migrado():
    """Base limpia y migrada una vez por corrida, igual que en el arranque del contenedor."""
    _crear_base_si_falta(TEST_DATABASE_URL)
    _vaciar_esquema(TEST_DATABASE_URL)
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)


CLAVE_PRUEBAS = "Prueba-2026!"  # la misma de test_seguridad y test_contabilidad: las cuentas se crean una vez


@pytest.fixture(scope="module")
def sesion_contador(esquema_migrado) -> dict[str, str]:
    """Encabezado de una sesión de contador. Una por archivo: el hash scrypt del login es lento y
    test_seguridad vence todas las sesiones, así que no puede durar toda la corrida."""
    from app.comun.db import SessionLocal
    from app.modulos.seguridad.semilla import crear_cuentas_iniciales

    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE_PRUEBAS)
    respuesta = TestClient(app).post(
        "/api/v1/seguridad/login", json={"correo": "contador@empresa.gt", "clave": CLAVE_PRUEBAS}
    )
    return {"Authorization": f"Bearer {respuesta.json()['token']}"}


@pytest.fixture
def cliente_contador(sesion_contador) -> TestClient:
    """Para probar reglas de negocio en rutas que exigen sesión; los permisos se prueban aparte."""
    return TestClient(app, headers=sesion_contador)
