from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _monto_texto(valor: Decimal) -> str:
    return f"{valor:.6f}"


class TarifaEntrada(BaseModel):
    """Tarifa horaria de costo en quetzales; viaja como texto y el service la valida."""

    tarifa_hora: str
    vigente_desde: date


class TarifaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarifa_hora: Decimal
    vigente_desde: date
    creado_en: datetime

    @field_serializer("tarifa_hora")
    def tarifa_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


# ── HU-5.01: órdenes de trabajo ───────────────────────────────────────────────

TipoOrden = Literal["reacondicionamiento"]  # los demás tipos llegan en los Sprints 5 y 6


class OrdenEntrada(BaseModel):
    """Apertura de la orden. El VIN y la coherencia con el estado de la unidad se validan en el service."""

    vin: str = Field(max_length=30)
    tipo: TipoOrden
    fecha_apertura: date
    kilometraje: int = Field(ge=0, le=2_000_000)
    descripcion: str = Field(min_length=1, max_length=500)
    responsable: str = Field(min_length=1, max_length=100)

    @field_validator("vin", mode="before")
    @classmethod
    def normalizar_vin(cls, valor: object) -> object:
        return valor.strip().upper() if isinstance(valor, str) else valor

    @field_validator("descripcion", "responsable", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class OrdenSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    vin: str
    tipo: TipoOrden
    estado: Literal["abierta", "cerrada"]
    fecha_apertura: date
    kilometraje: int
    descripcion: str
    responsable: str
    dias: int
    costo_acumulado: Decimal
    fecha_cierre: date | None
    justificacion: str | None
    partida_id: int | None

    @field_serializer("costo_acumulado")
    def costo_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)
