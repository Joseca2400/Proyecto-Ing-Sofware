from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Usuario
from app.modulos.seguridad.schemas import LoginEntrada, LoginSalida, UsuarioSalida

router = APIRouter(prefix="/seguridad", tags=["Seguridad"])


@router.post("/login", response_model=LoginSalida)
def login(datos: LoginEntrada, db: Session = Depends(get_db)) -> LoginSalida:
    token, usuario = service.iniciar_sesion(db, datos.correo, datos.clave)
    return LoginSalida(token=token, usuario=UsuarioSalida.model_validate(usuario, from_attributes=True))


@router.post("/logout", status_code=204)
def logout(
    autorizacion: str | None = Header(default=None, alias="Authorization"),
    _: Usuario = Depends(service.usuario_actual),
    db: Session = Depends(get_db),
) -> None:
    service.cerrar_sesion(db, service.token_del_encabezado(autorizacion))


@router.get("/yo", response_model=UsuarioSalida)
def yo(usuario: Usuario = Depends(service.usuario_actual)) -> UsuarioSalida:
    return UsuarioSalida.model_validate(usuario, from_attributes=True)
