from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service
from app.modulos.configuracion.schemas import (
    TipoCambioEntrada,
    TipoCambioSalida,
    TransaccionUSDEntrada,
    TransaccionUSDSalida,
)

# Pendiente al mezclar HU-1.09/HU-1.10: exigir sesión y permisos por rol.
router = APIRouter(prefix="/configuracion", tags=["Configuración"])


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────


@router.get("/tipos-cambio", response_model=list[TipoCambioSalida])
def listar_tipos_cambio(
    desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db)
) -> list[TipoCambioSalida]:
    return [TipoCambioSalida.model_validate(t) for t in service.listar(db, desde, hasta)]


@router.post("/tipos-cambio", response_model=TipoCambioSalida, status_code=201)
def registrar_tipo_cambio(datos: TipoCambioEntrada, db: Session = Depends(get_db)) -> TipoCambioSalida:
    return TipoCambioSalida.model_validate(service.registrar_manual(db, datos.fecha, datos.valor))


@router.get("/tipos-cambio/{fecha}", response_model=TipoCambioSalida)
def consultar_tipo_cambio(fecha: date, db: Session = Depends(get_db)) -> TipoCambioSalida:
    tipo = service.buscar(db, fecha)
    if tipo is None:
        raise ErrorNegocio(f"No existe tipo de cambio para el {fecha:%d/%m/%Y}", status=404)
    return TipoCambioSalida.model_validate(tipo)


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────


@router.get("/transacciones-usd", response_model=list[TransaccionUSDSalida])
def listar_transacciones_usd(
    desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db)
) -> list[TransaccionUSDSalida]:
    return [
        TransaccionUSDSalida.model_validate(t) for t in service.listar_transacciones_usd(db, desde, hasta)
    ]


@router.post("/transacciones-usd", response_model=TransaccionUSDSalida, status_code=201)
def registrar_transaccion_usd(
    datos: TransaccionUSDEntrada, db: Session = Depends(get_db)
) -> TransaccionUSDSalida:
    return TransaccionUSDSalida.model_validate(
        service.registrar_transaccion_usd(
            db,
            datos.fecha,
            datos.monto_usd,
            datos.tipo_cambio_personalizado,
            datos.justificacion,
        )
    )
