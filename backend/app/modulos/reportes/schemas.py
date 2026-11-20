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


# ── HU-7.02: rentabilidad de cada unidad en su ciclo (hasta la flota) ─────────

_MONTOS_CICLO = (
    "compra", "importacion", "reacondicionamiento", "costo_total", "ingreso_alquiler", "mantenimiento",
    "seguro", "marchamo", "depreciacion", "resultado",
)  # fmt: skip


class MontosCiclo(BaseModel):
    """Montos en quetzales; None = concepto pendiente. La rentabilidad es un porcentaje (texto)."""

    compra: Decimal | None
    importacion: Decimal | None
    reacondicionamiento: Decimal | None
    costo_total: Decimal | None
    ingreso_alquiler: Decimal | None
    mantenimiento: Decimal | None
    seguro: Decimal | None
    marchamo: Decimal | None
    depreciacion: Decimal | None
    resultado: Decimal | None
    rentabilidad: Decimal | None

    @field_serializer(*_MONTOS_CICLO)
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _monto_o_pendiente(valor)

    @field_serializer("rentabilidad")
    def porcentaje_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.2f}"


class RentabilidadCiclo(MontosCiclo):
    vin: str
    marca: str
    linea: str
    modelo: int
    estado: str
    proveedor: str | None
    fecha_compra: date | None
    fecha_alta: date | None
    dias_en_flota: int | None
    dias_alquilados: int
    ocupacion: Decimal | None

    @field_serializer("ocupacion")
    def ocupacion_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.2f}"


class ProveedorFiltro(BaseModel):
    id: int
    nombre: str


class FiltrosCiclo(BaseModel):
    marcas: list[str]
    lineas: list[str]
    anios_compra: list[int]
    proveedores: list[ProveedorFiltro]


class ReporteRentabilidadCiclo(BaseModel):
    orden: str
    unidades: list[RentabilidadCiclo]
    totales: MontosCiclo
    filtros: FiltrosCiclo
    pendientes: list[str]
