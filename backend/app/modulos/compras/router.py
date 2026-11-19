from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.compras import service
from app.modulos.compras.schemas import (
    AnulacionPagoEntrada,
    CompraUnidadEntrada,
    CompraUnidadSalida,
    ConceptoGastoSalida,
    CuentaPorPagarPendiente,
    DecisionPagoEntrada,
    FacturaCompraEntrada,
    FacturaCompraSalida,
    GastoImportacionEntrada,
    GastoImportacionSalida,
    HojaCosto,
    Moneda,
    PagoProgramadoSalida,
    PagoProveedorEntrada,
    PagoProveedorSalida,
    ProgramacionPagoEntrada,
    ProgramacionPagoSalida,
    ProveedorEntrada,
    ProveedorSalida,
    ResumenGastosUnidad,
    RubroProveedor,
    TipoProveedor,
)
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    GERENTE_FINANCIERO,
    Usuario,
    requiere_rol,
    usuario_actual,
)

# HU-1.09: todas las rutas exigen sesión; las altas, además, el rol que registra el documento.
CONTADOR_ = requiere_rol(CONTADOR)
CAPTURA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)
# HU-4.13: proponer pagos lo hace el área contable; aprobarlos, solo el gerente financiero, y nunca
# quien los propuso (lo revisa el service).
PROPONE = requiere_rol(AUXILIAR_CONTABLE, CONTADOR, GERENTE_FINANCIERO)
APRUEBA = requiere_rol(GERENTE_FINANCIERO)
# HU-4.14: el pago lo registra el área contable; anularlo, el contador o el gerente financiero.
ANULA = requiere_rol(CONTADOR, GERENTE_FINANCIERO)

router = APIRouter(prefix="/compras", tags=["Compras"], dependencies=[Depends(usuario_actual)])


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
def registrar_proveedor(
    datos: ProveedorEntrada, _: Usuario = Depends(CONTADOR_), db: Session = Depends(get_db)
) -> ProveedorSalida:
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
def registrar_factura(
    datos: FacturaCompraEntrada, usuario: Usuario = Depends(CONTADOR_), db: Session = Depends(get_db)
) -> FacturaCompraSalida:
    return FacturaCompraSalida.model_validate(service.registrar_factura(db, datos, usuario.id))


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
    datos: GastoImportacionEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> GastoImportacionSalida:
    return GastoImportacionSalida.model_validate(service.registrar_gasto_importacion(db, datos, usuario.id))


@router.get("/gastos-importacion/{gasto_id}", response_model=GastoImportacionSalida)
def consultar_gasto_importacion(gasto_id: int, db: Session = Depends(get_db)) -> GastoImportacionSalida:
    return GastoImportacionSalida.model_validate(service.obtener_gasto_importacion(db, gasto_id))


# ── HU-4.02: compra de la unidad en EE. UU. ───────────────────────────────────


@router.get("/compras-unidades", response_model=list[CompraUnidadSalida])
def listar_compras_unidad(
    vin: str | None = None, proveedor_id: int | None = None, db: Session = Depends(get_db)
) -> list[CompraUnidadSalida]:
    compras = service.listar_compras_unidad(db, vin, proveedor_id)
    return [CompraUnidadSalida.model_validate(c) for c in compras]


@router.post("/compras-unidades", response_model=CompraUnidadSalida, status_code=201)
def registrar_compra_unidad(
    datos: CompraUnidadEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> CompraUnidadSalida:
    return CompraUnidadSalida.model_validate(service.registrar_compra_unidad(db, datos, usuario.id))


@router.get("/compras-unidades/{compra_id}", response_model=CompraUnidadSalida)
def consultar_compra_unidad(compra_id: int, db: Session = Depends(get_db)) -> CompraUnidadSalida:
    return CompraUnidadSalida.model_validate(service.obtener_compra_unidad(db, compra_id))


# ── HU-4.08: hoja de costo de una unidad ──────────────────────────────────────


@router.get("/hoja-costo/{vin}", response_model=HojaCosto)
def hoja_de_costo(vin: str, db: Session = Depends(get_db)) -> HojaCosto:
    return HojaCosto(**service.hoja_de_costo(db, vin))


# ── HU-4.13: programación y aprobación de pagos ───────────────────────────────


@router.get("/cuentas-por-pagar", response_model=list[CuentaPorPagarPendiente])
def cuentas_por_pagar_pendientes(
    moneda: Moneda | None = None,
    vence_hasta: date | None = None,
    proveedor_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[CuentaPorPagarPendiente]:
    cuentas = service.cuentas_por_pagar_pendientes(db, moneda, vence_hasta, proveedor_id)
    return [CuentaPorPagarPendiente.model_validate(c) for c in cuentas]


def _programacion(db: Session, programacion) -> ProgramacionPagoSalida:
    return ProgramacionPagoSalida.model_validate(service.detalle_programacion(db, programacion))


@router.get("/programaciones-pago", response_model=list[ProgramacionPagoSalida])
def listar_programaciones(db: Session = Depends(get_db)) -> list[ProgramacionPagoSalida]:
    return [_programacion(db, p) for p in service.listar_programaciones(db)]


@router.post("/programaciones-pago", response_model=ProgramacionPagoSalida, status_code=201)
def proponer_pagos(
    datos: ProgramacionPagoEntrada, usuario: Usuario = Depends(PROPONE), db: Session = Depends(get_db)
) -> ProgramacionPagoSalida:
    return _programacion(db, service.proponer_pagos(db, datos, usuario.id))


@router.get("/programaciones-pago/{programacion_id}", response_model=ProgramacionPagoSalida)
def consultar_programacion(programacion_id: int, db: Session = Depends(get_db)) -> ProgramacionPagoSalida:
    return _programacion(db, service.obtener_programacion(db, programacion_id))


@router.post(
    "/programaciones-pago/{programacion_id}/pagos/{pago_id}/decision", response_model=ProgramacionPagoSalida
)
def decidir_pago(
    programacion_id: int,
    pago_id: int,
    datos: DecisionPagoEntrada,
    usuario: Usuario = Depends(APRUEBA),
    db: Session = Depends(get_db),
) -> ProgramacionPagoSalida:
    return _programacion(db, service.decidir_pago(db, programacion_id, pago_id, datos, usuario.id))


# ── HU-4.14: pago a un proveedor ──────────────────────────────────────────────


@router.get("/pagos-por-ejecutar", response_model=list[PagoProgramadoSalida])
def pagos_por_ejecutar(db: Session = Depends(get_db)) -> list[PagoProgramadoSalida]:
    return [PagoProgramadoSalida.model_validate(p) for p in service.pagos_por_ejecutar(db)]


def _pago(db: Session, pago) -> PagoProveedorSalida:
    return PagoProveedorSalida.model_validate(service.detalle_pago(db, pago))


@router.get("/pagos", response_model=list[PagoProveedorSalida])
def listar_pagos(proveedor_id: int | None = None, db: Session = Depends(get_db)) -> list[PagoProveedorSalida]:
    return [_pago(db, p) for p in service.listar_pagos(db, proveedor_id)]


@router.post("/pagos", response_model=PagoProveedorSalida, status_code=201)
def registrar_pago(
    datos: PagoProveedorEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> PagoProveedorSalida:
    return _pago(db, service.registrar_pago(db, datos, usuario.id))


@router.get("/pagos/{pago_id}", response_model=PagoProveedorSalida)
def consultar_pago(pago_id: int, db: Session = Depends(get_db)) -> PagoProveedorSalida:
    return _pago(db, service.obtener_pago(db, pago_id))


@router.post("/pagos/{pago_id}/anulacion", response_model=PagoProveedorSalida)
def anular_pago(
    pago_id: int,
    datos: AnulacionPagoEntrada,
    usuario: Usuario = Depends(ANULA),
    db: Session = Depends(get_db),
) -> PagoProveedorSalida:
    return _pago(db, service.anular_pago(db, pago_id, datos, usuario.id))
