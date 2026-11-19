from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.comun.nit import formatear_nit

TipoCliente = Literal["individual", "empresa"]

# ── HU-6.01: clientes ──────────────────────────────────────────────────────────


class ClienteEntrada(BaseModel):
    """Alta de cliente. Las reglas que cruzan campos (qué identificación lleva cada tipo, pasaporte
    con país) y el dígito verificador del NIT se validan en el service."""

    tipo: TipoCliente
    nombre: str = Field(max_length=200)
    nit: str | None = Field(default=None, max_length=20)
    cui: str | None = Field(default=None, max_length=20)
    pasaporte: str | None = Field(default=None, max_length=30)
    pais: str | None = Field(default=None, max_length=2)
    direccion: str | None = Field(default=None, max_length=300)
    telefono: str | None = Field(default=None, max_length=30)
    correo: str | None = Field(default=None, max_length=100)
    agente_retencion_iva: bool = False
    agente_retencion_isr: bool = False

    @field_validator("nombre", mode="before")
    @classmethod
    def recortar_nombre(cls, valor: object) -> object:
        """Sin espacios a los lados; si queda vacío, el service responde con un mensaje claro."""
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("nit", "cui", "pasaporte", "pais", "direccion", "telefono", "correo", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        """Quita espacios a los lados; un texto vacío cuenta como no enviado."""
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class ClienteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoCliente
    nombre: str
    nit: str | None
    cui: str | None
    pasaporte: str | None
    pais: str | None
    direccion: str | None
    telefono: str | None
    correo: str | None
    agente_retencion_iva: bool
    agente_retencion_isr: bool
    creado_en: datetime

    @computed_field
    @property
    def nit_formateado(self) -> str | None:
        """NIT con guion para mostrar ("1234567-9"); `nit` queda normalizado para buscar."""
        return formatear_nit(self.nit) if self.nit else None
