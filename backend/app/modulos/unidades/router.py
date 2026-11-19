from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
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

# Pendiente (HU-1.09/HU-1.10): las rutas siguen abiertas porque el front aún no tiene login
# (tarea C1 del equipo C); exigir sesión hoy dejaría sin funcionar la pantalla de unidades.
# Cuando exista el login del front, proteger con `app.modulos.seguridad.service`:
# - Consultas (GET): `_: Usuario = Depends(usuario_actual)`.
# - Alta (POST): `usuario: Usuario = Depends(requiere_rol(AUXILIAR_CONTABLE, CONTADOR))`.
# - Cambio de estado (POST): `requiere_rol(AUXILIAR_CONTABLE, CONTADOR, GERENTE_FINANCIERO)`; el
#   gerente financiero sigue las etapas de importación (HU-4.07). En ambos POST, pasar `usuario.id`
#   al service para que el historial guarde quién hizo el cambio.
# - Etapas de importación (GET, HU-4.07): `requiere_rol(GERENTE_FINANCIERO, CONTADOR, GERENCIA)`.
# Sin sesión, el historial y la bitácora (HU-1.11) guardan el cambio con el usuario vacío.
router = APIRouter(prefix="/unidades", tags=["Unidades"])


@router.get("/catalogos", response_model=Catalogos)
def catalogos() -> Catalogos:
    return Catalogos(**service.catalogos())


@router.get("/etapas-importacion", response_model=EtapasImportacion)
def etapas_importacion(etapa: Etapa | None = None, db: Session = Depends(get_db)) -> EtapasImportacion:
    """HU-4.07: unidades por etapa con los días en su etapa actual y su costo acumulado."""
    return EtapasImportacion(**service.etapas_importacion(db, etapa))


@router.get("", response_model=list[UnidadSalida])
def listar_unidades(
    estado: Estado | None = None, buscar: str | None = None, db: Session = Depends(get_db)
) -> list[UnidadSalida]:
    return [UnidadSalida.model_validate(u) for u in service.listar_unidades(db, estado, buscar)]


@router.post("", response_model=UnidadSalida, status_code=201)
def registrar_unidad(datos: UnidadEntrada, db: Session = Depends(get_db)) -> UnidadSalida:
    return UnidadSalida.model_validate(service.registrar_unidad(db, datos))


@router.get("/{vin}", response_model=UnidadSalida)
def consultar_unidad(vin: str, db: Session = Depends(get_db)) -> UnidadSalida:
    return UnidadSalida.model_validate(service.obtener_por_vin(db, vin))


@router.post("/{vin}/estado", response_model=UnidadSalida)
def cambiar_estado(vin: str, datos: CambioEstadoEntrada, db: Session = Depends(get_db)) -> UnidadSalida:
    return UnidadSalida.model_validate(service.cambiar_estado(db, vin, datos.estado, datos.documento))


@router.get("/{vin}/historial", response_model=list[CambioEstadoSalida])
def historial(vin: str, db: Session = Depends(get_db)) -> list[CambioEstadoSalida]:
    return [CambioEstadoSalida.model_validate(c) for c in service.historial(db, vin)]
