from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

Modalidad = Literal["diaria", "semanal", "mensual", "por_kilometraje"]
Moneda = Literal["GTQ", "USD"]


class TarifaEntrada(BaseModel):
    """Alta de una tarifa. Los montos llegan como texto; que se indique tipo de vehículo o VIN (uno
    solo), la existencia del VIN y la vigencia se validan en el service."""

    tipo_vehiculo: str | None = Field(default=None, max_length=20)
    vin: str | None = Field(default=None, max_length=17)
    modalidad: Modalidad
    moneda: Moneda
    monto: str
    km_incluido: int = Field(default=0, ge=0, le=1_000_000)
    precio_km_adicional: str = "0"
    vigente_desde: date
    vigente_hasta: date | None = None

    @field_validator("tipo_vehiculo", "vin", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        return (valor.strip() or None) if isinstance(valor, str) else valor

    @field_validator("monto", "precio_km_adicional", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('Los montos se envían como texto, por ejemplo "350.00"')
        return valor.strip()


class TarifaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_vehiculo: str | None
    vin: str | None
    modalidad: Modalidad
    moneda: Moneda
    monto: Decimal
    km_incluido: int
    precio_km_adicional: Decimal
    vigente_desde: date
    vigente_hasta: date | None
    creado_en: datetime

    @field_serializer("monto", "precio_km_adicional")
    def monto_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.6f}"


class CatalogosTarifas(BaseModel):
    modalidades: list[Modalidad]
    monedas: list[Moneda]
    tipos_vehiculo: list[str]
