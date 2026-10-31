"""Esquemas de entrada y salida de la API."""

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, field_validator

from app.models import LineaNegocio, Moneda, Rol

Numero = Annotated[Decimal, PlainSerializer(lambda v: float(v), return_type=float)]


def _txt(v: str) -> str:
    v = " ".join(v.split())
    if not v:
        raise ValueError("no puede estar vacío")
    return v


def _txt_opc(v: str | None) -> str | None:
    if v is None:
        return None
    v = " ".join(v.split())
    return v or None


def positivo(v: Decimal) -> Decimal:
    if v <= 0:
        raise ValueError("debe ser mayor que 0")
    return v


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ======================================================================= E1

class UsuarioIn(BaseModel):
    usuario: str = Field(max_length=40, examples=["aux2"])
    nombre: str = Field(max_length=120)
    rol: Rol
    password: str = Field(min_length=1, examples=["Clave2026"])
    v = field_validator("usuario", "nombre")(_txt)


class LoginIn(BaseModel):
    usuario: str = Field(examples=["aux"])
    password: str = Field(examples=["Demo2026!"])


class LoginOut(BaseModel):
    token: str
    tipo: str = "Bearer"
    expira_en: datetime
    usuario: "UsuarioOut"


class UsuarioOut(ORM):
    id: int
    usuario: str
    nombre: str
    rol: str
    activo: bool


class CuentaIn(BaseModel):
    codigo: str = Field(max_length=20, examples=["6.1.03"])
    nombre: str = Field(max_length=120, examples=["Seguros de flota"])
    tipo: Literal["ACTIVO", "PASIVO", "PATRIMONIO", "INGRESO", "COSTO", "GASTO"]
    naturaleza: Literal["DEUDORA", "ACREEDORA"]
    es_detalle: bool = True
    monetaria_usd: bool = False
    exige_vin: Literal["OBLIGATORIO", "OPCIONAL", "NO_APLICA"] = "NO_APLICA"
    linea_defecto: LineaNegocio | None = None
    v = field_validator("codigo", "nombre")(_txt)


class CuentaOut(ORM):
    id: int
    codigo: str
    nombre: str
    tipo: str
    naturaleza: str
    es_detalle: bool
    monetaria_usd: bool
    exige_vin: str
    linea_defecto: str | None
    activa: bool


class TipoCambioIn(BaseModel):
    fecha: date
    valor: Decimal = Field(description="Quetzales por 1 USD (referencia Banguat)", examples=[7.71])
    v = field_validator("valor")(positivo)


class TipoCambioOut(ORM):
    fecha: date
    valor: Numero
    origen: str
    registrado_por: str


class HistorialOut(ORM):
    estado_anterior: str | None
    estado_nuevo: str
    fecha: datetime
    usuario: str
    documento: str


class UnidadOut(ORM):
    id: int
    vin: str
    marca: str
    linea: str
    modelo_anio: int
    color: str | None
    tipo_vehiculo: str | None
    estado: str
    kilometraje: int
    fecha_alta_flota: date | None
    costo_alta: Numero | None
    vida_util_meses: int | None
    valor_residual: Numero | None
    historial: list[HistorialOut]


class EstadoIn(BaseModel):
    estado: Literal["EN_ADUANA", "LISTA"]
    documento: str = Field(examples=["Arribo a Puerto Quetzal"])
    v = field_validator("documento")(_txt)


class BitacoraOut(ORM):
    id: int
    fecha: datetime
    usuario: str
    accion: str
    entidad: str
    entidad_id: int | None
    vin: str | None
    detalle: str | None
    valores_anteriores: dict | None
    valores_nuevos: dict | None

    @field_validator("valores_anteriores", "valores_nuevos", mode="before")
    @classmethod
    def _json(cls, v):
        import json
        return json.loads(v) if isinstance(v, str) else v


# ======================================================================= E2

class LineaPartidaIn(BaseModel):
    cuenta: str = Field(examples=["1.1.01"])
    lado: Literal["DEBE", "HABER"]
    monto: Decimal = Field(description="En la moneda de la línea")
    moneda: Moneda = Moneda.GTQ
    linea_negocio: LineaNegocio | None = None
    vin: str | None = None
    detalle: str | None = None
    tipo_cambio: Decimal | None = Field(default=None, description="Sólo si difiere del Banguat (requiere justificación)")
    v = field_validator("monto")(positivo)

    @field_validator("tipo_cambio")
    @classmethod
    def _tc_positivo(cls, v):
        if v is not None and v <= 0:
            raise ValueError("el tipo de cambio debe ser mayor que 0")
        return v


class PartidaIn(BaseModel):
    fecha: date
    concepto: str = Field(max_length=250)
    lineas: list[LineaPartidaIn] = Field(min_length=2)
    justificacion_tipo_cambio: str | None = None
    v = field_validator("concepto")(_txt)


class DevolverIn(BaseModel):
    comentario: str
    v = field_validator("comentario")(_txt)


class LineaPartidaOut(BaseModel):
    cuenta: str
    nombre_cuenta: str
    debe: Numero
    haber: Numero
    moneda: str
    monto_original: Numero | None
    tipo_cambio: Numero | None
    linea_negocio: str
    vin: str | None
    detalle: str | None


class PartidaOut(BaseModel):
    id: int
    numero: int | None
    fecha: date
    concepto: str
    estado: str
    automatica: bool
    origen_tipo: str | None
    origen_id: int | None
    registrada_por: str
    contabilizada_por: str | None
    comentario_revision: str | None
    total_debe: Numero
    total_haber: Numero
    lineas: list[LineaPartidaOut]


# ======================================================================= E4

class ProveedorIn(BaseModel):
    nombre: str = Field(max_length=120, examples=["Copart Inc."])
    tipo: Literal["LOCAL", "EXTERIOR"]
    nit: str | None = None
    pais: str | None = None
    rubro: Literal["SUBASTA", "DEALER", "NAVIERA", "AGENTE_ADUANAL", "REPUESTOS", "SEGUROS", "SERVICIOS", "SAT", "OTROS"]
    moneda: Moneda
    v = field_validator("nombre")(_txt)


class ProveedorOut(ORM):
    id: int
    nombre: str
    tipo: str
    nit: str | None
    pais: str
    rubro: str
    moneda: str


class CompraIn(BaseModel):
    proveedor_id: int
    fecha: date
    numero_lote: str = Field(examples=["LOT-58213"])
    vin: str = Field(examples=["1HGCM82633A004352"])
    marca: str = Field(examples=["Honda"])
    linea: str = Field(examples=["Accord"])
    modelo_anio: int = Field(ge=1980, le=2100, examples=[2019])
    color: str | None = None
    tipo_vehiculo: str | None = Field(default=None, examples=["Sedán"])
    precio_usd: Decimal = Field(examples=[8500])
    cargos_usd: Decimal = Field(default=Decimal("0"), ge=0, description="Comisión, documentación, arrastre")
    v = field_validator("precio_usd")(positivo)
    v2 = field_validator("numero_lote", "marca", "linea")(_txt)


class DocumentoOut(ORM):
    id: int
    proveedor_id: int
    tipo: str
    referencia: str | None
    fecha: date
    moneda: str
    monto: Numero
    saldo: Numero
    tipo_cambio: Numero | None
    partida_id: int | None


class CompraOut(BaseModel):
    unidad: UnidadOut
    documento: DocumentoOut
    partida_numero: int


class GastoIn(BaseModel):
    unidad_id: int
    proveedor_id: int
    concepto: Literal["FLETE", "SEGURO", "AGENTE_ADUANAL", "ALMACENAJE", "DAI", "IVA_IMPORTACION",
                      "IPRIMA", "PLACAS", "OTROS"]
    fecha: date
    moneda: Moneda
    monto: Decimal
    referencia: str | None = None
    v = field_validator("monto")(positivo)


class GastoOut(BaseModel):
    id: int
    concepto: str
    documento: DocumentoOut
    partida_numero: int
    capitalizable: bool = Field(description="False si es crédito fiscal (IVA de importación)")


# ======================================================================= E5

class OrdenIn(BaseModel):
    unidad_id: int
    tipo: Literal["REACONDICIONAMIENTO", "MANTENIMIENTO"]
    descripcion: str
    responsable: str
    fecha: date
    kilometraje: int | None = Field(default=None, ge=0)
    v = field_validator("descripcion", "responsable")(_txt)


class ManoObraIn(BaseModel):
    mecanico: str
    fecha: date
    horas: Decimal = Field(examples=[6])
    descripcion: str
    v = field_validator("horas")(positivo)
    v2 = field_validator("mecanico", "descripcion")(_txt)


class ManoObraOut(ORM):
    mecanico: str
    fecha: date
    horas: Numero
    tarifa: Numero
    costo: Numero
    descripcion: str


class OrdenOut(BaseModel):
    id: int
    unidad_id: int
    vin: str
    tipo: str
    descripcion: str
    responsable: str
    fecha_apertura: date
    fecha_cierre: date | None
    estado: str
    costo_total: Numero
    partida_id: int | None
    mano_obra: list[ManoObraOut]


class CerrarOrdenIn(BaseModel):
    fecha: date
    justificacion: str | None = None


class AltaFlotaIn(BaseModel):
    fecha: date
    vida_util_meses: int = Field(default=60, ge=1, le=240)
    valor_residual: Decimal = Field(default=Decimal("0"), ge=0)


# ======================================================================= E6 / E3

class ClienteIn(BaseModel):
    tipo: Literal["INDIVIDUAL", "EMPRESA"]
    nombre: str = Field(max_length=150)
    nit: str | None = Field(default=None, examples=["1234567-9"])
    cui: str | None = None
    pasaporte: str | None = None
    pais: str = "Guatemala"
    direccion: str | None = None
    telefono: str | None = None
    correo: str | None = None
    v = field_validator("nombre")(_txt)
    v2 = field_validator("nit", "cui", "pasaporte", "direccion", "telefono", "correo")(_txt_opc)


class ClienteOut(ORM):
    id: int
    tipo: str
    nombre: str
    nit: str | None
    cui: str | None
    pasaporte: str | None
    pais: str
    direccion: str | None
    telefono: str | None
    correo: str | None


class ContratoIn(BaseModel):
    cliente_id: int
    unidad_id: int
    fecha_salida: date
    fecha_prevista: date
    tarifa_diaria: Decimal = Field(description="IVA incluido", examples=[350])
    moneda: Moneda = Moneda.GTQ
    km_salida: int | None = Field(default=None, ge=0)
    v = field_validator("tarifa_diaria")(positivo)


class CerrarContratoIn(BaseModel):
    fecha_devolucion: date
    km_entrada: int = Field(ge=0)
    observaciones: str | None = None


class ContratoOut(BaseModel):
    id: int
    cliente_id: int
    cliente: str
    unidad_id: int
    vin: str
    fecha_salida: date
    fecha_prevista: date
    fecha_devolucion: date | None
    tarifa_diaria: Numero
    moneda: str
    km_salida: int
    km_entrada: int | None
    estado: str
    monto_estimado: Numero
    dias: int | None = None
    km_recorridos: int | None = None
    monto: Numero | None = None


class FacturarIn(BaseModel):
    fecha: date
    consumidor_final: bool = False


class FacturaOut(ORM):
    id: int
    serie: str
    numero_dte: int
    autorizacion: str
    simulada: bool
    cliente_id: int | None
    fecha: date
    moneda: str
    tipo_cambio: Numero | None
    base: Numero
    iva: Numero
    total: Numero
    total_q: Numero
    saldo: Numero
    descripcion: str
    linea_negocio: str
    unidad_id: int | None
    origen_tipo: str
    origen_id: int
    partida_id: int | None


class CobroIn(BaseModel):
    fecha: date
    forma: Literal["EFECTIVO", "CHEQUE", "TRANSFERENCIA", "TARJETA"]
    monto: Decimal = Field(description="En la moneda de la factura")
    referencia: str | None = None
    v = field_validator("monto")(positivo)


class CobroOut(ORM):
    id: int
    factura_id: int
    fecha: date
    forma: str
    monto: Numero
    tipo_cambio: Numero | None
    diferencial_q: Numero = Field(description="Positivo: ganancia cambiaria; negativo: pérdida")
    referencia: str | None
    partida_id: int | None


LoginOut.model_rebuild()
