from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.comun import config
from app.comun.db import get_db
from app.modulos.reportes import service
from app.modulos.reportes.schemas import (
    ReporteRentabilidadCiclo,
    ReporteRentabilidadContratos,
    ReporteRentabilidadUnidades,
    ReporteUnidadesEtapa,
)
from app.modulos.seguridad.service import (
    CONTADOR,
    GERENCIA,
    GERENTE_FINANCIERO,
    requiere_rol,
    usuario_actual,
)

LECTURA = requiere_rol(GERENCIA, GERENTE_FINANCIERO, CONTADOR)
CSV = {200: {"content": {"text/csv": {"schema": {"type": "string"}}}, "description": "Archivo CSV"}}

router = APIRouter(
    prefix="/reportes", tags=["Reportes"], dependencies=[Depends(usuario_actual), Depends(LECTURA)]
)


def _archivo_csv(contenido: str, nombre: str) -> Response:
    return Response(
        content=contenido.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.get("/unidades-por-etapa", response_model=ReporteUnidadesEtapa)
def unidades_por_etapa(
    limite_dias: int = Query(default=config.DIAS_LIMITE_ETAPA, ge=1, le=3650),
    db: Session = Depends(get_db),
) -> ReporteUnidadesEtapa:
    """HU-7.04: unidades y valor por estado, días promedio y las que superan el plazo."""
    return ReporteUnidadesEtapa(**service.unidades_por_etapa(db, limite_dias))


@router.get("/rentabilidad/unidades", response_model=ReporteRentabilidadUnidades)
def rentabilidad_unidades(
    desde: date | None = None,
    hasta: date | None = None,
    vin: str | None = None,
    db: Session = Depends(get_db),
) -> ReporteRentabilidadUnidades:
    """HU-3.13: ingreso, depreciación, mantenimiento, seguro, marchamo y resultado de cada unidad
    de la flota en el período (por defecto, del 1 de enero a hoy), del mayor filtrado por VIN."""
    return ReporteRentabilidadUnidades(**service.rentabilidad_unidades(db, desde, hasta, vin))


@router.get("/rentabilidad/unidades/csv", response_class=Response, responses=CSV)
def rentabilidad_unidades_csv(
    desde: date | None = None,
    hasta: date | None = None,
    vin: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    """HU-3.13: la misma consulta por unidad, en CSV."""
    reporte = service.rentabilidad_unidades(db, desde, hasta, vin)
    nombre = f"rentabilidad-unidades-{reporte['desde']}-{reporte['hasta']}.csv"
    return _archivo_csv(service.csv_rentabilidad_unidades(reporte), nombre)


@router.get("/rentabilidad/contratos", response_model=ReporteRentabilidadContratos)
def rentabilidad_contratos(
    desde: date | None = None,
    hasta: date | None = None,
    vin: str | None = None,
    db: Session = Depends(get_db),
) -> ReporteRentabilidadContratos:
    """HU-3.13: alquiler, cargos adicionales, costos directos y resultado de cada contrato con
    salida en el período, de las partidas de sus facturas."""
    return ReporteRentabilidadContratos(**service.rentabilidad_contratos(db, desde, hasta, vin))


@router.get("/rentabilidad/contratos/csv", response_class=Response, responses=CSV)
def rentabilidad_contratos_csv(
    desde: date | None = None,
    hasta: date | None = None,
    vin: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    """HU-3.13: la misma consulta por contrato, en CSV."""
    reporte = service.rentabilidad_contratos(db, desde, hasta, vin)
    nombre = f"rentabilidad-contratos-{reporte['desde']}-{reporte['hasta']}.csv"
    return _archivo_csv(service.csv_rentabilidad_contratos(reporte), nombre)


@router.get("/rentabilidad/ciclo", response_model=ReporteRentabilidadCiclo)
def rentabilidad_ciclo(
    estado: str | None = None,
    marca: str | None = None,
    linea: str | None = None,
    anio_compra: int | None = Query(default=None, ge=1900, le=2100),
    proveedor_id: int | None = None,
    orden: Literal["resultado", "rentabilidad"] = "resultado",
    db: Session = Depends(get_db),
) -> ReporteRentabilidadCiclo:
    """HU-7.02 (hasta la flota): por VIN, costo de compra, importación y reacondicionamiento,
    ingreso de alquiler, costos de flota, depreciación, resultado acumulado, rentabilidad sobre el
    costo, días en flota y ocupación; con filtros y orden."""
    return ReporteRentabilidadCiclo(
        **service.rentabilidad_ciclo(db, estado, marca, linea, anio_compra, proveedor_id, orden)
    )
