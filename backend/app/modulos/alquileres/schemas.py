from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator

Modalidad = Literal["diaria", "semanal", "mensual", "kilometraje"]
Moneda = Literal["GTQ", "USD"]
Naturaleza = Literal["ingreso", "deposito", "reintegro"]


def _texto(valor: Decimal | None) -> str | None:
    return None if valor is None else f"{valor:.6f}"


def _monto_como_texto(valor: object) -> object:
    """Los montos llegan como texto ("300.00") para no pasar por float; vacío es no enviado."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ValueError('Los montos se envían como texto, por ejemplo "300.00"')
    return valor.strip() or None


# ── Temporadas (listas de precios con fechas) ─────────────────────────────────


class TemporadaEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    fecha_inicio: date
    fecha_fin: date

    @field_validator("nombre", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class TemporadaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    activa: bool


# ── Tarifas ────────────────────────────────────────────────────────────────────


class TarifaEntrada(BaseModel):
    """Tarifa por tipo de vehículo o por unidad (VIN), nunca ambas; la regla y los montos se
    validan en el service."""

    tipo_vehiculo: str | None = Field(default=None, max_length=20)
    vin: str | None = Field(default=None, max_length=17)
    temporada_id: int | None = None
    modalidad: Modalidad
    moneda: Moneda
    monto: str
    km_incluido: int | None = Field(default=None, ge=0, le=1_000_000)
    costo_km_adicional: str | None = None
    vigente_desde: date

    @field_validator("tipo_vehiculo", "vin", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @field_validator("monto", "costo_km_adicional", mode="before")
    @classmethod
    def como_texto(cls, valor: object) -> object:
        return _monto_como_texto(valor)


class TarifaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo_vehiculo: str | None
    vin: str | None
    temporada: TemporadaSalida | None
    modalidad: Modalidad
    moneda: Moneda
    monto: Decimal
    km_incluido: int | None
    costo_km_adicional: Decimal | None
    vigente_desde: date
    creado_en: datetime

    @field_serializer("monto", "costo_km_adicional")
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _texto(valor)


# ── Conceptos (cargos adicionales y cómo tributan) ────────────────────────────


class ConceptoEntrada(BaseModel):
    nombre: str = Field(max_length=100)
    naturaleza: Naturaleza
    aplica_iva: bool = False
    precio_sugerido: str | None = None
    moneda: Moneda | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("precio_sugerido", mode="before")
    @classmethod
    def como_texto(cls, valor: object) -> object:
        return _monto_como_texto(valor)


class ConceptoCambio(BaseModel):
    """Cambio de precio o baja de un concepto; la naturaleza fiscal no se cambia."""

    precio_sugerido: str | None = None
    moneda: Moneda | None = None
    activo: bool = True

    @field_validator("precio_sugerido", mode="before")
    @classmethod
    def como_texto(cls, valor: object) -> object:
        return _monto_como_texto(valor)


class ConceptoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    naturaleza: Naturaleza
    aplica_iva: bool
    precio_sugerido: Decimal | None
    moneda: Moneda | None
    activo: bool

    @field_serializer("precio_sugerido")
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return _texto(valor)

    @computed_field
    @property
    def es_ingreso_acumulable(self) -> bool:
        """Solo un ingreso cuenta para el ISR; depósitos y reintegros no."""
        return self.naturaleza == "ingreso"


# ── Cotización ─────────────────────────────────────────────────────────────────


class CargoCotizacion(BaseModel):
    concepto_id: int
    cantidad: int = Field(default=1, ge=1, le=1000)
    precio: str | None = None  # obligatorio si el concepto no tiene precio sugerido (una multa)

    @field_validator("precio", mode="before")
    @classmethod
    def como_texto(cls, valor: object) -> object:
        return _monto_como_texto(valor)


class CotizacionEntrada(BaseModel):
    tipo_vehiculo: str = Field(max_length=20)
    vin: str | None = Field(default=None, max_length=17)
    modalidad: Modalidad
    moneda: Moneda
    fecha_salida: date
    fecha_devolucion: date
    km_estimados: int | None = Field(default=None, ge=0, le=1_000_000)
    cargos: list[CargoCotizacion] = Field(default_factory=list, max_length=50)

    @field_validator("tipo_vehiculo", "vin", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class LineaCotizacion(BaseModel):
    descripcion: str
    naturaleza: Naturaleza
    aplica_iva: bool
    cantidad: Decimal
    precio_unitario: Decimal
    total: Decimal
    base: Decimal
    iva: Decimal

    @field_serializer("cantidad")
    def cantidad_a_texto(self, valor: Decimal) -> str:
        return f"{valor.normalize():f}"

    @field_serializer("precio_unitario", "total", "base", "iva")
    def monto_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"


class CotizacionSalida(BaseModel):
    moneda: Moneda
    tarifa: TarifaSalida
    periodos: int
    dias: int
    tipo_cambio: Decimal | None  # solo si hubo que convertir de la otra moneda
    tasa_iva: Decimal
    lineas: list[LineaCotizacion]
    total_ingresos: Decimal
    total_base: Decimal
    total_iva: Decimal
    total_depositos: Decimal
    total_reintegros: Decimal
    total_a_pagar: Decimal

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.8f}"

    @field_serializer("tasa_iva")
    def tasa_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.6f}"

    @field_serializer(
        "total_ingresos",
        "total_base",
        "total_iva",
        "total_depositos",
        "total_reintegros",
        "total_a_pagar",
    )
    def monto_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.2f}"
