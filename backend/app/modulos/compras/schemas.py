from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PlainSerializer,
    computed_field,
    field_serializer,
    field_validator,
)

from app.comun.nit import formatear_nit

TipoProveedor = Literal["local", "exterior"]
RubroProveedor = Literal[
    "subasta", "dealer", "naviera", "agente_aduanal", "repuestos", "seguros", "servicios", "otros"
]
Moneda = Literal["GTQ", "USD"]
RegimenProveedor = Literal["general", "pequeno_contribuyente"]

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
    la cuenta, la línea de negocio (contra `configuracion`), el VIN (contra `unidades`) y los montos
    se validan en el service."""

    descripcion: str = Field(max_length=300)
    cuenta: str = Field(max_length=20)
    linea_negocio: str = Field(max_length=20)
    vin: str | None = Field(default=None, max_length=17)
    base: str
    iva: str

    @field_validator("descripcion", "cuenta", "linea_negocio", mode="before")
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
    linea_negocio: str
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


# ── HU-4.04: gastos de importación ────────────────────────────────────────────

TratamientoGasto = Literal["costo", "credito_fiscal"]


class ConceptoGastoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    codigo: str
    nombre: str
    cuenta: str
    tratamiento: TratamientoGasto

    @computed_field
    @property
    def suma_al_costo(self) -> bool:
        """El IVA de importación es crédito fiscal y no suma al costo de la unidad (criterio 3)."""
        return self.tratamiento == "costo"


class GastoImportacionEntrada(BaseModel):
    """Gasto de importación de una unidad. El monto llega como texto ("350.00"); el VIN (contra
    `unidades`), el concepto, el proveedor y el tipo de cambio se validan en el service."""

    vin: str = Field(max_length=30)
    concepto: str = Field(max_length=20)
    proveedor_id: int
    fecha: date
    documento: str = Field(max_length=50)
    descripcion: str | None = Field(default=None, max_length=300)
    moneda: Moneda
    monto: str

    @field_validator("vin", mode="before")
    @classmethod
    def normalizar_vin(cls, valor: object) -> object:
        return valor.strip().upper() if isinstance(valor, str) else valor

    @field_validator("concepto", "documento", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("descripcion", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @field_validator("monto", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('Los montos se envían como texto, por ejemplo "350.00"')
        return valor.strip()


class ProveedorGasto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    tipo: TipoProveedor


class GastoImportacionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    concepto: str
    concepto_nombre: str
    proveedor: ProveedorGasto
    fecha: date
    documento: str
    descripcion: str | None
    moneda: Moneda
    monto: Decimal
    tipo_cambio: Decimal | None
    monto_gtq: Decimal
    cuenta: str
    tratamiento: TratamientoGasto
    cuenta_por_pagar: CuentaPorPagarSalida
    creado_en: datetime

    @field_serializer("monto", "monto_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.8f}"

    @computed_field
    @property
    def suma_al_costo(self) -> bool:
        return self.tratamiento == "costo"


class ResumenGastosUnidad(BaseModel):
    """Costo de la unidad en quetzales que calcula el servidor; el front solo les da formato.

    `costo_total_gtq` es la compra (HU-4.02) más los gastos que suman al costo (HU-4.04); el IVA de
    importación es crédito fiscal y queda aparte.
    """

    vin: str
    gastos: int
    total_costo_gtq: Decimal
    total_credito_fiscal_gtq: Decimal
    compra_gtq: Decimal
    costo_total_gtq: Decimal

    @field_serializer("total_costo_gtq", "total_credito_fiscal_gtq", "compra_gtq", "costo_total_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


# ── HU-4.02: compra de la unidad en EE. UU. ───────────────────────────────────


class CompraUnidadEntrada(BaseModel):
    """Compra en USD a un proveedor del exterior con los datos de la unidad que crea.

    Los montos llegan como texto ("8500.00"); los cargos de la subasta son opcionales ("0"). El VIN
    y la ficha los valida `unidades`; el proveedor, los montos y el tipo de cambio, el service.
    """

    proveedor_id: int
    fecha: date
    documento: str = Field(max_length=50)
    vin: str = Field(max_length=30)
    marca: str = Field(max_length=50)
    linea: str = Field(max_length=50)
    modelo: int
    color: str = Field(max_length=30)
    tipo_vehiculo: str = Field(max_length=20)
    linea_negocio: str | None = Field(default=None, max_length=20)
    precio_usd: str
    comision_usd: str = "0"
    documentacion_usd: str = "0"
    arrastre_usd: str = "0"

    @field_validator("vin", mode="before")
    @classmethod
    def normalizar_vin(cls, valor: object) -> object:
        return valor.strip().upper() if isinstance(valor, str) else valor

    @field_validator("documento", "marca", "linea", "color", "tipo_vehiculo", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("linea_negocio", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @field_validator("precio_usd", "comision_usd", "documentacion_usd", "arrastre_usd", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if not isinstance(valor, str):
            raise ValueError('Los montos se envían como texto, por ejemplo "8500.00"')
        return valor.strip() or "0"


class CompraUnidadSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vin: str
    proveedor: ProveedorGasto
    fecha: date
    documento: str
    precio_usd: Decimal
    comision_usd: Decimal
    documentacion_usd: Decimal
    arrastre_usd: Decimal
    total_usd: Decimal
    tipo_cambio: Decimal
    total_gtq: Decimal
    partida_id: int
    cuenta_por_pagar: CuentaPorPagarSalida
    creado_en: datetime

    @field_serializer(
        "precio_usd", "comision_usd", "documentacion_usd", "arrastre_usd", "total_usd", "total_gtq"
    )
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.8f}"


# ── HU-4.08: hoja de costo de una unidad ──────────────────────────────────────


class CompraHojaCosto(BaseModel):
    fecha: date
    documento: str
    proveedor: str
    total_usd: Decimal
    tipo_cambio: Decimal
    total_gtq: Decimal

    @field_serializer("total_usd", "total_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal) -> str:
        return f"{valor:.8f}"


class GastoHojaCosto(BaseModel):
    """Un gasto de importación; `suma_al_costo` es falso para el IVA de importación (crédito fiscal)."""

    concepto: str
    nombre: str
    fecha: date
    documento: str
    moneda: Moneda
    monto: Decimal
    tipo_cambio: Decimal | None
    monto_gtq: Decimal
    suma_al_costo: bool

    @field_serializer("monto", "monto_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("tipo_cambio")
    def tipo_cambio_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else f"{valor:.8f}"


class ManoObraHojaCosto(BaseModel):
    numero: str
    fecha_cierre: date
    costo_gtq: Decimal

    @field_serializer("costo_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class RepuestoHojaCosto(BaseModel):
    """Línea de una factura local cargada a unidades en proceso con el VIN (repuesto o subcontrato)."""

    documento: str
    proveedor: str
    fecha: date
    descripcion: str
    monto_gtq: Decimal

    @field_serializer("monto_gtq")
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)


class HojaCosto(BaseModel):
    """Hoja de costo (HU-4.08) que calcula el servidor; el front solo da formato a los montos.

    `saldo_mayor_gtq` es el saldo de unidades en proceso del VIN, más el costo trasladado en el alta
    a la flota (`costo_alta_gtq`) cuando ya la tiene; `cuadra` compara el total con ese saldo.
    """

    vin: str
    marca: str
    linea: str
    modelo: int
    estado: str
    compra: CompraHojaCosto | None
    importacion: list[GastoHojaCosto]
    mano_obra: list[ManoObraHojaCosto]
    repuestos: list[RepuestoHojaCosto]
    compra_gtq: Decimal
    importacion_gtq: Decimal
    credito_fiscal_gtq: Decimal
    reacondicionamiento_gtq: Decimal
    total_gtq: Decimal
    saldo_mayor_gtq: Decimal
    costo_alta_gtq: Decimal | None
    diferencia_gtq: Decimal
    cuadra: bool

    @field_serializer(
        "compra_gtq", "importacion_gtq", "credito_fiscal_gtq", "reacondicionamiento_gtq", "total_gtq",
        "saldo_mayor_gtq", "diferencia_gtq",
    )  # fmt: skip
    def monto_a_texto(self, valor: Decimal) -> str:
        return _monto_texto(valor)

    @field_serializer("costo_alta_gtq")
    def costo_alta_a_texto(self, valor: Decimal | None) -> str | None:
        return None if valor is None else _monto_texto(valor)


# ── HU-4.13: programación y aprobación de pagos ───────────────────────────────

MontoTexto = Annotated[Decimal, PlainSerializer(_monto_texto, return_type=str)]
TipoCambioTexto = Annotated[Decimal, PlainSerializer(lambda valor: f"{valor:.8f}", return_type=str)]
OrigenCuentaPorPagar = Literal["factura", "gasto_importacion", "compra_unidad"]
EstadoPagoProgramado = Literal["propuesto", "aprobado", "rechazado", "ejecutado", "anulado"]


def _texto_monto(valor: object) -> object:
    if not isinstance(valor, str):
        raise ValueError('Los montos se envían como texto, por ejemplo "350.00"')
    return valor.strip()


class CuentaPorPagarPendiente(BaseModel):
    """Cuenta por pagar con saldo, con su documento de origen, para proponer pagos."""

    id: int
    proveedor_id: int
    proveedor: str
    origen: OrigenCuentaPorPagar
    documento: str
    vin: str | None
    fecha: date
    fecha_vencimiento: date
    dias_vencida: int  # negativo: faltan días para el vencimiento
    moneda: Moneda
    monto: MontoTexto
    saldo: MontoTexto
    programado: MontoTexto  # en un pago propuesto o aprobado que aún no se ejecuta


class PagoProgramadoEntrada(BaseModel):
    cuenta_por_pagar_id: int
    cuenta_bancaria_id: int
    monto: str  # en la moneda del documento; menor que el saldo es un pago parcial

    @field_validator("monto", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        return _texto_monto(valor)


class ProgramacionPagoEntrada(BaseModel):
    fecha: date
    descripcion: str | None = Field(default=None, max_length=300)
    pagos: list[PagoProgramadoEntrada]

    @field_validator("descripcion", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class DecisionPagoEntrada(BaseModel):
    """Aprobar (con monto o cuenta bancaria cambiados, si se modifica) o rechazar con su motivo."""

    accion: Literal["aprobar", "rechazar"]
    monto: str | None = None
    cuenta_bancaria_id: int | None = None
    comentario: str | None = Field(default=None, max_length=300)

    @field_validator("monto", mode="before")
    @classmethod
    def monto_como_texto(cls, valor: object) -> object:
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return None
        return _texto_monto(valor)

    @field_validator("comentario", mode="before")
    @classmethod
    def recortar_opcional(cls, valor: object) -> object:
        if isinstance(valor, str):
            return valor.strip() or None
        return valor


class PagoProgramadoSalida(BaseModel):
    id: int
    programacion_id: int
    cuenta_por_pagar_id: int
    proveedor_id: int
    proveedor: str
    documento: str
    vin: str | None
    fecha_vencimiento: date
    moneda: Moneda
    saldo: MontoTexto
    cuenta_bancaria_id: int
    banco: str
    moneda_banco: Moneda
    monto_propuesto: MontoTexto
    monto: MontoTexto
    # Lo que sale de la cuenta bancaria; si la moneda difiere, estimado con el último tipo de cambio.
    monto_banco: MontoTexto | None
    estado: EstadoPagoProgramado
    decidido_por: int | None
    decidido_en: datetime | None
    comentario: str | None


class SaldoBancoProgramacion(BaseModel):
    """Saldo disponible de una cuenta bancaria frente a lo que esta programación sacaría de ella."""

    cuenta_bancaria_id: int
    banco: str
    moneda: Moneda
    saldo_libros: MontoTexto
    comprometido: MontoTexto  # pagos aprobados de otras programaciones, aún sin ejecutar
    disponible: MontoTexto
    programado: MontoTexto  # pagos propuestos o aprobados de esta programación, sin ejecutar
    alcanza: bool


class ProgramacionPagoSalida(BaseModel):
    id: int
    fecha: date
    descripcion: str | None
    propuesta_por: int
    creado_en: datetime
    estado: Literal["pendiente", "revisada"]
    pagos: list[PagoProgramadoSalida]
    totales: dict[str, MontoTexto]  # por moneda de salida (GTQ y USD), sin los rechazados
    tipo_cambio_estimado: TipoCambioTexto | None
    bancos: list[SaldoBancoProgramacion]


# ── HU-4.14: pago a un proveedor ──────────────────────────────────────────────

FormaPago = Literal["cheque", "transferencia"]


class PagoProveedorEntrada(BaseModel):
    """Ejecuta pagos programados y aprobados (HU-4.13) de un mismo proveedor y cuenta bancaria."""

    cuenta_bancaria_id: int
    forma_pago: FormaPago
    referencia: str = Field(max_length=50)  # número de cheque o referencia de la transferencia
    fecha: date
    pagos_programados: list[int]

    @field_validator("referencia", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class AnulacionPagoEntrada(BaseModel):
    fecha: date
    motivo: str = Field(max_length=300)

    @field_validator("motivo", mode="before")
    @classmethod
    def recortar(cls, valor: object) -> object:
        return valor.strip() if isinstance(valor, str) else valor


class AplicacionPagoSalida(BaseModel):
    cuenta_por_pagar_id: int
    documento: str
    vin: str | None
    moneda_documento: Moneda
    monto_documento: MontoTexto
    monto_pago: MontoTexto
    tipo_cambio_libros: TipoCambioTexto | None
    diferencial: MontoTexto
    saldo_documento: MontoTexto


class PagoProveedorSalida(BaseModel):
    id: int
    proveedor_id: int
    proveedor: str
    cuenta_bancaria_id: int
    banco: str
    moneda: Moneda
    forma_pago: FormaPago
    referencia: str
    fecha: date
    tipo_cambio: TipoCambioTexto | None
    monto: MontoTexto
    diferencial: MontoTexto  # realizado, en quetzales: positivo ganancia, negativo pérdida
    estado: Literal["registrado", "anulado"]
    usuario_id: int | None
    anulado_por: int | None
    fecha_anulacion: date | None
    motivo_anulacion: str | None
    partida_numero: int | None
    reversion_numero: int | None
    creado_en: datetime
    aplicaciones: list[AplicacionPagoSalida]
