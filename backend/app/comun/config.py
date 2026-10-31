"""Configuración tomada de variables de entorno."""

import os

APP_NOMBRE = "Sistema administrativo y financiero"
APP_VERSION = "0.1.0"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://sistema:sistema@localhost:5432/sistema",
)
