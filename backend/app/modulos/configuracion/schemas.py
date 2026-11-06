from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from app.modulos.configuracion import service

Tipo = Literal[*service.TIPOS]
Naturaleza = Literal[*service.NATURALEZAS]
ModoVin = Literal[*service.MODOS_VIN]
Linea = Literal[*service.LINEAS_NEGOCIO]


class DimensionesEntrada(BaseModel):
    linea_obligatoria: bool = False
    vin: ModoVin = "no_aplica"
    linea_defecto: Linea | None = None


class CuentaEntrada(DimensionesEntrada):
    codigo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    tipo: Tipo
    naturaleza: Naturaleza
    padre_id: int | None = None
    es_detalle: bool = True
    monetaria_usd: bool = False


class CuentaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    tipo: Tipo
    naturaleza: Naturaleza
    nivel: int
    padre_id: int | None
    es_detalle: bool
    monetaria_usd: bool
    linea_obligatoria: bool
    vin: ModoVin
    linea_defecto: Linea | None
