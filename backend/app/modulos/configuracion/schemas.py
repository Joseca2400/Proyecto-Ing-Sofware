from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints, field_serializer, field_validator

from app.modulos.configuracion import service

# ── HU-1.02 y HU-1.04: catálogo de cuentas y dimensiones ──────────────────────

Tipo = Literal[*service.TIPOS]
Naturaleza = Literal[*service.NATURALEZAS]
ModoVin = Literal[*service.MODOS_VIN]
Linea = Literal[*service.LINEAS_NEGOCIO]


class DimensionesEntrada(BaseModel):
    linea_obligatoria: bool = False
    vin: ModoVin = "no_aplica"
    linea_defecto: Linea | None = None


class CuentaEntrada(DimensionesEntrada):
    codigo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]
    nombre: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    tipo: Tipo
    naturaleza: Naturaleza
    padre_id: int | None = None
    es_detalle: bool = True
    monetaria_usd: bool = False


class CuentaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    nombre: str
    tipo: Tipo
    naturaleza: Naturaleza
    nivel: int
    padre_id: int | None
    es_detalle: bool
    monetaria_usd: bool
    linea_obligatoria: bool
    vin: ModoVin
    linea_defecto: Linea | None


# ── HU-1.06: tipo de cambio ────────────────────────────────────────────────────


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


# ── HU-1.07: transacciones en USD ─────────────────────────────────────────────


class TransaccionUSDEntrada(BaseModel):
    """Registro de un monto en USD.

    monto_usd y tipo_cambio_personalizado llegan como texto para no pasar por float.
    Si se indica tipo_cambio_personalizado, justificacion es obligatoria (validación en service).
    """

    fecha: date
    monto_usd: str
    tipo_cambio_personalizado: str | None = None
    justificacion: str | None = None

    @field_validator("monto_usd", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('El monto en USD se envía como texto, por ejemplo "8500.00"')
        return valor

    @field_validator("tipo_cambio_personalizado", mode="before")
    @classmethod
    def tipo_personalizado_como_texto(cls, valor: object) -> object:
        if valor is not None and not isinstance(valor, str):
            raise ValueError("El tipo de cambio personalizado se envía como texto")
        return valor


class TransaccionUSDSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    monto_usd: Decimal
    tipo_cambio_aplicado: Decimal
    monto_gtq: Decimal
    justificacion: str | None

    @field_serializer("monto_usd", "monto_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.6f}"

    @field_serializer("tipo_cambio_aplicado")
    def tipo_cambio_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.8f}"
