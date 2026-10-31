"""Configuración tomada de variables de entorno."""

import os

APP_NOMBRE = "Sistema administrativo y financiero"
APP_VERSION = "0.1.0"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://sistema:sistema@localhost:5432/sistema",
)

# El sistema solo corre sobre PostgreSQL (NUMERIC exacto, JSONB, transacciones, triggers).
if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError("DATABASE_URL debe apuntar a PostgreSQL (postgresql+psycopg://...)")
