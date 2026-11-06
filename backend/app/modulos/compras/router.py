from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.compras import service
from app.modulos.compras.schemas import (
    FacturaCompraEntrada,
    FacturaCompraSalida,
    ProveedorEntrada,
    ProveedorSalida,
    RubroProveedor,
    TipoProveedor,
)

# Pendiente al mezclar HU-1.09/HU-1.10: exigir sesión y permisos por rol.
router = APIRouter(prefix="/compras", tags=["Compras"])


# ── HU-4.01: proveedores ───────────────────────────────────────────────────────


@router.get("/proveedores", response_model=list[ProveedorSalida])
def listar_proveedores(
    tipo: TipoProveedor | None = None,
    rubro: RubroProveedor | None = None,
    buscar: str | None = None,
    db: Session = Depends(get_db),
) -> list[ProveedorSalida]:
    return [ProveedorSalida.model_validate(p) for p in service.listar_proveedores(db, tipo, rubro, buscar)]


@router.post("/proveedores", response_model=ProveedorSalida, status_code=201)
def registrar_proveedor(datos: ProveedorEntrada, db: Session = Depends(get_db)) -> ProveedorSalida:
    return ProveedorSalida.model_validate(service.registrar_proveedor(db, datos))


@router.get("/proveedores/{proveedor_id}", response_model=ProveedorSalida)
def consultar_proveedor(proveedor_id: int, db: Session = Depends(get_db)) -> ProveedorSalida:
    return ProveedorSalida.model_validate(service.obtener_proveedor(db, proveedor_id))


# ── HU-4.09: facturas de compras y gastos locales ─────────────────────────────


@router.get("/facturas", response_model=list[FacturaCompraSalida])
def listar_facturas(
    proveedor_id: int | None = None, db: Session = Depends(get_db)
) -> list[FacturaCompraSalida]:
    return [FacturaCompraSalida.model_validate(f) for f in service.listar_facturas(db, proveedor_id)]


@router.post("/facturas", response_model=FacturaCompraSalida, status_code=201)
def registrar_factura(datos: FacturaCompraEntrada, db: Session = Depends(get_db)) -> FacturaCompraSalida:
    return FacturaCompraSalida.model_validate(service.registrar_factura(db, datos))


@router.get("/facturas/{factura_id}", response_model=FacturaCompraSalida)
def consultar_factura(factura_id: int, db: Session = Depends(get_db)) -> FacturaCompraSalida:
    return FacturaCompraSalida.model_validate(service.obtener_factura(db, factura_id))
