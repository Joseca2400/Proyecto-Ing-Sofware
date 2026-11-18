from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

Estado = Literal[
    "en_transito", "en_aduana", "en_taller", "lista", "en_flota", "alquilada", "en_venta", "vendida",
    "recuperada",
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
    kilometraje: int | None = None
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


# ── HU-4.07: etapas de importación ────────────────────────────────────────────

Etapa = Literal["en_transito", "en_aduana", "en_taller", "lista"]


def _monto_texto(valor: Decimal) -> str:
    return f"{valor:.6f}"


class UnidadEnEtapa(BaseModel):
    """Una unidad del listado por etapa. Los días y el costo los calcula el servidor; el costo
    viaja como texto y el front solo le da formato."""

    vin: str
    marca: str
    linea: str
    modelo: int
    color: str
    estado: Etapa
    desde: datetime
    dias_en_etapa: int
    costo_total_gtq: Decimal
    siguiente_etapa: Etapa | None

    @field_serializer("costo_total_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class ResumenEtapa(BaseModel):
    estado: Etapa
    unidades: int
    costo_total_gtq: Decimal

    @field_serializer("costo_total_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class EtapasImportacion(BaseModel):
    """Totales por etapa, en orden (tránsito, aduana, taller, lista), y las unidades de cada una
    de la que lleva más días a la que lleva menos."""

    etapas: list[ResumenEtapa]
    unidades: list[UnidadEnEtapa]


# ── HU-3.01: alta en flota ────────────────────────────────────────────────────


class CandidataAltaFlota(BaseModel):
    """Unidad lista con el costo de su hoja de costo y si se puede dar de alta (cuadra, sin orden)."""

    vin: str
    marca: str
    linea: str
    modelo: int
    tipo_vehiculo: str
    costo: Decimal
    cuadra: bool
    diferencia: Decimal
    orden_abierta: bool
    # Parámetros de depreciación que se proponen (HU-3.02), los del tipo de vehículo.
    vida_util_meses: int
    valor_residual: Decimal
    porcentaje_fiscal: Decimal

    @field_serializer("costo", "diferencia", "valor_residual")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("porcentaje_fiscal")
    def porcentaje_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"


class AltaFlotaEntrada(BaseModel):
    """Fecha del alta y, opcionalmente, los parámetros de depreciación si el contador cambia los
    propuestos (montos y porcentajes como texto)."""

    fecha: date
    vida_util_meses: int | None = None
    valor_residual: str | None = Field(default=None, max_length=30)
    porcentaje_fiscal: str | None = Field(default=None, max_length=10)


class AltaFlotaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    fecha: date
    costo: Decimal
    partida_id: int
    usuario_id: int | None
    creado_en: datetime

    @field_serializer("costo")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


# ── HU-3.02: depreciación ─────────────────────────────────────────────────────


class DepreciacionTipoEntrada(BaseModel):
    vida_util_meses: int
    porcentaje_residual: str = Field(max_length=10)
    porcentaje_fiscal: str = Field(max_length=10)


class DepreciacionTipoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tipo_vehiculo: str
    vida_util_meses: int
    porcentaje_residual: Decimal
    porcentaje_fiscal: Decimal

    @field_serializer("porcentaje_residual", "porcentaje_fiscal")
    def porcentaje_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"


class ParametroDepreciacionEntrada(BaseModel):
    vigente_desde: date
    vida_util_meses: int
    valor_residual: str = Field(max_length=30)
    porcentaje_fiscal: str = Field(max_length=10)


class ParametroDepreciacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    vigente_desde: date
    vida_util_meses: int
    valor_residual: Decimal
    porcentaje_fiscal: Decimal
    usuario_id: int | None
    creado_en: datetime

    @field_serializer("valor_residual")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("porcentaje_fiscal")
    def porcentaje_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"


class ValorEnLibros(BaseModel):
    """Depreciación acumulada y valor en libros a una fecha, financieros y fiscales (línea recta)."""

    vin: str
    fecha: date
    fecha_alta: date
    costo: Decimal
    meses_depreciados: int
    vida_util_meses: int
    valor_residual: Decimal
    porcentaje_fiscal: Decimal
    depreciacion_financiera: Decimal
    valor_libros_financiero: Decimal
    depreciacion_fiscal: Decimal
    valor_libros_fiscal: Decimal

    @field_serializer(
        "costo", "valor_residual", "depreciacion_financiera", "valor_libros_financiero",
        "depreciacion_fiscal", "valor_libros_fiscal",
    )  # fmt: skip
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("porcentaje_fiscal")
    def porcentaje_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"
