"""Ingreso: clientes y facturación (E6), contratos (E3) y reportes (E7)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import REGISTRAN, TODOS, requiere
from app.models import Cliente, Cobro, Contrato, Factura, Usuario
from app.schemas import (
    CerrarContratoIn,
    ClienteIn,
    ClienteOut,
    CobroIn,
    CobroOut,
    ContratoIn,
    ContratoOut,
    FacturaOut,
    FacturarIn,
)
from app.services import ingreso as svc
from app.services.base import obtener

router = APIRouter()


def contrato_out(c: Contrato, cierre: dict | None = None) -> ContratoOut:
    if cierre is None and c.estado == "CERRADO":
        cierre = svc.resumen_cierre(c)
    return ContratoOut(
        id=c.id, cliente_id=c.cliente_id, cliente=c.cliente.nombre, unidad_id=c.unidad_id, vin=c.unidad.vin,
        fecha_salida=c.fecha_salida, fecha_prevista=c.fecha_prevista, fecha_devolucion=c.fecha_devolucion,
        tarifa_diaria=c.tarifa_diaria, moneda=c.moneda, km_salida=c.km_salida, km_entrada=c.km_entrada,
        estado=c.estado, monto_estimado=svc.monto_estimado(c),
        dias=cierre["dias"] if cierre else None, km_recorridos=cierre["km_recorridos"] if cierre else None,
        monto=cierre["monto"] if cierre else None,
    )


# ======================================================================= Clientes (HU-6.01)

@router.post("/clientes", response_model=ClienteOut, status_code=201, tags=["E6 · Facturación"],
             summary="HU-6.01 Registrar cliente (NIT validado, sin duplicados)")
def crear_cliente(datos: ClienteIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    return svc.crear_cliente(db, datos, quien.usuario)


@router.get("/clientes", response_model=list[ClienteOut], tags=["E6 · Facturación"])
def listar_clientes(db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return list(db.scalars(select(Cliente).order_by(Cliente.nombre)))


# ======================================================================= Contratos (HU-3.06, HU-3.08)

@router.post("/contratos", response_model=ContratoOut, status_code=201, tags=["E3 · Alquileres"],
             summary="HU-3.06 Registrar contrato de alquiler (valida disponibilidad)")
def crear_contrato(datos: ContratoIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    return contrato_out(svc.registrar_contrato(db, datos, quien.usuario))


@router.get("/contratos", response_model=list[ContratoOut], tags=["E3 · Alquileres"])
def listar_contratos(estado: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    stmt = select(Contrato).order_by(Contrato.id.desc())
    if estado:
        stmt = stmt.where(Contrato.estado == estado)
    return [contrato_out(c) for c in db.scalars(stmt)]


@router.post("/contratos/{contrato_id}/cerrar", response_model=ContratoOut, tags=["E3 · Alquileres"],
             summary="HU-3.08 Cerrar contrato al devolver la unidad")
def cerrar_contrato(contrato_id: int, datos: CerrarContratoIn, db: Session = Depends(get_db),
                    quien: Usuario = Depends(requiere(*REGISTRAN))):
    r = svc.cerrar_contrato(db, contrato_id, datos, quien.usuario)
    return contrato_out(r["contrato"], r)


@router.post("/contratos/{contrato_id}/facturar", response_model=FacturaOut, status_code=201,
             tags=["E6 · Facturación"], summary="HU-6.02 Emitir factura FEL del contrato (certificación simulada)")
def facturar(contrato_id: int, datos: FacturarIn, db: Session = Depends(get_db),
             quien: Usuario = Depends(requiere(*REGISTRAN))):
    return svc.facturar_contrato(db, contrato_id, datos.fecha, datos.consumidor_final, quien.usuario)


# ======================================================================= Facturas y cobros (HU-6.07)

@router.get("/facturas", response_model=list[FacturaOut], tags=["E6 · Facturación"])
def listar_facturas(con_saldo: bool = False, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    stmt = select(Factura).order_by(Factura.id.desc())
    if con_saldo:
        stmt = stmt.where(Factura.saldo > 0)
    return list(db.scalars(stmt))


@router.post("/facturas/{factura_id}/cobros", response_model=CobroOut, status_code=201, tags=["E6 · Facturación"],
             summary="HU-6.07 Registrar cobro (calcula diferencial cambiario realizado, HU-2.09)")
def cobrar(factura_id: int, datos: CobroIn, db: Session = Depends(get_db),
           quien: Usuario = Depends(requiere(*REGISTRAN))):
    return svc.registrar_cobro(db, factura_id, datos, quien.usuario)


@router.get("/facturas/{factura_id}/cobros", response_model=list[CobroOut], tags=["E6 · Facturación"])
def cobros(factura_id: int, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    obtener(db, Factura, factura_id, "La factura")
    return list(db.scalars(select(Cobro).where(Cobro.factura_id == factura_id).order_by(Cobro.id)))


# ======================================================================= Reportes (E7, incluye rol gerencia)

@router.get("/reportes/unidades-por-etapa", tags=["E7 · Reportes"],
            summary="HU-7.04 Unidades y capital invertido por etapa del ciclo")
def por_etapa(db: Session = Depends(get_db), _=Depends(requiere(*TODOS))):
    return svc.unidades_por_etapa(db)


@router.get("/reportes/rentabilidad-unidades", tags=["E7 · Reportes"],
            summary="HU-7.02 Rentabilidad por unidad (versión del corte)")
def rentabilidad(estado: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*TODOS))):
    return svc.rentabilidad_unidades(db, estado)
