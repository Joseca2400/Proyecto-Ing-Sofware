"""Configuración de la aplicación, tomada de variables de entorno."""

import os
from decimal import Decimal

DATABASE_URL: str = os.getenv("SISTEMA_DB_URL", "sqlite:///./sistema.db")

# Tasa de IVA en Guatemala (los precios de alquiler se capturan con IVA incluido).
TASA_IVA: Decimal = Decimal(os.getenv("SISTEMA_TASA_IVA", "0.12"))

# Monto a partir del cual la SAT exige NIT o CUI (no se permite "Consumidor Final").
# Verificar el umbral vigente con el contador antes de producción.
UMBRAL_CONSUMIDOR_FINAL: Decimal = Decimal(os.getenv("SISTEMA_UMBRAL_CF", "2500"))

# Tarifa horaria interna de costo de mano de obra del taller (HU-5.02, versión del corte).
TARIFA_HORA_TALLER: Decimal = Decimal(os.getenv("SISTEMA_TARIFA_HORA_TALLER", "75"))

# Sesiones (HU-1.09): duración del token y costo del hash de contraseñas.
HORAS_SESION: int = int(os.getenv("SISTEMA_HORAS_SESION", "8"))
ITERACIONES_HASH: int = int(os.getenv("SISTEMA_ITERACIONES_HASH", "240000"))

# Contraseña inicial de las cuentas sembradas (sólo ambiente de pruebas).
PASSWORD_INICIAL: str = os.getenv("SISTEMA_PASSWORD_INICIAL", "Demo2026!")

# Alquiler, facturación, cobros y reportes quedan fuera del Sprint 1 (Sprint1.md, sección 2).
# El código existe como adelanto; se habilita con SISTEMA_MODULOS_INGRESO=true.
MODULOS_INGRESO: bool = os.getenv("SISTEMA_MODULOS_INGRESO", "false").lower() == "true"
