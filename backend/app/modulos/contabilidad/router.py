from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.comun.db import get_db
from app.modulos.contabilidad import service
from app.modulos.contabilidad.schemas import DevolucionEntrada, PartidaEntrada, PartidaSalida
from app.modulos.seguridad.service import AUXILIAR_CONTABLE, CONTADOR, Usuario, requiere_rol, usuario_actual

router = APIRouter(prefix="/contabilidad", tags=["Contabilidad"])

# La separación entre quien registra y quien contabiliza llega con HU-1.10.
CAPTURA = requiere_rol(AUXILIAR_CONTABLE, CONTADOR)
REVISION = requiere_rol(CONTADOR)


@router.get("/partidas", response_model=list[PartidaSalida])
def listar_partidas(
    estado: str | None = None, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)
):
    return service.listar_partidas(db, estado)


@router.post("/partidas", response_model=PartidaSalida, status_code=201)
def crear_partida(datos: PartidaEntrada, usuario: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)):
    return service.crear_borrador(db, datos, usuario.id)


@router.get("/partidas/{partida_id}", response_model=PartidaSalida)
def consultar_partida(partida_id: int, _: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    return service.obtener_partida(db, partida_id)


@router.put("/partidas/{partida_id}", response_model=PartidaSalida)
def corregir_partida(
    partida_id: int, datos: PartidaEntrada, _: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)
):
    return service.corregir(db, partida_id, datos)


@router.post("/partidas/{partida_id}/enviar-a-revision", response_model=PartidaSalida)
def enviar_a_revision(partida_id: int, _: Usuario = Depends(CAPTURA), db: Session = Depends(get_db)):
    return service.enviar_a_revision(db, partida_id)


@router.post("/partidas/{partida_id}/contabilizar", response_model=PartidaSalida)
def contabilizar(partida_id: int, usuario: Usuario = Depends(REVISION), db: Session = Depends(get_db)):
    return service.contabilizar(db, partida_id, usuario.id)


@router.post("/partidas/{partida_id}/devolver", response_model=PartidaSalida)
def devolver(
    partida_id: int, datos: DevolucionEntrada, _: Usuario = Depends(REVISION), db: Session = Depends(get_db)
):
    return service.devolver(db, partida_id, datos.comentario)
