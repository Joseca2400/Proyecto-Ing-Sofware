from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad.service import CONTADOR, Usuario, requiere_rol, usuario_actual
from app.modulos.taller import service
from app.modulos.taller.schemas import TarifaEntrada, TarifaSalida

# Todas las rutas exigen sesión; las tarifas las define el contador.
CONTADOR_ = requiere_rol(CONTADOR)

router = APIRouter(prefix="/taller", tags=["Taller"], dependencies=[Depends(usuario_actual)])


@router.get("/tarifas", response_model=list[TarifaSalida])
def listar_tarifas(db: Session = Depends(get_db)) -> list[TarifaSalida]:
    return [TarifaSalida.model_validate(t) for t in service.listar_tarifas(db)]


@router.post("/tarifas", response_model=TarifaSalida, status_code=201)
def crear_tarifa(
    datos: TarifaEntrada, usuario: Usuario = Depends(CONTADOR_), db: Session = Depends(get_db)
) -> TarifaSalida:
    return TarifaSalida.model_validate(service.crear_tarifa(db, datos, usuario.id))
