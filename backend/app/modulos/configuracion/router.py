from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service
from app.modulos.configuracion.schemas import (
    CuentaEntrada,
    CuentaSalida,
    DimensionesEntrada,
    PerfilFiscalEntrada,
    PerfilFiscalSalida,
    TipoCambioEntrada,
    TipoCambioSalida,
    TransaccionUSDEntrada,
    TransaccionUSDSalida,
)
from app.modulos.seguridad.service import (
    CONTADOR,
    GERENTE_FINANCIERO,
    Usuario,
    requiere_rol,
    usuario_actual,
)

router = APIRouter(prefix="/configuracion", tags=["Configuración"])


# ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────


@router.get("/lineas-negocio", response_model=list[str])
def lineas_negocio(_: Usuario = Depends(usuario_actual)) -> list[str]:
    return list(service.LINEAS_NEGOCIO)


@router.get("/cuentas", response_model=list[CuentaSalida])
def listar_cuentas(
    solo_detalle: bool = False, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
):
    return service.listar_cuentas(db, solo_detalle)


@router.post("/cuentas", response_model=CuentaSalida, status_code=201)
def crear_cuenta(
    datos: CuentaEntrada, _: Usuario = Depends(requiere_rol(CONTADOR)), db: Session = Depends(get_db)
):
    return service.crear_cuenta(db, **datos.model_dump())


@router.put("/cuentas/{cuenta_id}/dimensiones", response_model=CuentaSalida)
def definir_dimensiones(
    cuenta_id: int,
    datos: DimensionesEntrada,
    _: Usuario = Depends(requiere_rol(CONTADOR)),
    db: Session = Depends(get_db),
):
    return service.definir_dimensiones(db, cuenta_id, **datos.model_dump())


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────
CAMBIARIO = requiere_rol(CONTADOR, GERENTE_FINANCIERO)


@router.get("/tipos-cambio", response_model=list[TipoCambioSalida])
def listar_tipos_cambio(
    desde: date | None = None,
    hasta: date | None = None,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[TipoCambioSalida]:
    return [TipoCambioSalida.model_validate(t) for t in service.listar(db, desde, hasta)]


@router.post("/tipos-cambio", response_model=TipoCambioSalida, status_code=201)
def registrar_tipo_cambio(
    datos: TipoCambioEntrada, _: Usuario = Depends(CAMBIARIO), db: Session = Depends(get_db)
) -> TipoCambioSalida:
    return TipoCambioSalida.model_validate(service.registrar_manual(db, datos.fecha, datos.valor))


@router.get("/tipos-cambio/{fecha}", response_model=TipoCambioSalida)
def consultar_tipo_cambio(
    fecha: date, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
) -> TipoCambioSalida:
    tipo = service.buscar(db, fecha)
    if tipo is None:
        raise ErrorNegocio(f"No existe tipo de cambio para el {fecha:%d/%m/%Y}", status=404)
    return TipoCambioSalida.model_validate(tipo)


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────


@router.get("/transacciones-usd", response_model=list[TransaccionUSDSalida])
def listar_transacciones_usd(
    desde: date | None = None,
    hasta: date | None = None,
    _: Usuario = Depends(usuario_actual),
    db: Session = Depends(get_db),
) -> list[TransaccionUSDSalida]:
    return [
        TransaccionUSDSalida.model_validate(t) for t in service.listar_transacciones_usd(db, desde, hasta)
    ]


@router.post("/transacciones-usd", response_model=TransaccionUSDSalida, status_code=201)
def registrar_transaccion_usd(
    datos: TransaccionUSDEntrada, _: Usuario = Depends(CAMBIARIO), db: Session = Depends(get_db)
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


# ── HU-1.01: perfil fiscal de la empresa ──────────────────────────────────────


@router.get("/perfil-fiscal", response_model=PerfilFiscalSalida)
def perfil_fiscal_vigente(
    fecha: date | None = None, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
) -> PerfilFiscalSalida:
    perfil = service.perfil_fiscal_vigente(db, fecha)
    if perfil is None:
        raise ErrorNegocio("Todavía no hay un perfil fiscal registrado", status=404)
    return PerfilFiscalSalida.model_validate(perfil)


@router.get("/perfil-fiscal/historial", response_model=list[PerfilFiscalSalida])
def historial_perfil_fiscal(
    _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
) -> list[PerfilFiscalSalida]:
    return [PerfilFiscalSalida.model_validate(p) for p in service.historial_perfil_fiscal(db)]


@router.post("/perfil-fiscal", response_model=PerfilFiscalSalida, status_code=201)
def registrar_perfil_fiscal(
    datos: PerfilFiscalEntrada, _: Usuario = Depends(CAMBIARIO), db: Session = Depends(get_db)
) -> PerfilFiscalSalida:
    return PerfilFiscalSalida.model_validate(service.registrar_perfil_fiscal(db, **datos.model_dump()))
