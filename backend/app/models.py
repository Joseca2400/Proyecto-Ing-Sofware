"""Modelo de datos del corte transversal.

Épicas: E1 Configuración, multimoneda y seguridad · E2 Contabilidad · E3 Flota y alquileres ·
E4 Importación y CxP · E5 Taller · E6 Facturación y CxC · E7 Reportes.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def ahora() -> datetime:
    return datetime.now(timezone.utc)


class Decimal6(TypeDecorator):
    """Decimal exacto: NUMERIC en PostgreSQL, texto en SQLite (sin pérdida por flotantes)."""

    impl = Numeric(18, 6)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(40))
        return dialect.type_descriptor(Numeric(18, 6))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        value = Decimal(value)
        return str(value) if dialect.name == "sqlite" else value

    def process_result_value(self, value, dialect):
        return None if value is None else Decimal(value)


# ======================================================================= Catálogos

class Rol(StrEnum):
    AUXILIAR = "AUXILIAR"          # registra
    CONTADOR = "CONTADOR"          # revisa, contabiliza y cierra
    GERENTE_FINANCIERO = "GERENTE_FINANCIERO"  # aprueba
    GERENCIA = "GERENCIA"          # solo consulta reportes


class Moneda(StrEnum):
    GTQ = "GTQ"
    USD = "USD"


class LineaNegocio(StrEnum):
    ALQUILER = "ALQUILER"
    VENTA = "VENTA"
    TALLER = "TALLER"
    FINANCIAMIENTO = "FINANCIAMIENTO"
    ADMINISTRACION = "ADMINISTRACION"


class ExigenciaVin(StrEnum):
    OBLIGATORIO = "OBLIGATORIO"
    OPCIONAL = "OPCIONAL"
    NO_APLICA = "NO_APLICA"


class EstadoUnidad(StrEnum):
    EN_TRANSITO = "EN_TRANSITO"
    EN_ADUANA = "EN_ADUANA"
    EN_TALLER = "EN_TALLER"
    LISTA = "LISTA"
    EN_FLOTA = "EN_FLOTA"
    EN_VENTA = "EN_VENTA"
    VENDIDA = "VENDIDA"
    RECUPERADA = "RECUPERADA"


class EstadoPartida(StrEnum):
    BORRADOR = "BORRADOR"
    EN_REVISION = "EN_REVISION"
    CONTABILIZADA = "CONTABILIZADA"
    DEVUELTA = "DEVUELTA"


# ======================================================================= E1

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(40), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    rol: Mapped[str] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    password_hash: Mapped[str] = mapped_column(String(200))  # nunca se audita ni se expone


class SesionUsuario(Base):
    """Sesión iniciada con usuario y contraseña. Se guarda el hash del token, no el token."""

    __tablename__ = "sesiones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cerrada: Mapped[bool] = mapped_column(Boolean, default=False)

    usuario: Mapped[Usuario] = relationship()


class Bitacora(Base):
    """HU-1.11: registro inmutable de acciones."""

    __tablename__ = "bitacora"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    usuario: Mapped[str] = mapped_column(String(40))
    accion: Mapped[str] = mapped_column(String(40))
    entidad: Mapped[str] = mapped_column(String(40))
    entidad_id: Mapped[int | None] = mapped_column(Integer)
    vin: Mapped[str | None] = mapped_column(String(17))
    detalle: Mapped[str | None] = mapped_column(Text)
    valores_anteriores: Mapped[str | None] = mapped_column(Text)  # JSON
    valores_nuevos: Mapped[str | None] = mapped_column(Text)      # JSON


class Cuenta(Base):
    """HU-1.02 y HU-1.04: cuenta contable con sus reglas de dimensiones."""

    __tablename__ = "cuentas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(20))          # ACTIVO, PASIVO, PATRIMONIO, INGRESO, COSTO, GASTO
    naturaleza: Mapped[str] = mapped_column(String(10))    # DEUDORA / ACREEDORA
    es_detalle: Mapped[bool] = mapped_column(Boolean, default=True)
    monetaria_usd: Mapped[bool] = mapped_column(Boolean, default=False)
    exige_vin: Mapped[str] = mapped_column(String(15), default=ExigenciaVin.NO_APLICA)
    linea_defecto: Mapped[str | None] = mapped_column(String(20))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class TipoCambio(Base):
    """HU-1.06: tipo de cambio de referencia del Banguat por fecha (Q por USD)."""

    __tablename__ = "tipos_cambio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha: Mapped[date] = mapped_column(Date, unique=True)
    valor: Mapped[Decimal] = mapped_column(Decimal6)
    origen: Mapped[str] = mapped_column(String(15), default="MANUAL")
    registrado_por: Mapped[str] = mapped_column(String(40))


class Unidad(Base):
    """HU-1.05: vehículo identificado por su VIN."""

    __tablename__ = "unidades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vin: Mapped[str] = mapped_column(String(17), unique=True)
    marca: Mapped[str] = mapped_column(String(40))
    linea: Mapped[str] = mapped_column(String(40))
    modelo_anio: Mapped[int] = mapped_column(Integer)
    color: Mapped[str | None] = mapped_column(String(30))
    tipo_vehiculo: Mapped[str | None] = mapped_column(String(30))
    placa: Mapped[str | None] = mapped_column(String(15))
    estado: Mapped[str] = mapped_column(String(20))
    kilometraje: Mapped[int] = mapped_column(Integer, default=0)
    fecha_alta_flota: Mapped[date | None] = mapped_column(Date)
    costo_alta: Mapped[Decimal | None] = mapped_column(Decimal6)
    vida_util_meses: Mapped[int | None] = mapped_column(Integer)
    valor_residual: Mapped[Decimal | None] = mapped_column(Decimal6)

    historial: Mapped[list["HistorialEstado"]] = relationship(
        back_populates="unidad", order_by="HistorialEstado.id", cascade="all, delete-orphan"
    )


class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    estado_anterior: Mapped[str | None] = mapped_column(String(20))
    estado_nuevo: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    usuario: Mapped[str] = mapped_column(String(40))
    documento: Mapped[str] = mapped_column(String(60))

    unidad: Mapped[Unidad] = relationship(back_populates="historial")


# ======================================================================= E2

class Partida(Base):
    __tablename__ = "partidas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[int | None] = mapped_column(Integer, unique=True)  # correlativo al contabilizar
    fecha: Mapped[date] = mapped_column(Date)
    concepto: Mapped[str] = mapped_column(String(250))
    estado: Mapped[str] = mapped_column(String(20), default=EstadoPartida.BORRADOR)
    automatica: Mapped[bool] = mapped_column(Boolean, default=False)
    origen_tipo: Mapped[str | None] = mapped_column(String(30))
    origen_id: Mapped[int | None] = mapped_column(Integer)
    registrada_por: Mapped[str] = mapped_column(String(40))
    contabilizada_por: Mapped[str | None] = mapped_column(String(40))
    comentario_revision: Mapped[str | None] = mapped_column(Text)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    lineas: Mapped[list["LineaPartida"]] = relationship(
        back_populates="partida", order_by="LineaPartida.id", cascade="all, delete-orphan"
    )


class LineaPartida(Base):
    __tablename__ = "lineas_partida"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partida_id: Mapped[int] = mapped_column(ForeignKey("partidas.id", ondelete="CASCADE"))
    cuenta_id: Mapped[int] = mapped_column(ForeignKey("cuentas.id"))
    debe: Mapped[Decimal] = mapped_column(Decimal6, default=Decimal("0"))   # en quetzales
    haber: Mapped[Decimal] = mapped_column(Decimal6, default=Decimal("0"))  # en quetzales
    moneda: Mapped[str] = mapped_column(String(3), default=Moneda.GTQ)
    monto_original: Mapped[Decimal | None] = mapped_column(Decimal6)        # en USD si aplica
    tipo_cambio: Mapped[Decimal | None] = mapped_column(Decimal6)
    linea_negocio: Mapped[str] = mapped_column(String(20))
    unidad_id: Mapped[int | None] = mapped_column(ForeignKey("unidades.id"))
    detalle: Mapped[str | None] = mapped_column(String(120))

    partida: Mapped[Partida] = relationship(back_populates="lineas")
    cuenta: Mapped[Cuenta] = relationship()
    unidad: Mapped[Unidad | None] = relationship()


# ======================================================================= E4

class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo: Mapped[str] = mapped_column(String(10))  # LOCAL / EXTERIOR
    nit: Mapped[str | None] = mapped_column(String(20), unique=True)
    pais: Mapped[str] = mapped_column(String(40), default="Guatemala")
    rubro: Mapped[str] = mapped_column(String(30))
    moneda: Mapped[str] = mapped_column(String(3))


class DocumentoPorPagar(Base):
    __tablename__ = "documentos_por_pagar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(ForeignKey("proveedores.id"))
    tipo: Mapped[str] = mapped_column(String(30))  # COMPRA_UNIDAD / GASTO_IMPORTACION
    referencia: Mapped[str | None] = mapped_column(String(60))
    fecha: Mapped[date] = mapped_column(Date)
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(Decimal6)
    saldo: Mapped[Decimal] = mapped_column(Decimal6)
    tipo_cambio: Mapped[Decimal | None] = mapped_column(Decimal6)
    unidad_id: Mapped[int | None] = mapped_column(ForeignKey("unidades.id"))
    partida_id: Mapped[int | None] = mapped_column(ForeignKey("partidas.id"))

    proveedor: Mapped[Proveedor] = relationship()


class GastoImportacion(Base):
    __tablename__ = "gastos_importacion"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    concepto: Mapped[str] = mapped_column(String(30))
    documento_id: Mapped[int] = mapped_column(ForeignKey("documentos_por_pagar.id"))


# ======================================================================= E5

class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    tipo: Mapped[str] = mapped_column(String(30))  # REACONDICIONAMIENTO / MANTENIMIENTO
    descripcion: Mapped[str] = mapped_column(Text)
    responsable: Mapped[str] = mapped_column(String(80))
    kilometraje: Mapped[int] = mapped_column(Integer, default=0)
    fecha_apertura: Mapped[date] = mapped_column(Date)
    fecha_cierre: Mapped[date | None] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(10), default="ABIERTA")
    justificacion_cero: Mapped[str | None] = mapped_column(Text)
    partida_id: Mapped[int | None] = mapped_column(ForeignKey("partidas.id"))

    unidad: Mapped[Unidad] = relationship()
    mano_obra: Mapped[list["ManoObra"]] = relationship(
        back_populates="orden", order_by="ManoObra.id", cascade="all, delete-orphan"
    )


class ManoObra(Base):
    __tablename__ = "mano_obra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orden_id: Mapped[int] = mapped_column(ForeignKey("ordenes_trabajo.id"))
    mecanico: Mapped[str] = mapped_column(String(80))
    fecha: Mapped[date] = mapped_column(Date)
    horas: Mapped[Decimal] = mapped_column(Decimal6)
    tarifa: Mapped[Decimal] = mapped_column(Decimal6)
    costo: Mapped[Decimal] = mapped_column(Decimal6)
    descripcion: Mapped[str] = mapped_column(String(200))

    orden: Mapped[OrdenTrabajo] = relationship(back_populates="mano_obra")


# ======================================================================= E6

class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(15))  # INDIVIDUAL / EMPRESA
    nombre: Mapped[str] = mapped_column(String(150))
    nit: Mapped[str | None] = mapped_column(String(20), unique=True)
    cui: Mapped[str | None] = mapped_column(String(13), unique=True)
    pasaporte: Mapped[str | None] = mapped_column(String(30), unique=True)
    pais: Mapped[str] = mapped_column(String(40), default="Guatemala")
    direccion: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(30))
    correo: Mapped[str | None] = mapped_column(String(120))


class Factura(Base):
    __tablename__ = "facturas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))  # None = Consumidor Final
    fecha: Mapped[date] = mapped_column(Date)
    moneda: Mapped[str] = mapped_column(String(3))
    tipo_cambio: Mapped[Decimal | None] = mapped_column(Decimal6)
    base: Mapped[Decimal] = mapped_column(Decimal6)
    iva: Mapped[Decimal] = mapped_column(Decimal6)
    total: Mapped[Decimal] = mapped_column(Decimal6)
    total_q: Mapped[Decimal] = mapped_column(Decimal6)
    saldo: Mapped[Decimal] = mapped_column(Decimal6)          # en la moneda de la factura
    descripcion: Mapped[str] = mapped_column(String(250))
    linea_negocio: Mapped[str] = mapped_column(String(20))
    unidad_id: Mapped[int | None] = mapped_column(ForeignKey("unidades.id"))
    origen_tipo: Mapped[str] = mapped_column(String(20))
    origen_id: Mapped[int] = mapped_column(Integer)
    # Datos de certificación FEL (simulados hasta elegir certificador)
    serie: Mapped[str] = mapped_column(String(20))
    numero_dte: Mapped[int] = mapped_column(Integer)
    autorizacion: Mapped[str] = mapped_column(String(40), unique=True)
    simulada: Mapped[bool] = mapped_column(Boolean, default=True)
    partida_id: Mapped[int | None] = mapped_column(ForeignKey("partidas.id"))

    cliente: Mapped[Cliente | None] = relationship()


class Cobro(Base):
    __tablename__ = "cobros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(ForeignKey("facturas.id"))
    fecha: Mapped[date] = mapped_column(Date)
    forma: Mapped[str] = mapped_column(String(20))
    monto: Mapped[Decimal] = mapped_column(Decimal6)          # en la moneda de la factura
    tipo_cambio: Mapped[Decimal | None] = mapped_column(Decimal6)
    diferencial_q: Mapped[Decimal] = mapped_column(Decimal6, default=Decimal("0"))
    referencia: Mapped[str | None] = mapped_column(String(60))
    partida_id: Mapped[int | None] = mapped_column(ForeignKey("partidas.id"))


# ======================================================================= E3

class Contrato(Base):
    __tablename__ = "contratos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.id"))
    unidad_id: Mapped[int] = mapped_column(ForeignKey("unidades.id"))
    fecha_salida: Mapped[date] = mapped_column(Date)
    fecha_prevista: Mapped[date] = mapped_column(Date)
    fecha_devolucion: Mapped[date | None] = mapped_column(Date)
    tarifa_diaria: Mapped[Decimal] = mapped_column(Decimal6)  # IVA incluido
    moneda: Mapped[str] = mapped_column(String(3))
    km_salida: Mapped[int] = mapped_column(Integer)
    km_entrada: Mapped[int | None] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(10), default="ACTIVO")  # ACTIVO / CERRADO
    observaciones: Mapped[str | None] = mapped_column(Text)
    registrado_por: Mapped[str] = mapped_column(String(40))

    cliente: Mapped[Cliente] = relationship()
    unidad: Mapped[Unidad] = relationship()
