from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.comun import config
from app.comun.db import get_db
from app.modulos.reportes import service
from app.modulos.reportes.schemas import ReporteUnidadesEtapa
from app.modulos.seguridad.service import (
    CONTADOR,
    GERENCIA,
    GERENTE_FINANCIERO,
    requiere_rol,
    usuario_actual,
)

LECTURA = requiere_rol(GERENCIA, GERENTE_FINANCIERO, CONTADOR)

router = APIRouter(
    prefix="/reportes", tags=["Reportes"], dependencies=[Depends(usuario_actual), Depends(LECTURA)]
)


@router.get("/unidades-por-etapa", response_model=ReporteUnidadesEtapa)
def unidades_por_etapa(
    limite_dias: int = Query(default=config.DIAS_LIMITE_ETAPA, ge=1, le=3650),
    db: Session = Depends(get_db),
) -> ReporteUnidadesEtapa:
    """HU-7.04: unidades y valor por estado, días promedio y las que superan el plazo."""
    return ReporteUnidadesEtapa(**service.unidades_por_etapa(db, limite_dias))
