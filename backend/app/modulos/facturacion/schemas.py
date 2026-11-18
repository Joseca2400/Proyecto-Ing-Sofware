from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator

from app.comun.nit import formatear_nit

TipoCliente = Literal["individual", "empresa"]
TipoIdentificacion = Literal["nit", "cui", "pasaporte"]


class ClienteEntrada(BaseModel):
    """Alta de cliente. El verificador del NIT y las reglas que cruzan campos (empresa solo con
    NIT, país solo con pasaporte) se validan en el service."""

    tipo: TipoCliente
    nombre: str = Field(max_length=200)
    tipo_identificacion: TipoIdentificacion
    identificacion: str = Field(max_length=30)
    pais: str | None = Field(default=None, max_length=2)
    direccion: str | None = Field(default=None, max_length=300)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=120)
    agente_retencion_iva: bool = False
    agente_retencion_isr: bool = False

    @field_validator("nombre", "identificacion", mode="before")
    @classmethod
    def recortar_obligatorio(cls, valor: object) -> object:
        """Sin espacios a los lados; si queda vacío, el service responde con un mensaje claro."""
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("pais", "direccion", "telefono", "correo", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        """Quita espacios a los lados; un texto vacío cuenta como no enviado."""
        return (valor.strip() or None) if isinstance(valor, str) else valor


class ClienteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoCliente
    nombre: str
    tipo_identificacion: TipoIdentificacion
    identificacion: str
    pais: str | None
    direccion: str | None
    telefono: str | None
    correo: str | None
    agente_retencion_iva: bool
    agente_retencion_isr: bool
    creado_en: datetime

    @computed_field
    @property
    def identificacion_formateada(self) -> str:
        """NIT con guion para mostrar; CUI y pasaporte tal cual."""
        return (
            formatear_nit(self.identificacion) if self.tipo_identificacion == "nit" else self.identificacion
        )


# ── HU-6.02: facturas FEL ──────────────────────────────────────────────────────

OrigenFactura = Literal["contrato", "venta", "orden_taller"]


class LineaFacturaFelEntrada(BaseModel):
    """Línea de la factura. Cantidad y precio unitario (con IVA) llegan como texto ("1120.00");
    se validan en el service, igual que la línea de negocio y el VIN."""

    descripcion: str = Field(max_length=300)
    cantidad: str
    precio_unitario: str
    linea_negocio: str = Field(max_length=20)
    vin: str | None = Field(default=None, max_length=17)

    @field_validator("descripcion", "linea_negocio", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("vin", mode="before")
    @classmethod
    def recortar_vin(cls, valor: object) -> object:
        return (valor.strip().upper() or None) if isinstance(valor, str) else valor

    @field_validator("cantidad", "precio_unitario", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('Los montos se envían como texto, por ejemplo "1120.00"')
        return valor.strip()


class FacturaEntrada(BaseModel):
    """Factura a emitir. Sin `cliente_id` se emite a Consumidor Final; `origen_tipo` y `origen_id`
    (los dos o ninguno) ligan la factura al contrato, la venta o la orden que la origina."""

    cliente_id: int | None = None
    fecha: date
    moneda: Literal["GTQ", "USD"]
    dias_credito: int = Field(default=0, ge=0, le=365)
    origen_tipo: OrigenFactura | None = None
    origen_id: int | None = None
    lineas: list[LineaFacturaFelEntrada] = Field(max_length=200)


def _texto(valor: Decimal | None) -> str | None:
    return None if valor is None else f"{valor:.6f}"


class LineaFacturaFelSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero_linea: int
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    total: Decimal
    base: Decimal
    iva: Decimal
    linea_negocio: str
    vin: str | None

    @field_serializer("cantidad", "precio_unitario", "total", "base", "iva")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _texto(valor)


class CuentaPorCobrarSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    fecha_vencimiento: date
    moneda: str
    monto: Decimal
    saldo: Decimal

    @field_serializer("monto", "saldo")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _texto(valor)


class FacturaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int | None
    fecha: date
    moneda: str
    tipo_cambio: Decimal | None
    origen_tipo: str | None
    origen_id: int | None
    dias_credito: int
    emisor_nit: str
    emisor_nombre: str
    receptor_id: str
    receptor_nombre: str
    base: Decimal
    iva: Decimal
    total: Decimal
    total_gtq: Decimal
    estado: Literal["pendiente", "certificada", "rechazada"]
    serie: str | None
    numero: str | None
    autorizacion: str | None
    certificada_en: datetime | None
    xml: str | None
    motivo_rechazo: str | None
    partida_id: int | None
    lineas: list[LineaFacturaFelSalida]
    cuenta_por_cobrar: CuentaPorCobrarSalida | None

    @field_serializer("base", "iva", "total", "total_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _texto(valor)

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.8f}"
