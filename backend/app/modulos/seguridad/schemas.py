from datetime import datetime

from pydantic import BaseModel, ConfigDict, JsonValue


class LoginEntrada(BaseModel):
    correo: str
    clave: str


class UsuarioSalida(BaseModel):
    id: int
    correo: str
    nombre: str
    rol: str


class LoginSalida(BaseModel):
    token: str
    usuario: UsuarioSalida


class BitacoraSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    fecha: datetime
    entidad: str
    registro_id: str
    accion: str
    vin: str | None
    anteriores: dict[str, JsonValue] | None
    nuevos: dict[str, JsonValue] | None
