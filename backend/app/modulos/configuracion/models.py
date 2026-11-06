from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.comun.db import Base


class Cuenta(Base):
    """Cuenta contable. Las de detalle reciben movimientos; las de agrupación suman a sus hijas."""

    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(30), unique=True)
    nombre: Mapped[str] = mapped_column(String(200))
    tipo: Mapped[str] = mapped_column(String(20))
    naturaleza: Mapped[str] = mapped_column(String(20))
    nivel: Mapped[int]
    padre_id: Mapped[int | None] = mapped_column(ForeignKey("cuentas.id"), index=True)
    es_detalle: Mapped[bool] = mapped_column(default=True)
    monetaria_usd: Mapped[bool] = mapped_column(default=False)
    # Dimensiones analíticas (HU-1.04): solo tienen sentido en cuentas de detalle.
    linea_obligatoria: Mapped[bool] = mapped_column(default=False)
    vin: Mapped[str] = mapped_column(String(20), default="no_aplica")
    linea_defecto: Mapped[str | None] = mapped_column(String(20))
