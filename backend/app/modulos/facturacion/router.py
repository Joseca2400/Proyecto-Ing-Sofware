from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.facturacion import service
from app.modulos.facturacion.schemas import ClienteEntrada, ClienteSalida, TipoCliente

# Pendiente (HU-1.09/HU-1.10): igual que compras, las rutas siguen abiertas hasta que el front
# tenga login (tarea C1). Entonces: consultas con `usuario_actual` y altas con el rol del
# auxiliar contable, desde `app.modulos.seguridad.service`.
router = APIRouter(prefix="/facturacion", tags=["Facturación"])


# ── HU-6.01: clientes ──────────────────────────────────────────────────────────


@router.get("/clientes", response_model=list[ClienteSalida])
def listar_clientes(
    tipo: TipoCliente | None = None,
    buscar: str | None = None,
    db: Session = Depends(get_db),
) -> list[ClienteSalida]:
    return [ClienteSalida.model_validate(c) for c in service.listar_clientes(db, tipo, buscar)]


@router.post("/clientes", response_model=ClienteSalida, status_code=201)
def registrar_cliente(datos: ClienteEntrada, db: Session = Depends(get_db)) -> ClienteSalida:
    return ClienteSalida.model_validate(service.registrar_cliente(db, datos))


@router.get("/clientes/{cliente_id}", response_model=ClienteSalida)
def consultar_cliente(cliente_id: int, db: Session = Depends(get_db)) -> ClienteSalida:
    return ClienteSalida.model_validate(service.obtener_cliente(db, cliente_id))
