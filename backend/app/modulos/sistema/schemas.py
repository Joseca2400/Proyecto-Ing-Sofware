from pydantic import BaseModel


class EstadoBaseDatos(BaseModel):
    conectada: bool
    motor: str | None
    revision_esquema: str | None


class EstadoSistema(BaseModel):
    aplicacion: str
    version: str
    mensaje: str
    base_datos: EstadoBaseDatos
