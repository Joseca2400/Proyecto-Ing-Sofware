from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Usuario
from app.modulos.seguridad.schemas import (
    BitacoraSalida,
    LoginEntrada,
    LoginSalida,
    UsuarioAdminSalida,
    UsuarioAltaEntrada,
    UsuarioSalida,
)

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


def _admin(usuario: Usuario) -> UsuarioAdminSalida:
    return UsuarioAdminSalida(
        id=usuario.id,
        correo=usuario.correo,
        nombre=usuario.nombre,
        rol=usuario.rol,
        estado=service.estado_usuario(usuario),
        creado_en=usuario.creado_en,
    )


# HU-1.09: solo el gerente financiero administra usuarios.
administrador = Depends(service.requiere_rol(service.GERENTE_FINANCIERO))


@router.get("/usuarios", response_model=list[UsuarioAdminSalida])
def listar_usuarios(_: Usuario = administrador, db: Session = Depends(get_db)):
    return [_admin(u) for u in service.listar_usuarios(db)]


@router.post("/usuarios", response_model=UsuarioAdminSalida, status_code=201)
def alta_usuario(datos: UsuarioAltaEntrada, _: Usuario = administrador, db: Session = Depends(get_db)):
    return _admin(service.alta_usuario(db, datos.correo, datos.nombre, datos.rol, datos.clave))


@router.post("/usuarios/{usuario_id}/suspender", response_model=UsuarioAdminSalida)
def suspender(usuario_id: int, usuario: Usuario = administrador, db: Session = Depends(get_db)):
    return _admin(service.suspender_usuario(db, usuario.id, usuario_id))


@router.post("/usuarios/{usuario_id}/reactivar", response_model=UsuarioAdminSalida)
def reactivar(usuario_id: int, usuario: Usuario = administrador, db: Session = Depends(get_db)):
    return _admin(service.reactivar_usuario(db, usuario.id, usuario_id))


@router.post("/usuarios/{usuario_id}/baja", response_model=UsuarioAdminSalida)
def baja(usuario_id: int, usuario: Usuario = administrador, db: Session = Depends(get_db)):
    return _admin(service.dar_de_baja_usuario(db, usuario.id, usuario_id))
