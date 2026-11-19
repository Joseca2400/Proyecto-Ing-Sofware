from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.facturacion import service
from app.modulos.facturacion.schemas import ClienteEntrada, ClienteSalida, FacturaEntrada, FacturaSalida
from app.modulos.seguridad.service import (
    AUXILIAR_CONTABLE,
    CONTADOR,
    Usuario,
    requiere_rol,
    usuario_actual,
)

# Todas las rutas exigen sesión; el alta de clientes y la emisión de facturas, además, su rol.
CAPTURA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)

router = APIRouter(prefix="/facturacion", tags=["Facturación"], dependencies=[Depends(usuario_actual)])


# ── HU-6.01: clientes ──────────────────────────────────────────────────────────


@router.get("/clientes", response_model=list[ClienteSalida])
def listar_clientes(buscar: str | None = None, db: Session = Depends(get_db)) -> list[ClienteSalida]:
    return [ClienteSalida.model_validate(c) for c in service.listar_clientes(db, buscar)]


@router.post("/clientes", response_model=ClienteSalida, status_code=201)
def registrar_cliente(
    datos: ClienteEntrada, _: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> ClienteSalida:
    return ClienteSalida.model_validate(service.registrar_cliente(db, datos))


@router.get("/clientes/{cliente_id}", response_model=ClienteSalida)
def consultar_cliente(cliente_id: int, db: Session = Depends(get_db)) -> ClienteSalida:
    return ClienteSalida.model_validate(service.obtener_cliente(db, cliente_id))


# ── HU-6.02: facturas FEL ──────────────────────────────────────────────────────


@router.get("/facturas", response_model=list[FacturaSalida])
def listar_facturas(db: Session = Depends(get_db)) -> list[FacturaSalida]:
    return [FacturaSalida.model_validate(f) for f in service.listar_facturas(db)]


@router.post("/facturas", response_model=FacturaSalida, status_code=201)
def emitir_factura(
    datos: FacturaEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
) -> FacturaSalida:
    """Certificada o rechazada por el certificador, la factura queda registrada: ver `estado`."""
    return FacturaSalida.model_validate(service.emitir_factura(db, datos, usuario.id))


@router.get("/facturas/{factura_id}", response_model=FacturaSalida)
def consultar_factura(factura_id: int, db: Session = Depends(get_db)) -> FacturaSalida:
    return FacturaSalida.model_validate(service.obtener_factura(db, factura_id))
