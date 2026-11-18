from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_serializer, field_validator

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


def _texto(valor: object) -> object:
    if not isinstance(valor, str):
        raise ValueError('Los montos se envían como texto, por ejemplo "1500.00"')
    return valor.strip()


# ── HU-3.06: contratos ─────────────────────────────────────────────────────────


class ContratoEntrada(BaseModel):
    """Registro del contrato al salir la unidad. La tarifa se toma del tarifario vigente el día de
    salida para la modalidad y moneda indicadas; el depósito esperado llega como texto."""

    cliente_id: int
    vin: str = Field(max_length=30)
    salida: AwareDatetime
    devolucion_prevista: date
    modalidad: Modalidad
    moneda: Moneda
    km_salida: int = Field(ge=0, le=10_000_000)
    combustible_salida: int = Field(ge=0, le=8, description="Octavos de tanque, de 0 (vacío) a 8 (lleno)")
    deposito_esperado: str = "0"

    _deposito_texto = field_validator("deposito_esperado", mode="before")(_texto)


class ContratoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: int
    cliente_id: int
    vin: str
    salida: datetime
    devolucion_prevista: date
    tarifa_id: int
    modalidad: Modalidad
    moneda: Moneda
    tarifa_monto: Decimal
    km_incluido: int
    precio_km_adicional: Decimal
    km_salida: int
    combustible_salida: int
    deposito_esperado: Decimal
    dias_previstos: int
    monto_estimado: Decimal
    estado: Literal["abierto", "cerrado"]
    creado_en: datetime
    devolucion: datetime | None
    km_devolucion: int | None
    combustible_devolucion: int | None
    observaciones_danos: str | None
    dias_efectivos: int | None
    km_recorridos: int | None
    km_excedentes: int | None
    combustible_faltante: int | None
    monto_final: Decimal | None

    @field_serializer(
        "tarifa_monto", "precio_km_adicional", "deposito_esperado", "monto_estimado", "monto_final"
    )
    def monto_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.6f}"


# ── HU-3.08: cierre ────────────────────────────────────────────────────────────


class CierreEntrada(BaseModel):
    devolucion: AwareDatetime
    km_devolucion: int = Field(ge=0, le=10_000_000)
    combustible_devolucion: int = Field(ge=0, le=8, description="Octavos de tanque, de 0 (vacío) a 8 (lleno)")
    observaciones_danos: str | None = Field(default=None, max_length=1000)


# ── HU-3.07: depósitos en garantía ─────────────────────────────────────────────


class DepositoEntrada(BaseModel):
    """Depósito en dinero (con su cuenta bancaria) o autorización de tarjeta sin cobro (con su
    referencia). La moneda de la cuenta bancaria se valida en el service."""

    tipo: Literal["deposito", "autorizacion_tarjeta"]
    fecha: date
    moneda: Moneda
    monto: str
    cuenta_bancaria_id: int | None = None
    referencia: str | None = Field(default=None, max_length=100)

    _monto_texto = field_validator("monto", mode="before")(_texto)


class AplicacionEntrada(BaseModel):
    fecha: date
    monto: str

    _monto_texto = field_validator("monto", mode="before")(_texto)


class DevolucionDepositoEntrada(AplicacionEntrada):
    cuenta_bancaria_id: int


class DepositoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contrato_id: int
    contrato_numero: int
    vin: str
    tipo: Literal["deposito", "autorizacion_tarjeta"]
    fecha: date
    moneda: Moneda
    monto: Decimal
    saldo: Decimal
    cuenta_bancaria_id: int | None
    referencia: str | None
    devuelto: bool
    creado_en: datetime

    @field_serializer("monto", "saldo")
    def monto_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.6f}"


class DepositosVigentes(BaseModel):
    depositos: list[DepositoSalida]
    totales: dict[Moneda, Decimal]

    @field_serializer("totales")
    def totales_a_texto(self, valores: dict[str, Decimal]) -> dict[str, str]:
        return {moneda: f"{valor:.6f}" for moneda, valor in valores.items()}
