from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Estado = Literal[
    "en_transito", "en_aduana", "en_taller", "lista", "en_flota", "en_venta", "vendida", "recuperada"
]  # fmt: skip


def _recortar(valor: object) -> object:
    return valor.strip() if isinstance(valor, str) else valor


class UnidadEntrada(BaseModel):
    """Alta de una unidad. El VIN (forma y dígito verificador), el año, el tipo de vehículo y la
    línea de negocio se validan en el service."""

    vin: str = Field(max_length=30)
    marca: str = Field(max_length=50)
    linea: str = Field(max_length=50)
    modelo: int
    color: str = Field(max_length=30)
    tipo_vehiculo: str = Field(max_length=20)
    linea_negocio: str | None = Field(default=None, max_length=20)
    estado: Estado = "en_transito"
    documento: str | None = Field(default=None, max_length=200)

    @field_validator("marca", "linea", "color", "tipo_vehiculo", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return _recortar(valor)

    @field_validator("linea_negocio", "documento", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        """Un texto vacío cuenta como no enviado."""
        valor = _recortar(valor)
        return valor or None

    @field_validator("vin", mode="before")
    @classmethod
    def normalizar_vin(cls, valor: object) -> object:
        return valor.strip().upper() if isinstance(valor, str) else valor


class CambioEstadoEntrada(BaseModel):
    estado: Estado
    documento: str = Field(max_length=200)

    @field_validator("documento", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return _recortar(valor)


class UnidadSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    marca: str
    linea: str
    modelo: int
    color: str
    tipo_vehiculo: str
    linea_negocio: str | None
    estado: Estado
    creado_en: datetime


class CambioEstadoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado_anterior: Estado | None
    estado_nuevo: Estado
    documento: str
    usuario_id: int | None
    fecha: datetime


class Catalogos(BaseModel):
    """Listas que la pantalla necesita; las líneas de negocio vienen de `configuracion`."""

    estados: list[str]
    tipos_vehiculo: list[str]
    lineas_negocio: list[str]
