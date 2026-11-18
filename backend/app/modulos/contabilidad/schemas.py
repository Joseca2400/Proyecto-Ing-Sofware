from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    PlainSerializer,
    StringConstraints,
    computed_field,
    field_serializer,
    field_validator,
)

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LineaEntrada(BaseModel):
    """Línea de una partida. `monto` va como texto y en la moneda de la línea: en USD se
    convierte con el tipo de cambio de la fecha de la partida (HU-1.06)."""

    cuenta_id: int
    lado: Literal["debe", "haber"]
    monto: str
    moneda: Literal["GTQ", "USD"] = "GTQ"
    linea_negocio: str | None = None
    vin: str | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('El monto se envía como texto, por ejemplo "1250.00"')
        return valor


class LineaAutomatica(LineaEntrada):
    """Solo para `registrar_automatica` (no la recibe ninguna ruta): una línea en USD llevada al
    tipo de cambio dado y no al de la fecha, p. ej. el saldo en libros de la factura que se paga
    (HU-2.09)."""

    tipo_cambio: Decimal | None = None


class PartidaEntrada(BaseModel):
    fecha: date
    concepto: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    documento_soporte: Annotated[str, StringConstraints(strip_whitespace=True, max_length=100)] | None = None
    lineas: list[LineaEntrada]


class ReglaEntrada(BaseModel):
    cuenta_codigo: Texto


class ReglaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_tipo: str
    concepto: str
    descripcion: str
    cuenta_codigo: str | None


class DevolucionEntrada(BaseModel):
    comentario: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class ReversionEntrada(BaseModel):
    fecha: date
    motivo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class LineaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero_linea: int
    cuenta_id: int
    debe: Decimal
    haber: Decimal
    moneda: str
    monto_usd: Decimal | None
    tipo_cambio: Decimal | None
    linea_negocio: str | None
    vin: str | None

    @field_serializer("debe", "haber", "monto_usd")
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.6f}"

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.8f}"


class PartidaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int | None
    fecha: date
    concepto: str
    documento_soporte: str | None
    estado: str
    origen: str
    documento_tipo: str | None
    documento_id: str | None
    comentario: str | None
    creado_por: int | None
    contabilizada_por: int | None
    contabilizada_en: datetime | None
    revierte_a: int | None
    revertida_por: int | None
    lineas: list[LineaSalida]

    # El front no suma montos: la bandeja de revisión muestra estos totales.
    @computed_field
    @property
    def total_debe(self) -> str:
        return f"{sum((linea.debe for linea in self.lineas), Decimal(0)):.6f}"

    @computed_field
    @property
    def total_haber(self) -> str:
        return f"{sum((linea.haber for linea in self.lineas), Decimal(0)):.6f}"


# ── HU-2.16: balance de comprobación y mayor ──────────────────────────────────

Monto = Annotated[Decimal, PlainSerializer(lambda valor: f"{valor:.6f}", return_type=str)]
TipoCambio = Annotated[Decimal, PlainSerializer(lambda valor: f"{valor:.8f}", return_type=str)]


class FilaBalance(BaseModel):
    cuenta_id: int
    codigo: str
    nombre: str
    naturaleza: str
    saldo_inicial: Monto
    debe: Monto
    haber: Monto
    saldo_final: Monto


class BalanceSalida(BaseModel):
    filas: list[FilaBalance]
    total_debe: Monto
    total_haber: Monto


class MovimientoMayor(BaseModel):
    fecha: date
    partida_id: int
    numero: int | None
    concepto: str
    documento_tipo: str | None
    documento_id: str | None
    debe: Monto
    haber: Monto
    saldo: Monto
    moneda: str
    monto_usd: Monto | None
    tipo_cambio: TipoCambio | None
    linea_negocio: str | None
    vin: str | None


class MayorSalida(BaseModel):
    cuenta_id: int
    codigo: str
    nombre: str
    naturaleza: str
    monetaria_usd: bool
    saldo_inicial: Monto
    movimientos: list[MovimientoMayor]
    saldo_final: Monto
