from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.sistema import service
from app.modulos.sistema.schemas import EstadoSistema

router = APIRouter(prefix="/sistema", tags=["Sistema"])


@router.get("/estado", response_model=EstadoSistema)
def estado(db: Session = Depends(get_db)) -> EstadoSistema:
    """Hola mundo de punta a punta: API, base de datos y revisión del esquema."""
    return service.estado_sistema(db)
