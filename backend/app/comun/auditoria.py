"""HU-1.11: consulta de la bitácora; PostgreSQL registra los cambios automáticamente."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.comun.db import Base


class RegistroBitacora(Base):
    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(index=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    entidad: Mapped[str] = mapped_column(String(100), index=True)
    registro_id: Mapped[str] = mapped_column(String(100))
    accion: Mapped[str] = mapped_column(String(20))
    vin: Mapped[str | None] = mapped_column(String(17), index=True)
    anteriores: Mapped[dict | None] = mapped_column(JSONB)
    nuevos: Mapped[dict | None] = mapped_column(JSONB)


def consultar_bitacora(
    db: Session,
    usuario_id: int | None = None,
    entidad: str | None = None,
    vin: str | None = None,
    limite: int = 100,
    desplazamiento: int = 0,
) -> list[RegistroBitacora]:
    consulta = select(RegistroBitacora)
    if usuario_id is not None:
        consulta = consulta.where(RegistroBitacora.usuario_id == usuario_id)
    if entidad is not None:
        consulta = consulta.where(RegistroBitacora.entidad == entidad)
    if vin is not None:
        consulta = consulta.where(RegistroBitacora.vin == vin.strip().upper())
    return list(
        db.scalars(consulta.order_by(RegistroBitacora.id.desc()).limit(limite).offset(desplazamiento))
    )
