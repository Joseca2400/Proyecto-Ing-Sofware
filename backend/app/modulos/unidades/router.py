from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    GERENCIA,
    GERENTE_FINANCIERO,
    Usuario,
    requiere_rol,
    usuario_actual,
)
from app.modulos.unidades import service
from app.modulos.unidades.schemas import (
    CambioEstadoEntrada,
    CambioEstadoSalida,
    Catalogos,
    Estado,
    Etapa,
    EtapasImportacion,
    UnidadEntrada,
    UnidadSalida,
)

# HU-1.09: todas las rutas exigen sesión. El gerente financiero sigue las etapas de importación
# (HU-4.07), por eso también cambia el estado.
ALTA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)
CAMBIO_ESTADO = requiere_rol(AUXILIAR_CONTABLE, CONTADOR, GERENTE_FINANCIERO)
ETAPAS = requiere_rol(GERENTE_FINANCIERO, CONTADOR, GERENCIA)

router = APIRouter(prefix="/unidades", tags=["Unidades"], dependencies=[Depends(usuario_actual)])


@router.get("/catalogos", response_model=Catalogos)
def catalogos() -> Catalogos:
    return Catalogos(**service.catalogos())


@router.get("/etapas-importacion", response_model=EtapasImportacion)
def etapas_importacion(
    etapa: Etapa | None = None, _: Usuario = Depends(ETAPAS), db: Session = Depends(get_db)
) -> EtapasImportacion:
    """HU-4.07: unidades por etapa con los días en su etapa actual y su costo acumulado."""
    return EtapasImportacion(**service.etapas_importacion(db, etapa))


@router.get("", response_model=list[UnidadSalida])
def listar_unidades(
    estado: Estado | None = None, buscar: str | None = None, db: Session = Depends(get_db)
) -> list[UnidadSalida]:
    return [UnidadSalida.model_validate(u) for u in service.listar_unidades(db, estado, buscar)]


@router.post("", response_model=UnidadSalida, status_code=201)
def registrar_unidad(
    datos: UnidadEntrada, usuario: Usuario = Depends(ALTA), db: Session = Depends(get_db)
) -> UnidadSalida:
    return UnidadSalida.model_validate(service.registrar_unidad(db, datos, usuario.id))


@router.get("/{vin}", response_model=UnidadSalida)
def consultar_unidad(vin: str, db: Session = Depends(get_db)) -> UnidadSalida:
    return UnidadSalida.model_validate(service.obtener_por_vin(db, vin))


@router.post("/{vin}/estado", response_model=UnidadSalida)
def cambiar_estado(
    vin: str,
    datos: CambioEstadoEntrada,
    usuario: Usuario = Depends(CAMBIO_ESTADO),
    db: Session = Depends(get_db),
) -> UnidadSalida:
    return UnidadSalida.model_validate(
        service.cambiar_estado(db, vin, datos.estado, datos.documento, usuario.id)
    )


@router.get("/{vin}/historial", response_model=list[CambioEstadoSalida])
def historial(vin: str, db: Session = Depends(get_db)) -> list[CambioEstadoSalida]:
    return [CambioEstadoSalida.model_validate(c) for c in service.historial(db, vin)]
