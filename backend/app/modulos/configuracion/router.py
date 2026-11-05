from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service
from app.modulos.configuracion.schemas import TipoCambioEntrada, TipoCambioSalida

# Pendiente al mezclar HU-1.09/HU-1.10: exigir sesión y que solo el contador cargue el tipo.
router = APIRouter(prefix="/configuracion", tags=["Configuración"])


@router.get("/tipos-cambio", response_model=list[TipoCambioSalida])
def listar_tipos_cambio(
    desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db)
) -> list[TipoCambioSalida]:
    return [TipoCambioSalida.model_validate(t) for t in service.listar(db, desde, hasta)]


@router.post("/tipos-cambio", response_model=TipoCambioSalida, status_code=201)
def registrar_tipo_cambio(datos: TipoCambioEntrada, db: Session = Depends(get_db)) -> TipoCambioSalida:
    return TipoCambioSalida.model_validate(service.registrar_manual(db, datos.fecha, datos.valor))


@router.get("/tipos-cambio/{fecha}", response_model=TipoCambioSalida)
def consultar_tipo_cambio(fecha: date, db: Session = Depends(get_db)) -> TipoCambioSalida:
    tipo = service.buscar(db, fecha)
    if tipo is None:
        raise ErrorNegocio(f"No existe tipo de cambio para el {fecha:%d/%m/%Y}", status=404)
    return TipoCambioSalida.model_validate(tipo)
