from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.alquileres import service
from app.modulos.alquileres.schemas import (
    AplicacionEntrada,
    CatalogosTarifas,
    CierreContratoEntrada,
    ContratoEntrada,
    ContratoSalida,
    DepositoEntrada,
    DepositoSalida,
    DepositosVigentes,
    DevolucionDepositoEntrada,
    Modalidad,
    Moneda,
    TarifaEntrada,
    TarifaSalida,
)
from app.modulos.facturacion.schemas import FacturaSalida
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    Usuario,
    requiere_rol,
    usuario_actual,
)

# Todas las rutas exigen sesión; las altas (tarifas, contratos, cierres, depósitos), además, el rol
# que las registra.
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
    contrato_id: int,
    datos: CierreContratoEntrada,
    usuario: Usuario = Depends(CAPTURA),
    db: Session = Depends(get_db),
) -> ContratoSalida:
    return ContratoSalida.model_validate(service.cerrar_contrato(db, contrato_id, datos, usuario.id))


@router.post("/contratos/{contrato_id}/factura", response_model=FacturaSalida, status_code=201)
def facturar_contrato(
    contrato_id: int, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> FacturaSalida:
    """HU-6.02: factura FEL del cobro del contrato cerrado."""
    return FacturaSalida.model_validate(service.facturar_contrato(db, contrato_id, usuario.id))


# ── HU-3.07: depósitos en garantía ─────────────────────────────────────────────


@router.get("/contratos/{contrato_id}/depositos", response_model=list[DepositoSalida])
def depositos_de_contrato(contrato_id: int, db: Session = Depends(get_db)) -> list[DepositoSalida]:
    return [DepositoSalida.model_validate(d) for d in service.depositos_de_contrato(db, contrato_id)]


@router.post("/contratos/{contrato_id}/depositos", response_model=DepositoSalida, status_code=201)
def recibir_deposito(
    contrato_id: int,
    datos: DepositoEntrada,
    usuario: Usuario = Depends(CAPTURA),
    db: Session = Depends(get_db),
) -> DepositoSalida:
    return DepositoSalida.model_validate(service.recibir_deposito(db, contrato_id, datos, usuario.id))


@router.get("/depositos", response_model=DepositosVigentes)
def depositos_vigentes(db: Session = Depends(get_db)) -> DepositosVigentes:
    totales, mayor = service.saldo_depositos(db), service.saldo_depositos_en_mayor(db)
    return DepositosVigentes(
        depositos=[DepositoSalida.model_validate(d) for d in service.depositos_vigentes(db)],
        totales=totales,
        mayor=mayor,
        cuadra=totales == mayor,
    )


@router.post("/depositos/{deposito_id}/aplicacion", response_model=DepositoSalida)
def aplicar_deposito(
    deposito_id: int,
    datos: AplicacionEntrada,
    usuario: Usuario = Depends(CAPTURA),
    db: Session = Depends(get_db),
) -> DepositoSalida:
    return DepositoSalida.model_validate(service.aplicar_deposito(db, deposito_id, datos, usuario.id))


@router.post("/depositos/{deposito_id}/devolucion", response_model=DepositoSalida)
def devolver_deposito(
    deposito_id: int,
    datos: DevolucionDepositoEntrada,
    usuario: Usuario = Depends(CAPTURA),
    db: Session = Depends(get_db),
) -> DepositoSalida:
    return DepositoSalida.model_validate(service.devolver_deposito(db, deposito_id, datos, usuario.id))
