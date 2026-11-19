from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.compras import service
from app.modulos.compras.schemas import (
    ConceptoGastoSalida,
    FacturaCompraEntrada,
    FacturaCompraSalida,
    GastoImportacionEntrada,
    GastoImportacionSalida,
    ProveedorEntrada,
    ProveedorSalida,
    ResumenGastosUnidad,
    RubroProveedor,
    TipoProveedor,
)

# Pendiente (HU-1.09/HU-1.10): las rutas siguen abiertas porque el front aún no tiene login
# (tarea C1 del equipo C); exigir sesión hoy dejaría sin funcionar las pantallas de compras.
# Cuando exista el login del front, proteger con `app.modulos.seguridad.service`:
# - Consultas (GET): `_: Usuario = Depends(usuario_actual)`.
# - Altas de proveedores y facturas (POST): `_: Usuario = Depends(requiere_rol(CONTADOR))`.
# - Alta de gastos de importación (POST; en HU-4.04 la hace el auxiliar contable):
#   `_: Usuario = Depends(requiere_rol(AUXILIAR_CONTABLE, CONTADOR))`.
# Sin sesión, la bitácora (HU-1.11) guarda el cambio con el actor vacío.
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


# ── HU-4.04: gastos de importación ────────────────────────────────────────────


@router.get("/gastos-importacion/conceptos", response_model=list[ConceptoGastoSalida])
def listar_conceptos(db: Session = Depends(get_db)) -> list[ConceptoGastoSalida]:
    return [ConceptoGastoSalida.model_validate(c) for c in service.listar_conceptos(db)]


@router.get("/gastos-importacion/unidad/{vin}", response_model=ResumenGastosUnidad)
def resumen_gastos_unidad(vin: str, db: Session = Depends(get_db)) -> ResumenGastosUnidad:
    return ResumenGastosUnidad(**service.resumen_gastos_unidad(db, vin))


@router.get("/gastos-importacion", response_model=list[GastoImportacionSalida])
def listar_gastos_importacion(
    vin: str | None = None, proveedor_id: int | None = None, db: Session = Depends(get_db)
) -> list[GastoImportacionSalida]:
    gastos = service.listar_gastos_importacion(db, vin, proveedor_id)
    return [GastoImportacionSalida.model_validate(g) for g in gastos]


@router.post("/gastos-importacion", response_model=GastoImportacionSalida, status_code=201)
def registrar_gasto_importacion(
    datos: GastoImportacionEntrada, db: Session = Depends(get_db)
) -> GastoImportacionSalida:
    return GastoImportacionSalida.model_validate(service.registrar_gasto_importacion(db, datos))


@router.get("/gastos-importacion/{gasto_id}", response_model=GastoImportacionSalida)
def consultar_gasto_importacion(gasto_id: int, db: Session = Depends(get_db)) -> GastoImportacionSalida:
    return GastoImportacionSalida.model_validate(service.obtener_gasto_importacion(db, gasto_id))
