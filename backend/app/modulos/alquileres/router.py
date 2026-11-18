from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.alquileres import service
from app.modulos.alquileres.schemas import (
    CatalogosTarifas,
    CierreEntrada,
    ContratoEntrada,
    ContratoSalida,
    Modalidad,
    Moneda,
    TarifaEntrada,
    TarifaSalida,
)
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    Usuario,
    requiere_rol,
    usuario_actual,
)

# Todas las rutas exigen sesión; el alta de tarifas, además, el rol que las registra.
CAPTURA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)

router = APIRouter(prefix="/alquileres", tags=["Alquileres"], dependencies=[Depends(usuario_actual)])


# ── HU-3.05: tarifario ─────────────────────────────────────────────────────────


@router.get("/tarifas/catalogos", response_model=CatalogosTarifas)
def catalogos() -> CatalogosTarifas:
    return CatalogosTarifas(**service.catalogos())


@router.get("/tarifas", response_model=list[TarifaSalida])
def listar_tarifas(
    tipo_vehiculo: str | None = None,
    vin: str | None = None,
    modalidad: Modalidad | None = None,
    db: Session = Depends(get_db),
) -> list[TarifaSalida]:
    return [TarifaSalida.model_validate(t) for t in service.listar_tarifas(db, tipo_vehiculo, vin, modalidad)]


@router.post("/tarifas", response_model=TarifaSalida, status_code=201)
def registrar_tarifa(
    datos: TarifaEntrada, _: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> TarifaSalida:
    return TarifaSalida.model_validate(service.registrar_tarifa(db, datos))


@router.get("/tarifas/vigente", response_model=TarifaSalida)
def tarifa_vigente(
    modalidad: Modalidad,
    moneda: Moneda,
    tipo_vehiculo: str,
    fecha: date | None = None,
    vin: str | None = None,
    db: Session = Depends(get_db),
) -> TarifaSalida:
    """Cotización: la tarifa que aplica hoy (o en `fecha`) a esa unidad o tipo de vehículo."""
    return TarifaSalida.model_validate(
        service.tarifa_vigente(db, fecha or date.today(), modalidad, moneda, tipo_vehiculo, vin)
    )


# ── HU-3.06: contratos ─────────────────────────────────────────────────────────


@router.get("/contratos", response_model=list[ContratoSalida])
def listar_contratos(
    estado: Literal["abierto", "cerrado"] | None = None, vin: str | None = None, db: Session = Depends(get_db)
) -> list[ContratoSalida]:
    return [ContratoSalida.model_validate(c) for c in service.listar_contratos(db, estado, vin)]


@router.post("/contratos", response_model=ContratoSalida, status_code=201)
def registrar_contrato(
    datos: ContratoEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> ContratoSalida:
    return ContratoSalida.model_validate(service.registrar_contrato(db, datos, usuario.id))


@router.get("/contratos/{contrato_id}", response_model=ContratoSalida)
def obtener_contrato(contrato_id: int, db: Session = Depends(get_db)) -> ContratoSalida:
    return ContratoSalida.model_validate(service.obtener_contrato(db, contrato_id))


# ── HU-3.08: cierre ────────────────────────────────────────────────────────────


@router.post("/contratos/{contrato_id}/cierre", response_model=ContratoSalida)
def cerrar_contrato(
    contrato_id: int, datos: CierreEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> ContratoSalida:
    return ContratoSalida.model_validate(service.cerrar_contrato(db, contrato_id, datos, usuario.id))
