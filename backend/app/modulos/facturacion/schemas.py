from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

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
