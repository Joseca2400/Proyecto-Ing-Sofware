from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    Usuario,
    requiere_rol,
    usuario_actual,
)
from app.modulos.taller import service
from app.modulos.taller.schemas import (
    HoraEntrada,
    HoraSalida,
    OrdenEntrada,
    OrdenSalida,
    TarifaEntrada,
    TarifaSalida,
)

# Todas las rutas exigen sesión; las tarifas y el cierre los hace el contador, y el auxiliar
# contable con el contador abren las órdenes y registran las horas.
CONTADOR_ = requiere_rol(CONTADOR)
CAPTURA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)

router = APIRouter(prefix="/taller", tags=["Taller"], dependencies=[Depends(usuario_actual)])


@router.get("/tarifas", response_model=list[TarifaSalida])
def listar_tarifas(db: Session = Depends(get_db)) -> list[TarifaSalida]:
    return [TarifaSalida.model_validate(t) for t in service.listar_tarifas(db)]


@router.post("/tarifas", response_model=TarifaSalida, status_code=201)
def crear_tarifa(
    datos: TarifaEntrada, usuario: Usuario = Depends(CONTADOR_), db: Session = Depends(get_db)
) -> TarifaSalida:
    return TarifaSalida.model_validate(service.crear_tarifa(db, datos, usuario.id))


@router.get("/ordenes", response_model=list[OrdenSalida])
def listar_ordenes(
    estado: Literal["abierta", "cerrada"] | None = None, vin: str | None = None, db: Session = Depends(get_db)
) -> list[OrdenSalida]:
    return [OrdenSalida.model_validate(o) for o in service.listar_ordenes(db, estado, vin)]


@router.post("/ordenes", response_model=OrdenSalida, status_code=201)
def abrir_orden(
    datos: OrdenEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> OrdenSalida:
    return OrdenSalida.model_validate(service.abrir_orden(db, datos, usuario.id))


@router.get("/ordenes/{orden_id}", response_model=OrdenSalida)
def consultar_orden(orden_id: int, db: Session = Depends(get_db)) -> OrdenSalida:
    return OrdenSalida.model_validate(service.obtener_orden(db, orden_id))


@router.get("/ordenes/{orden_id}/horas", response_model=list[HoraSalida])
def listar_horas(orden_id: int, db: Session = Depends(get_db)) -> list[HoraSalida]:
    return [HoraSalida.model_validate(h) for h in service.listar_horas(db, orden_id)]


@router.post("/ordenes/{orden_id}/horas", response_model=HoraSalida, status_code=201)
def registrar_horas(
    orden_id: int, datos: HoraEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> HoraSalida:
    return HoraSalida.model_validate(service.registrar_horas(db, orden_id, datos, usuario.id))
