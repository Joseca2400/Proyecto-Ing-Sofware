"""Costo de la unidad: unidades (E1), importación (E4), taller (E5) y alta en flota (E3)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import REGISTRAN, REVISAN, requiere
from app.models import DocumentoPorPagar, OrdenTrabajo, Proveedor, Usuario
from app.schemas import (
    AltaFlotaIn,
    CerrarOrdenIn,
    CompraIn,
    CompraOut,
    DocumentoOut,
    EstadoIn,
    GastoIn,
    GastoOut,
    ManoObraIn,
    ManoObraOut,
    OrdenIn,
    OrdenOut,
    ProveedorIn,
    ProveedorOut,
    UnidadOut,
)
from app.services import ciclo as svc
from app.services.base import obtener

router = APIRouter()


def orden_out(o: OrdenTrabajo) -> OrdenOut:
    return OrdenOut(
        id=o.id, unidad_id=o.unidad_id, vin=o.unidad.vin, tipo=o.tipo, descripcion=o.descripcion,
        responsable=o.responsable, fecha_apertura=o.fecha_apertura, fecha_cierre=o.fecha_cierre,
        estado=o.estado, costo_total=svc.costo_orden(o), partida_id=o.partida_id,
        mano_obra=[ManoObraOut.model_validate(m) for m in o.mano_obra],
    )


# ======================================================================= Unidades

@router.get("/unidades", response_model=list[UnidadOut], tags=["E1 · Unidades"])
def listar_unidades(estado: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return svc.listar_unidades(db, estado)


@router.get("/unidades/vin/{vin}", response_model=UnidadOut, tags=["E1 · Unidades"],
            summary="HU-1.05 Ficha de la unidad con su historial de estados")
def unidad_por_vin(vin: str, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return svc.unidad_por_vin(db, vin)


@router.get("/unidades/{unidad_id}", response_model=UnidadOut, tags=["E1 · Unidades"])
def obtener_unidad(unidad_id: int, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return svc.obtener_unidad(db, unidad_id)


@router.post("/unidades/{unidad_id}/estado", response_model=UnidadOut, tags=["E4 · Importación"],
             summary="HU-4.07 Avanzar etapa: en tránsito → en aduana, en taller → lista")
def avanzar(unidad_id: int, datos: EstadoIn, db: Session = Depends(get_db),
            quien: Usuario = Depends(requiere(*REGISTRAN))):
    return svc.avanzar_importacion(db, unidad_id, datos.estado, datos.documento, quien.usuario)


@router.get("/unidades/{unidad_id}/hoja-costo", tags=["E4 · Importación"],
            summary="HU-4.08 Hoja de costo desglosada (cuadra con el mayor)")
def hoja_costo(unidad_id: int, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return svc.hoja_costo(db, unidad_id)


@router.post("/unidades/{unidad_id}/alta-flota", response_model=UnidadOut, tags=["E3 · Flota"],
             summary="HU-3.01 Dar de alta en la flota (contador o gerente financiero)")
def alta_flota(unidad_id: int, datos: AltaFlotaIn, db: Session = Depends(get_db),
               quien: Usuario = Depends(requiere(*REVISAN))):
    return svc.dar_alta_flota(db, unidad_id, datos.fecha, datos.vida_util_meses, datos.valor_residual,
                              quien.usuario)["unidad"]


# ======================================================================= Proveedores y compras

@router.get("/proveedores", response_model=list[ProveedorOut], tags=["E4 · Importación"])
def listar_proveedores(db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return list(db.scalars(select(Proveedor).order_by(Proveedor.nombre)))


@router.post("/proveedores", response_model=ProveedorOut, status_code=201, tags=["E4 · Importación"],
             summary="HU-4.01 Registrar proveedor local o del exterior")
def crear_proveedor(datos: ProveedorIn, db: Session = Depends(get_db),
                    quien: Usuario = Depends(requiere(*REGISTRAN))):
    return svc.crear_proveedor(db, datos, quien.usuario)


@router.post("/compras", response_model=CompraOut, status_code=201, tags=["E4 · Importación"],
             summary="HU-4.02 Comprar una unidad en EE. UU. (crea la unidad, la CxP y la partida)")
def comprar(datos: CompraIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    r = svc.registrar_compra(db, datos, quien.usuario)
    return CompraOut(unidad=UnidadOut.model_validate(r["unidad"]),
                     documento=DocumentoOut.model_validate(r["documento"]), partida_numero=r["partida"].numero)


@router.post("/gastos-importacion", response_model=GastoOut, status_code=201, tags=["E4 · Importación"],
             summary="HU-4.04 Registrar gasto de importación de una unidad")
def gasto(datos: GastoIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    r = svc.registrar_gasto_importacion(db, datos, quien.usuario)
    return GastoOut(id=r["gasto"].id, concepto=r["gasto"].concepto,
                    documento=DocumentoOut.model_validate(r["documento"]),
                    partida_numero=r["partida"].numero, capitalizable=r["capitalizable"])


@router.get("/cuentas-por-pagar", response_model=list[DocumentoOut], tags=["E4 · Importación"])
def cxp(db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return list(db.scalars(select(DocumentoPorPagar).where(DocumentoPorPagar.saldo > 0).order_by(DocumentoPorPagar.fecha)))


# ======================================================================= Taller

@router.post("/ordenes", response_model=OrdenOut, status_code=201, tags=["E5 · Taller"],
             summary="HU-5.01 Abrir orden de trabajo ligada a un VIN")
def abrir_orden(datos: OrdenIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    return orden_out(svc.abrir_orden(db, datos, quien.usuario))


@router.get("/ordenes", response_model=list[OrdenOut], tags=["E5 · Taller"])
def listar_ordenes(estado: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    stmt = select(OrdenTrabajo).order_by(OrdenTrabajo.id.desc())
    if estado:
        stmt = stmt.where(OrdenTrabajo.estado == estado)
    return [orden_out(o) for o in db.scalars(stmt)]


@router.get("/ordenes/{orden_id}", response_model=OrdenOut, tags=["E5 · Taller"])
def obtener_orden(orden_id: int, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return orden_out(obtener(db, OrdenTrabajo, orden_id, "La orden"))


@router.post("/ordenes/{orden_id}/mano-obra", response_model=OrdenOut, tags=["E5 · Taller"],
             summary="HU-5.03 Registrar horas (costeadas con la tarifa interna, HU-5.02)")
def mano_obra(orden_id: int, datos: ManoObraIn, db: Session = Depends(get_db),
              quien: Usuario = Depends(requiere(*REGISTRAN))):
    return orden_out(svc.registrar_mano_obra(db, orden_id, datos, quien.usuario))


@router.post("/ordenes/{orden_id}/cerrar", response_model=OrdenOut, tags=["E5 · Taller"],
             summary="HU-5.07 Cerrar la orden y generar su destino contable (contador)")
def cerrar_orden(orden_id: int, datos: CerrarOrdenIn, db: Session = Depends(get_db),
                 quien: Usuario = Depends(requiere(*REVISAN))):
    return orden_out(svc.cerrar_orden(db, orden_id, datos.fecha, datos.justificacion, quien.usuario)["orden"])
