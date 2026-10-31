"""API del sistema administrativo y financiero (alquiler, venta y taller de vehículos)."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import auditoria  # noqa: F401  registra la auditoría automática
from app import config
from app.database import Base, SessionLocal, engine
from app.routers import base, ciclo, ingreso
from app.services.base import ErrorNegocio, sembrar_datos_iniciales


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Sprint 1: el esquema se crea al iniciar; se migrará a Alembic en el Sprint 2.
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        sembrar_datos_iniciales(db)
    yield


app = FastAPI(
    title="Sistema contable · Alquiler, venta y taller de vehículos",
    version="0.1.0",
    description=(
        "**Sprint 1 · Corte transversal: de la compra al alta en flota.** Cada paso genera su partida:\n\n"
        "Compra en EE. UU. (USD) → gastos de importación → taller → hoja de costo → alta en flota.\n\n"
        "Inicie sesión en `POST /api/v1/auth/login` y use el botón **Authorize** con el token. "
        "Usuarios de prueba: `aux`, `contador`, `gerente` y `gerencia` (contraseña inicial `Demo2026!`)."
    ),
    lifespan=lifespan,
)

# Permite que la maqueta HTML/JS llame a la API desde el navegador.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(ErrorNegocio)
async def manejar_error_negocio(_: Request, exc: ErrorNegocio):
    return JSONResponse(status_code=exc.status, content={"detail": exc.mensaje})


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}


app.include_router(base.router, prefix="/api/v1")
app.include_router(ciclo.router, prefix="/api/v1")
if config.MODULOS_INGRESO:  # fuera del alcance del Sprint 1 (Sprint1.md, sección 2)
    app.include_router(ingreso.router, prefix="/api/v1")
