from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_serializer, field_validator

from app.comun.nit import formatear_nit

TipoProveedor = Literal["local", "exterior"]
RubroProveedor = Literal[
    "subasta", "dealer", "naviera", "agente_aduanal", "repuestos", "seguros", "servicios", "otros"
]
Moneda = Literal["GTQ", "USD"]
RegimenProveedor = Literal["general", "pequeno_contribuyente"]
LineaNegocio = Literal["alquiler", "venta", "taller", "financiamiento", "administracion"]

# ── HU-4.01: proveedores ───────────────────────────────────────────────────────


class ProveedorEntrada(BaseModel):
    """Alta de proveedor. Las reglas que cruzan campos (NIT para locales, identificación fiscal y
    país para extranjeros; régimen para locales) y el dígito verificador se validan en el service."""

    tipo: TipoProveedor
    nombre: str = Field(max_length=200)
    nit: str | None = Field(default=None, max_length=20)
    identificacion_fiscal: str | None = Field(default=None, max_length=50)
    pais: str | None = Field(default=None, max_length=2)
    regimen: RegimenProveedor | None = None
    rubro: RubroProveedor
    moneda_habitual: Moneda
    dias_credito: int = Field(default=0, ge=0, le=365)
    banco: str | None = Field(default=None, max_length=100)
    cuenta_bancaria: str | None = Field(default=None, max_length=50)

    @field_validator("nombre", mode="before")
    @classmethod
    def recortar_nombre(cls, valor: object) -> object:
        """Sin espacios a los lados; si queda vacío, el service responde con un mensaje claro."""
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("nit", "identificacion_fiscal", "pais", "banco", "cuenta_bancaria", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        """Quita espacios a los lados; un texto vacío cuenta como no enviado."""
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class ProveedorSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoProveedor
    nombre: str
    nit: str | None
    identificacion_fiscal: str | None
    pais: str | None
    regimen: RegimenProveedor | None
    rubro: RubroProveedor
    moneda_habitual: Moneda
    dias_credito: int
    banco: str | None
    cuenta_bancaria: str | None
    creado_en: datetime

    @computed_field
    @property
    def nit_formateado(self) -> str | None:
        """NIT con guion para mostrar ("1234567-9"); `nit` queda normalizado para buscar."""
        return formatear_nit(self.nit) if self.nit else None


# ── HU-4.09: facturas de compras y gastos locales ─────────────────────────────


class LineaFacturaEntrada(BaseModel):
    """Línea del DTE. Base e IVA llegan como texto ("1250.00") para no pasar por float; la forma de
    la cuenta, el VIN y los montos se validan en el service."""

    descripcion: str = Field(max_length=300)
    cuenta: str = Field(max_length=20)
    linea_negocio: LineaNegocio
    vin: str | None = Field(default=None, max_length=17)
    base: str
    iva: str

    @field_validator("descripcion", "cuenta", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("vin", mode="before")
    @classmethod
    def recortar_vin(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip().upper() or None
        return valor

    @field_validator("base", "iva", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('Los montos se envían como texto, por ejemplo "1250.00"')
        return valor.strip()


class FacturaCompraEntrada(BaseModel):
    """Captura de un DTE FEL recibido de un proveedor local, en quetzales."""

    proveedor_id: int
    serie: str = Field(max_length=20)
    numero: str = Field(max_length=20)
    autorizacion: str = Field(max_length=36)
    fecha: date
    lineas: list[LineaFacturaEntrada] = Field(max_length=200)

    @field_validator("serie", "numero", "autorizacion", mode="before")
    @classmethod
    def recortar_y_mayusculas(cls, valor: object) -> object:
        return valor.strip().upper() if isinstance(valor, str) else valor


def _monto_texto(valor: Decimal) -> str:
    return f"{valor:.6f}"


class ProveedorResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nit: str | None
    regimen: RegimenProveedor | None

    @computed_field
    @property
    def nit_formateado(self) -> str | None:
        return formatear_nit(self.nit) if self.nit else None


class LineaFacturaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    numero_linea: int
    descripcion: str
    cuenta: str
    linea_negocio: LineaNegocio
    vin: str | None
    base: Decimal
    iva: Decimal

    @field_serializer("base", "iva")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class CuentaPorPagarSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    fecha_vencimiento: date
    moneda: Moneda
    monto: Decimal
    saldo: Decimal

    @field_serializer("monto", "saldo")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class FacturaCompraSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    proveedor: ProveedorResumen
    serie: str
    numero: str
    autorizacion: str
    fecha: date
    regimen_proveedor: RegimenProveedor
    total_base: Decimal
    total_iva: Decimal
    credito_fiscal: Decimal
    total: Decimal
    lineas: list[LineaFacturaSalida]
    cuenta_por_pagar: CuentaPorPagarSalida
    creado_en: datetime

    @field_serializer("total_base", "total_iva", "credito_fiscal", "total")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @computed_field
    @property
    def genera_credito_fiscal(self) -> bool:
        """La factura de un pequeño contribuyente no da crédito fiscal de IVA (criterio 4)."""
        return self.regimen_proveedor == "general"
