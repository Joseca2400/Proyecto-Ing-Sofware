from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    correo: Mapped[str] = mapped_column(String(200), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    rol: Mapped[str] = mapped_column(String(30))
    clave_hash: Mapped[str] = mapped_column(String(300))
    activo: Mapped[bool] = mapped_column(default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Sesion(Base):
    """Sesión en el servidor: solo se guarda el hash del token, y cerrar sesión la borra."""

    __tablename__ = "sesiones"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"), index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
