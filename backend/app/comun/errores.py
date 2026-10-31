"""Errores de negocio con el formato común de la API: `{"detail": "..."}`."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class ErrorNegocio(Exception):
    def __init__(self, mensaje: str, status: int = 400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def manejar_error_negocio(_: Request, exc: ErrorNegocio) -> JSONResponse:
        return JSONResponse(status_code=exc.status, content={"detail": exc.mensaje})
