"""Las pruebas usan la base de DATABASE_URL: PostgreSQL en CI y en Docker.

Sin esa variable se usa SQLite en un archivo temporal para correrlas rápido en local.
"""

import os
import tempfile

if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/sistema_pruebas.db"

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def esquema_migrado():
    """Aplica las migraciones una vez, igual que en el arranque del contenedor."""
    command.upgrade(Config("alembic.ini"), "head")


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)
