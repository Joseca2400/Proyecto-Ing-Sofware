"""API del sistema administrativo y financiero (alquiler, venta y taller de vehículos)."""

from fastapi import FastAPI

from app.comun import config
from app.comun.errores import registrar_manejadores
from app.modulos.sistema.router import router as sistema_router

app = FastAPI(title=config.APP_NOMBRE, version=config.APP_VERSION)

registrar_manejadores(app)


@app.get("/health", tags=["Sistema"])
def health() -> dict[str, str]:
    """Prueba de vida para Docker y el proxy; no toca la base de datos."""
    return {"status": "ok"}


# Cada módulo nuevo se registra aquí, siempre bajo /api/v1.
app.include_router(sistema_router, prefix="/api/v1")
