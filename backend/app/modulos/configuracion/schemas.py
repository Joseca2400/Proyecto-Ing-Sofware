from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


class TipoCambioEntrada(BaseModel):
    """Carga manual. El valor llega como texto ("7.75123456") para no pasar por float."""

    fecha: date
    valor: str

    @field_validator("valor", mode="before")
    @classmethod
    def valor_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('El tipo de cambio se envía como texto, por ejemplo "7.75"')
        return valor


class TipoCambioSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    valor: Decimal
    origen: str

    @field_serializer("valor")
    def valor_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.8f}"
