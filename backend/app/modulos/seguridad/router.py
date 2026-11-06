from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Usuario
from app.modulos.seguridad.schemas import BitacoraSalida, LoginEntrada, LoginSalida, UsuarioSalida

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


@router.get("/bitacora", response_model=list[BitacoraSalida])
def bitacora(
    usuario_id: int | None = Query(default=None, ge=1),
    entidad: str | None = Query(default=None, max_length=100),
    vin: str | None = Query(default=None, min_length=17, max_length=17),
    limite: int = Query(default=100, ge=1, le=200),
    desplazamiento: int = Query(default=0, ge=0),
    _: Usuario = Depends(service.requiere_rol(service.CONTADOR, service.GERENTE_FINANCIERO)),
    db: Session = Depends(get_db),
):
    return service.consultar_bitacora(db, usuario_id, entidad, vin, limite, desplazamiento)
