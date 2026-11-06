from pydantic import BaseModel


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
