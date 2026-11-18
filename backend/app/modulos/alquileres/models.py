"""Tablas del módulo de alquileres (Sprint 2: tarifario, HU-3.05; contratos, HU-3.06 y HU-3.08;
depósitos en garantía, HU-3.07)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.comun.db import Base
from app.comun.dinero import MONTO

MODALIDADES = ("diaria", "semanal", "mensual", "por_kilometraje")


class Tarifa(Base):
    """Tarifa de alquiler de un tipo de vehículo o, como excepción, de una unidad (VIN).

    Nunca se edita el monto: un cambio es otra tarifa con su propia vigencia, y la anterior se
    cierra (`vigente_hasta`). El contrato copia los valores al firmarse, así que no se altera.
    """

    __tablename__ = "tarifa"
    __table_args__ = (
        CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')", name="ck_tarifa_modalidad"
        ),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_tarifa_moneda"),
        CheckConstraint(
            "(tipo_vehiculo IS NOT NULL AND vin IS NULL) OR (tipo_vehiculo IS NULL AND vin IS NOT NULL)",
            name="ck_tarifa_aplica_a",
        ),
        CheckConstraint(
            "monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0", name="ck_tarifa_montos"
        ),
        CheckConstraint("vigente_hasta IS NULL OR vigente_hasta >= vigente_desde", name="ck_tarifa_vigencia"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_vehiculo: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    vin: Mapped[str | None] = mapped_column(ForeignKey("unidad.vin"), nullable=True, index=True)
    modalidad: Mapped[str] = mapped_column(String(20))
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    km_incluido: Mapped[int] = mapped_column(Integer, default=0)
    precio_km_adicional: Mapped[Decimal] = mapped_column(MONTO)
    vigente_desde: Mapped[date] = mapped_column(Date)
    vigente_hasta: Mapped[date | None] = mapped_column(Date, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContratoAlquiler(Base):
    """Contrato de alquiler de una unidad (VIN) a un cliente.

    Copia los valores de la tarifa vigente el día de salida (`tarifa_*`, `km_incluido`,
    `precio_km_adicional`): un cambio posterior del tarifario no lo altera. `tarifa_id` queda solo
    como referencia. El combustible se mide en octavos de tanque (0 a 8).
    """

    __tablename__ = "contrato_alquiler"
    __table_args__ = (
        CheckConstraint("estado IN ('abierto', 'cerrado')", name="ck_contrato_alquiler_estado"),
        CheckConstraint(
            "modalidad IN ('diaria', 'semanal', 'mensual', 'por_kilometraje')",
            name="ck_contrato_alquiler_modalidad",
        ),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_contrato_alquiler_moneda"),
        CheckConstraint(
            "combustible_salida BETWEEN 0 AND 8 AND km_salida >= 0", name="ck_contrato_alquiler_salida"
        ),
        CheckConstraint(
            "tarifa_monto > 0 AND precio_km_adicional >= 0 AND km_incluido >= 0 AND deposito_esperado >= 0"
            " AND dias_previstos >= 1 AND monto_estimado > 0",
            name="ck_contrato_alquiler_montos",
        ),
        CheckConstraint(
            "estado = 'abierto' OR (devolucion IS NOT NULL AND km_devolucion >= km_salida"
            " AND combustible_devolucion BETWEEN 0 AND 8 AND dias_efectivos >= 1 AND km_recorridos >= 0"
            " AND km_excedentes >= 0 AND combustible_faltante >= 0 AND monto_final > 0)",
            name="ck_contrato_alquiler_cierre",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(Integer, unique=True)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("cliente.id"), index=True)
    vin: Mapped[str] = mapped_column(ForeignKey("unidad.vin"), index=True)
    salida: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    devolucion_prevista: Mapped[date] = mapped_column(Date)
    tarifa_id: Mapped[int] = mapped_column(ForeignKey("tarifa.id"))
    modalidad: Mapped[str] = mapped_column(String(20))
    moneda: Mapped[str] = mapped_column(String(3))
    tarifa_monto: Mapped[Decimal] = mapped_column(MONTO)
    km_incluido: Mapped[int] = mapped_column(Integer)
    precio_km_adicional: Mapped[Decimal] = mapped_column(MONTO)
    km_salida: Mapped[int] = mapped_column(Integer)
    combustible_salida: Mapped[int] = mapped_column(SmallInteger)
    deposito_esperado: Mapped[Decimal] = mapped_column(MONTO)
    dias_previstos: Mapped[int] = mapped_column(Integer)
    monto_estimado: Mapped[Decimal] = mapped_column(MONTO)
    estado: Mapped[str] = mapped_column(String(10), default="abierto", index=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # HU-3.08: devolución y cálculo del cierre; vacíos mientras el contrato está abierto.
    devolucion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    km_devolucion: Mapped[int | None] = mapped_column(Integer, nullable=True)
    combustible_devolucion: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    observaciones_danos: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    dias_efectivos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    km_recorridos: Mapped[int | None] = mapped_column(Integer, nullable=True)
    km_excedentes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    combustible_faltante: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    monto_final: Mapped[Decimal | None] = mapped_column(MONTO, nullable=True)
    cerrado_por: Mapped[int | None] = mapped_column(Integer, nullable=True)


class DepositoGarantia(Base):
    """Depósito en garantía de un contrato, en la moneda en que se recibió.

    Un depósito en dinero entra a una cuenta bancaria y es pasivo; su `saldo` baja con cada
    aplicación a cargos o devolución. Una autorización de tarjeta sin cobro es solo referencia:
    sin cuenta bancaria, sin partida y con saldo cero.
    """

    __tablename__ = "deposito_garantia"
    __table_args__ = (
        CheckConstraint("tipo IN ('deposito', 'autorizacion_tarjeta')", name="ck_deposito_garantia_tipo"),
        CheckConstraint("moneda IN ('GTQ', 'USD')", name="ck_deposito_garantia_moneda"),
        CheckConstraint("monto > 0 AND saldo >= 0 AND saldo <= monto", name="ck_deposito_garantia_saldo"),
        CheckConstraint(
            "(tipo = 'deposito' AND cuenta_bancaria_id IS NOT NULL)"
            " OR (tipo = 'autorizacion_tarjeta' AND cuenta_bancaria_id IS NULL AND referencia IS NOT NULL"
            " AND saldo = 0)",
            name="ck_deposito_garantia_forma",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contrato_alquiler.id"), index=True)
    vin: Mapped[str] = mapped_column(ForeignKey("unidad.vin"))
    tipo: Mapped[str] = mapped_column(String(25))
    fecha: Mapped[date] = mapped_column(Date)
    moneda: Mapped[str] = mapped_column(String(3))
    monto: Mapped[Decimal] = mapped_column(MONTO)
    saldo: Mapped[Decimal] = mapped_column(MONTO)
    cuenta_bancaria_id: Mapped[int | None] = mapped_column(ForeignKey("cuenta_bancaria.id"), nullable=True)
    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contrato: Mapped[ContratoAlquiler] = relationship(lazy="joined", innerjoin=True)
    movimientos: Mapped[list["MovimientoDeposito"]] = relationship(
        lazy="selectin", order_by="MovimientoDeposito.id"
    )

    @property
    def contrato_numero(self) -> int:
        return self.contrato.numero

    @property
    def devuelto(self) -> bool:
        return any(m.tipo == "devolucion" for m in self.movimientos)


class MovimientoDeposito(Base):
    """Aplicación del depósito a los cargos del contrato o su devolución al cliente (una sola)."""

    __tablename__ = "movimiento_deposito"
    __table_args__ = (
        CheckConstraint("tipo IN ('aplicacion', 'devolucion')", name="ck_movimiento_deposito_tipo"),
        CheckConstraint("monto > 0", name="ck_movimiento_deposito_monto"),
        CheckConstraint(
            "tipo = 'aplicacion' OR cuenta_bancaria_id IS NOT NULL", name="ck_movimiento_deposito_banco"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    deposito_id: Mapped[int] = mapped_column(ForeignKey("deposito_garantia.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(15))
    fecha: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(MONTO)
    cuenta_bancaria_id: Mapped[int | None] = mapped_column(ForeignKey("cuenta_bancaria.id"), nullable=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
