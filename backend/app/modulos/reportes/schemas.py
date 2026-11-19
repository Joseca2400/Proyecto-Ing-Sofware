from datetime import date, datetime
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


# ── HU-3.13: rentabilidad por unidad y por contrato ───────────────────────────


def _monto_o_pendiente(valor: Decimal | None) -> str | None:
    return None if valor is None else _monto_texto(valor)


class CifrasRentabilidad(BaseModel):
    """Montos en quetzales del mayor. None en un concepto = pendiente (su regla no tiene cuenta)."""

    ingreso_alquiler: Decimal | None
    depreciacion: Decimal | None
    mantenimiento: Decimal | None
    seguro: Decimal | None
    marchamo: Decimal | None
    costos: Decimal
    resultado: Decimal

    @field_serializer(
        "ingreso_alquiler", "depreciacion", "mantenimiento", "seguro", "marchamo", "costos", "resultado"
    )
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _monto_o_pendiente(valor)


class TotalesRentabilidadUnidad(BaseModel):
    ingreso_alquiler: Decimal | None
    depreciacion: Decimal | None
    mantenimiento: Decimal | None
    seguro: Decimal | None
    marchamo: Decimal | None
    costos: Decimal | None
    resultado: Decimal | None

    @field_serializer(
        "ingreso_alquiler", "depreciacion", "mantenimiento", "seguro", "marchamo", "costos", "resultado"
    )
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _monto_o_pendiente(valor)


class RentabilidadUnidad(CifrasRentabilidad):
    vin: str
    marca: str
    linea: str
    modelo: int
    estado: str
    fecha_alta: date


class ReporteRentabilidadUnidades(BaseModel):
    desde: date
    hasta: date
    unidades: list[RentabilidadUnidad]
    totales: TotalesRentabilidadUnidad
    pendientes: list[str]


class MontosRentabilidadContrato(BaseModel):
    alquiler: Decimal | None
    cargos_adicionales: Decimal | None
    ingresos: Decimal | None
    costos_directos: Decimal | None
    resultado: Decimal | None

    @field_serializer("alquiler", "cargos_adicionales", "ingresos", "costos_directos", "resultado")
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _monto_o_pendiente(valor)


class RentabilidadContrato(MontosRentabilidadContrato):
    contrato_id: int
    numero: int
    vin: str
    cliente: str
    salida: datetime
    devolucion: datetime | None
    estado: str
    facturas: list[str]


class ReporteRentabilidadContratos(BaseModel):
    desde: date
    hasta: date
    contratos: list[RentabilidadContrato]
    totales: MontosRentabilidadContrato
    pendientes: list[str]
