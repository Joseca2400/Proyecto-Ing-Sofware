from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_serializer


def _monto_texto(valor: Decimal) -> str:
    return f"{valor:.6f}"


class UnidadReporteEtapa(BaseModel):
    """`valor_en_libros` dice si el valor es el en libros (con alta en flota) o el costo acumulado."""

    vin: str
    marca: str
    linea: str
    modelo: int
    estado: str
    desde: datetime
    dias_en_estado: int
    valor: Decimal
    valor_en_libros: bool
    excede: bool

    @field_serializer("valor")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class EstadoReporteEtapa(BaseModel):
    estado: str
    unidades: int
    valor: Decimal
    dias_promedio: int
    excedidas: int

    @field_serializer("valor")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class ReporteUnidadesEtapa(BaseModel):
    limite_dias: int
    valor_total: Decimal
    estados: list[EstadoReporteEtapa]
    unidades: list[UnidadReporteEtapa]

    @field_serializer("valor_total")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)
