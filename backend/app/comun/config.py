"""Configuración tomada de variables de entorno."""

import os
from decimal import Decimal

APP_NOMBRE = "Sistema administrativo y financiero"
APP_VERSION = "0.1.0"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://sistema:sistema@localhost:5432/sistema",
)

# El sistema solo corre sobre PostgreSQL (NUMERIC exacto, JSONB, transacciones, triggers).
if not DATABASE_URL.startswith("postgresql"):
    raise RuntimeError("DATABASE_URL debe apuntar a PostgreSQL (postgresql+psycopg://...)")

SESION_MINUTOS = int(os.getenv("SESION_MINUTOS", "480"))
# Contraseña de las cuentas iniciales (`python -m app.modulos.seguridad.semilla`); sin valor por defecto.
CLAVE_INICIAL = os.getenv("CLAVE_INICIAL")

# Certificador FEL (`comun/fel.py`): "simulado" hasta que se contrate el real (Sprint 3).
FEL_CERTIFICADOR = os.getenv("FEL_CERTIFICADOR", "simulado")
# Total en quetzales sobre el cual la SAT exige NIT o CUI (no "Consumidor Final"); lo confirma el contador.
UMBRAL_CONSUMIDOR_FINAL = Decimal(os.getenv("UMBRAL_CONSUMIDOR_FINAL", "2500.00"))
# Días en un mismo estado a partir de los cuales el reporte por etapa destaca la unidad (HU-7.04).
DIAS_LIMITE_ETAPA = int(os.getenv("DIAS_LIMITE_ETAPA", "30"))
