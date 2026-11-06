from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.compras import service
from app.modulos.compras.schemas import ProveedorEntrada, ProveedorSalida, RubroProveedor, TipoProveedor

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
