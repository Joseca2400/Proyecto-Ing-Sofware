from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.comun.nit import formatear_nit

TipoProveedor = Literal["local", "exterior"]
RubroProveedor = Literal[
    "subasta", "dealer", "naviera", "agente_aduanal", "repuestos", "seguros", "servicios", "otros"
]
Moneda = Literal["GTQ", "USD"]

# ── HU-4.01: proveedores ───────────────────────────────────────────────────────


class ProveedorEntrada(BaseModel):
    """Alta de proveedor. Las reglas que cruzan campos (NIT para locales, identificación fiscal y
    país para extranjeros) y el dígito verificador se validan en el service."""

    tipo: TipoProveedor
    nombre: str = Field(max_length=200)
    nit: str | None = Field(default=None, max_length=20)
    identificacion_fiscal: str | None = Field(default=None, max_length=50)
    pais: str | None = Field(default=None, max_length=2)
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
