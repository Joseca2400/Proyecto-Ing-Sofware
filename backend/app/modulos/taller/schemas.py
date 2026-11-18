from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_serializer


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
