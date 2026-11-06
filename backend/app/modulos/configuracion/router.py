from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.configuracion import service
from app.modulos.configuracion.schemas import CuentaEntrada, CuentaSalida, DimensionesEntrada
from app.modulos.seguridad.service import CONTADOR, Usuario, requiere_rol, usuario_actual

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


@router.get("/lineas-negocio", response_model=list[str])
def lineas_negocio(_: Usuario = Depends(usuario_actual)) -> list[str]:
    return list(service.LINEAS_NEGOCIO)


@router.get("/cuentas", response_model=list[CuentaSalida])
def listar_cuentas(
    solo_detalle: bool = False, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
):
    return service.listar_cuentas(db, solo_detalle)


@router.post("/cuentas", response_model=CuentaSalida, status_code=201)
def crear_cuenta(
    datos: CuentaEntrada, _: Usuario = Depends(requiere_rol(CONTADOR)), db: Session = Depends(get_db)
):
    return service.crear_cuenta(db, **datos.model_dump())


@router.put("/cuentas/{cuenta_id}/dimensiones", response_model=CuentaSalida)
def definir_dimensiones(
    cuenta_id: int,
    datos: DimensionesEntrada,
    _: Usuario = Depends(requiere_rol(CONTADOR)),
    db: Session = Depends(get_db),
):
    return service.definir_dimensiones(db, cuenta_id, **datos.model_dump())
