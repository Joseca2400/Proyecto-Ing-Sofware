from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.alquileres import service
from app.modulos.alquileres.schemas import (
    ConceptoCambio,
    ConceptoEntrada,
    ConceptoSalida,
    CotizacionEntrada,
    CotizacionSalida,
    TarifaEntrada,
    TarifaSalida,
    TemporadaEntrada,
    TemporadaSalida,
)

# Pendiente (HU-1.09/HU-1.10): igual que el resto del Sprint 1, las rutas siguen abiertas hasta
# que el front tenga login (tarea C1). Entonces las altas y cambios del tarifario llevan
# `Depends(requiere_rol(GERENTE_FINANCIERO))` y las consultas y la cotización `usuario_actual`.
router = APIRouter(prefix="/alquileres", tags=["Alquileres"])


# ── HU-3.05: tarifario de alquiler ─────────────────────────────────────────────


@router.get("/tipos-vehiculo", response_model=list[str])
def tipos_vehiculo() -> list[str]:
    return list(service.TIPOS_VEHICULO)


@router.get("/temporadas", response_model=list[TemporadaSalida])
def listar_temporadas(db: Session = Depends(get_db)) -> list[TemporadaSalida]:
    return [TemporadaSalida.model_validate(t) for t in service.listar_temporadas(db)]


@router.post("/temporadas", response_model=TemporadaSalida, status_code=201)
def registrar_temporada(datos: TemporadaEntrada, db: Session = Depends(get_db)) -> TemporadaSalida:
    return TemporadaSalida.model_validate(service.registrar_temporada(db, datos))


@router.post("/temporadas/{temporada_id}/desactivar", response_model=TemporadaSalida)
def desactivar_temporada(temporada_id: int, db: Session = Depends(get_db)) -> TemporadaSalida:
    return TemporadaSalida.model_validate(service.desactivar_temporada(db, temporada_id))


@router.get("/tarifas", response_model=list[TarifaSalida])
def listar_tarifas(
    tipo_vehiculo: str | None = None,
    vin: str | None = None,
    temporada_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[TarifaSalida]:
    tarifas = service.listar_tarifas(db, tipo_vehiculo, vin, temporada_id)
    return [TarifaSalida.model_validate(t) for t in tarifas]


@router.post("/tarifas", response_model=TarifaSalida, status_code=201)
def registrar_tarifa(datos: TarifaEntrada, db: Session = Depends(get_db)) -> TarifaSalida:
    return TarifaSalida.model_validate(service.registrar_tarifa(db, datos))


@router.get("/conceptos", response_model=list[ConceptoSalida])
def listar_conceptos(solo_activos: bool = False, db: Session = Depends(get_db)) -> list[ConceptoSalida]:
    return [ConceptoSalida.model_validate(c) for c in service.listar_conceptos(db, solo_activos)]


@router.post("/conceptos", response_model=ConceptoSalida, status_code=201)
def registrar_concepto(datos: ConceptoEntrada, db: Session = Depends(get_db)) -> ConceptoSalida:
    return ConceptoSalida.model_validate(service.registrar_concepto(db, datos))


@router.put("/conceptos/{concepto_id}", response_model=ConceptoSalida)
def cambiar_concepto(
    concepto_id: int, datos: ConceptoCambio, db: Session = Depends(get_db)
) -> ConceptoSalida:
    return ConceptoSalida.model_validate(service.cambiar_concepto(db, concepto_id, datos))


@router.post("/cotizaciones", response_model=CotizacionSalida)
def cotizar(datos: CotizacionEntrada, db: Session = Depends(get_db)) -> CotizacionSalida:
    """Monto estimado de un alquiler; no guarda nada."""
    return CotizacionSalida.model_validate(service.cotizar(db, datos))
