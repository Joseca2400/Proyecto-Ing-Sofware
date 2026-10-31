"""Usuario autenticado y permisos por rol, aplicados en el servidor (HU-1.09, acuerdo 4 de K1).

El cliente inicia sesión en `POST /api/v1/auth/login` y envía el token en cada petición:
`Authorization: Bearer <token>`. La matriz de permisos vive aquí, en un solo lugar.
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Rol, SesionUsuario, Usuario
from app.seguridad import usuario_de_token
from app.services.base import ErrorNegocio, Prohibido

REGISTRAN = (Rol.AUXILIAR, Rol.CONTADOR, Rol.GERENTE_FINANCIERO)
REVISAN = (Rol.CONTADOR, Rol.GERENTE_FINANCIERO)
APRUEBAN = (Rol.GERENTE_FINANCIERO,)
TODOS = tuple(Rol)


_bearer = HTTPBearer(auto_error=False, description="Token obtenido en POST /api/v1/auth/login")


def sesion_actual(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> tuple[Usuario, SesionUsuario]:
    if cred is None:
        raise ErrorNegocio("Inicie sesión: falta el encabezado Authorization: Bearer <token>", 401)
    resultado = usuario_de_token(db, cred.credentials)
    if resultado is None:
        raise ErrorNegocio("La sesión no es válida o expiró; inicie sesión de nuevo", 401)
    db.info["actor"] = resultado[0].usuario  # la auditoría registra a este usuario
    return resultado


def usuario_actual(s: tuple[Usuario, SesionUsuario] = Depends(sesion_actual)) -> Usuario:
    return s[0]


def requiere(*roles: Rol):
    def _verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            permitidos = ", ".join(r.value for r in roles)
            raise Prohibido(f"El rol {usuario.rol} no tiene permiso para esta operación (permitido: {permitidos})")
        return usuario
    return _verificar
