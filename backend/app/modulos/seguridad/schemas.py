from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, JsonValue


class LoginEntrada(BaseModel):
    correo: str
    clave: str


class UsuarioSalida(BaseModel):
    id: int
    correo: str
    nombre: str
    rol: str


class UsuarioAltaEntrada(BaseModel):
    correo: str = Field(max_length=200)
    nombre: str = Field(max_length=200)
    rol: str = Field(max_length=30)
    clave: str = Field(max_length=200)


class UsuarioAdminSalida(BaseModel):
    id: int
    correo: str
    nombre: str
    rol: str
    estado: str
    creado_en: datetime


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
