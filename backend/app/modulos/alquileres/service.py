"""Reglas del módulo de alquileres (equipo C).

HU-3.05 (Sprint 1, incluido): tarifas por modalidad (diaria, semanal, mensual o por kilometraje),
moneda, monto, kilometraje incluido, costo por kilómetro adicional y vigencia; por tipo de
vehículo y, como excepción, por unidad (VIN). Además:
- Temporadas: listas de precios con fechas que reemplazan a la lista base mientras están activas.
- Conceptos: cargos adicionales con su tratamiento fiscal (ingreso con o sin IVA, depósito,
  reintegro de gastos de terceros), para que la factura sepa qué grava.
- Cotización: aplica la tarifa vigente a la fecha de salida, convierte de moneda con el tipo de
  cambio del Banguat (HU-1.06) y separa base e IVA con la tasa del perfil fiscal (HU-1.01).

Reglas de la cotización:
- Los precios del tarifario incluyen IVA; base = total / (1 + tasa) y el IVA es la diferencia.
- La tarifa (y su temporada) se elige por la fecha de salida y aplica a todo el contrato.
- Orden de búsqueda: unidad en temporada, unidad, tipo en temporada, tipo; en cada nivel se
  prefiere la moneda pedida y, si no hay, se convierte la de la otra moneda.

Diferido: aprobación del gerente financiero para descuentos sobre el porcentaje configurado
(criterio 3). Criterio 4 (los contratos firmados no cambian) lo garantizan las tarifas en
versiones que no se modifican y el contrato (HU-3.06), que copia el precio al firmarse.
"""

import math
import re
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import a_decimal
from app.comun.errores import ErrorNegocio
from app.modulos.alquileres.models import ConceptoAlquiler, TarifaAlquiler, TemporadaAlquiler
from app.modulos.alquileres.schemas import (
    ConceptoCambio,
    ConceptoEntrada,
    CotizacionEntrada,
    TarifaEntrada,
    TemporadaEntrada,
)
from app.modulos.configuracion import service as configuracion

# Pendiente (HU-1.05): cuando exista el módulo `unidades`, el tipo de vehículo de cada unidad sale
# de ahí y este catálogo se mueve a ese módulo.
TIPOS_VEHICULO = ("sedan", "hatchback", "suv", "pickup", "microbus", "panel")

_VIN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")
_CENTAVO = Decimal("0.01")
_MAXIMO = Decimal("1000000000000")
_DIAS_POR_PERIODO = {"diaria": 1, "semanal": 7, "mensual": 30}


def _redondear(valor: Decimal) -> Decimal:
    return valor.quantize(_CENTAVO, rounding=ROUND_HALF_UP)


def _monto(texto: str | None, campo: str, permite_cero: bool = False) -> Decimal:
    try:
        valor = a_decimal((texto or "").strip())
    except (InvalidOperation, ValueError):
        raise ErrorNegocio(f"{campo} debe ser un número, por ejemplo 300.00") from None
    if not valor.is_finite() or valor < 0 or (valor == 0 and not permite_cero):
        raise ErrorNegocio(f"{campo} debe ser mayor que cero")
    # Los ceros a la derecha no cuentan: "25.000000" (como lo devuelve la API) es válido.
    if -valor.normalize().as_tuple().exponent > 2:
        raise ErrorNegocio(f"{campo} admite como máximo 2 decimales")
    if valor >= _MAXIMO:
        raise ErrorNegocio(f"{campo} es demasiado grande")
    return valor


def _tipo(tipo: str) -> str:
    tipo = tipo.lower()
    if tipo not in TIPOS_VEHICULO:
        raise ErrorNegocio(f"Tipo de vehículo desconocido: {tipo}. Use uno de: {', '.join(TIPOS_VEHICULO)}")
    return tipo


def _vin(texto: str) -> str:
    vin = texto.upper()
    if not _VIN.fullmatch(vin):
        raise ErrorNegocio("El VIN debe tener 17 caracteres, letras y números sin I, O ni Q")
    return vin


# ── Temporadas ─────────────────────────────────────────────────────────────────


def registrar_temporada(db: Session, datos: TemporadaEntrada) -> TemporadaAlquiler:
    if not datos.nombre:
        raise ErrorNegocio("El nombre de la temporada es obligatorio")
    if datos.fecha_fin < datos.fecha_inicio:
        raise ErrorNegocio("La fecha final de la temporada no puede ser anterior a la inicial")
    choque = db.scalar(
        select(TemporadaAlquiler).where(
            TemporadaAlquiler.activa,
            TemporadaAlquiler.fecha_inicio <= datos.fecha_fin,
            TemporadaAlquiler.fecha_fin >= datos.fecha_inicio,
        )
    )
    if choque is not None:
        raise ErrorNegocio(
            f"Las fechas se traslapan con la temporada «{choque.nombre}» "
            f"({choque.fecha_inicio:%d/%m/%Y} al {choque.fecha_fin:%d/%m/%Y})"
        )
    temporada = TemporadaAlquiler(
        nombre=datos.nombre, fecha_inicio=datos.fecha_inicio, fecha_fin=datos.fecha_fin, activa=True
    )
    db.add(temporada)
    db.commit()
    db.refresh(temporada)
    return temporada


def listar_temporadas(db: Session) -> list[TemporadaAlquiler]:
    return list(db.scalars(select(TemporadaAlquiler).order_by(TemporadaAlquiler.fecha_inicio.desc())))


def desactivar_temporada(db: Session, temporada_id: int) -> TemporadaAlquiler:
    """Una temporada desactivada deja de aplicar en las cotizaciones; sus tarifas se conservan."""
    temporada = db.get(TemporadaAlquiler, temporada_id)
    if temporada is None:
        raise ErrorNegocio(f"No existe la temporada {temporada_id}", status=404)
    temporada.activa = False
    db.commit()
    db.refresh(temporada)
    return temporada


def _temporada_en(db: Session, fecha: date) -> TemporadaAlquiler | None:
    return db.scalar(
        select(TemporadaAlquiler).where(
            TemporadaAlquiler.activa,
            TemporadaAlquiler.fecha_inicio <= fecha,
            TemporadaAlquiler.fecha_fin >= fecha,
        )
    )


# ── Tarifas ────────────────────────────────────────────────────────────────────


def _misma_tarifa(temporada_id, tipo, vin, modalidad, moneda):
    """Condición de "misma tarifa" (sin importar la vigencia); NULL se compara como valor."""
    return and_(
        TarifaAlquiler.temporada_id.is_not_distinct_from(temporada_id),
        TarifaAlquiler.tipo_vehiculo.is_not_distinct_from(tipo),
        TarifaAlquiler.vin.is_not_distinct_from(vin),
        TarifaAlquiler.modalidad == modalidad,
        TarifaAlquiler.moneda == moneda,
    )


def registrar_tarifa(db: Session, datos: TarifaEntrada) -> TarifaAlquiler:
    if (datos.tipo_vehiculo is None) == (datos.vin is None):
        raise ErrorNegocio("Indique el tipo de vehículo o, como excepción, el VIN de una unidad")
    tipo = _tipo(datos.tipo_vehiculo) if datos.tipo_vehiculo else None
    vin = _vin(datos.vin) if datos.vin else None

    if datos.temporada_id is not None:
        temporada = db.get(TemporadaAlquiler, datos.temporada_id)
        if temporada is None:
            raise ErrorNegocio(f"No existe la temporada {datos.temporada_id}", status=404)
        if not temporada.activa:
            raise ErrorNegocio(f"La temporada «{temporada.nombre}» está desactivada")

    monto = _monto(datos.monto, "El monto")
    costo = None
    if datos.costo_km_adicional is not None:
        costo = _monto(datos.costo_km_adicional, "El costo por kilómetro adicional", permite_cero=True)
    if datos.modalidad == "kilometraje" and (datos.km_incluido is None or costo is None):
        raise ErrorNegocio(
            "La tarifa por kilometraje requiere kilómetros incluidos y costo por kilómetro adicional"
        )
    if costo is not None and datos.km_incluido is None:
        raise ErrorNegocio("El costo por kilómetro adicional requiere indicar los kilómetros incluidos")

    misma = _misma_tarifa(datos.temporada_id, tipo, vin, datos.modalidad, datos.moneda)
    ultima = db.scalar(
        select(TarifaAlquiler.vigente_desde)
        .where(misma)
        .order_by(TarifaAlquiler.vigente_desde.desc())
        .limit(1)
    )
    if ultima is not None and datos.vigente_desde <= ultima:
        raise ErrorNegocio(
            f"La vigencia debe ser posterior a la de la tarifa actual ({ultima:%d/%m/%Y}): "
            "un cambio no altera las fechas que ya cubre otra versión"
        )

    tarifa = TarifaAlquiler(
        temporada_id=datos.temporada_id,
        tipo_vehiculo=tipo,
        vin=vin,
        modalidad=datos.modalidad,
        moneda=datos.moneda,
        monto=monto,
        km_incluido=datos.km_incluido,
        costo_km_adicional=costo,
        vigente_desde=datos.vigente_desde,
    )
    db.add(tarifa)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorNegocio(f"Ya existe esa tarifa vigente desde el {datos.vigente_desde:%d/%m/%Y}") from None
    db.refresh(tarifa)
    return tarifa


def listar_tarifas(
    db: Session,
    tipo_vehiculo: str | None = None,
    vin: str | None = None,
    temporada_id: int | None = None,
) -> list[TarifaAlquiler]:
    """Historial de tarifas: primero las por tipo y luego las por unidad, de la más reciente."""
    consulta = select(TarifaAlquiler).order_by(
        TarifaAlquiler.vin.is_not(None),
        TarifaAlquiler.tipo_vehiculo,
        TarifaAlquiler.vin,
        TarifaAlquiler.temporada_id.is_not(None),
        TarifaAlquiler.modalidad,
        TarifaAlquiler.moneda,
        TarifaAlquiler.vigente_desde.desc(),
    )
    if tipo_vehiculo:
        consulta = consulta.where(TarifaAlquiler.tipo_vehiculo == tipo_vehiculo.lower())
    if vin:
        consulta = consulta.where(TarifaAlquiler.vin == vin.strip().upper())
    if temporada_id is not None:
        consulta = consulta.where(TarifaAlquiler.temporada_id == temporada_id)
    return list(db.scalars(consulta))


def _tarifa_vigente(
    db: Session, fecha: date, temporada_id, tipo, vin, modalidad, moneda
) -> TarifaAlquiler | None:
    return db.scalar(
        select(TarifaAlquiler)
        .where(
            _misma_tarifa(temporada_id, tipo, vin, modalidad, moneda),
            TarifaAlquiler.vigente_desde <= fecha,
        )
        .order_by(TarifaAlquiler.vigente_desde.desc())
        .limit(1)
    )


def tarifa_aplicable(
    db: Session, tipo_vehiculo: str, vin: str | None, modalidad: str, moneda: str, fecha: date
) -> TarifaAlquiler:
    """La tarifa que aplica a un alquiler que sale en `fecha` (la usará el contrato, HU-3.06)."""
    tipo = _tipo(tipo_vehiculo)
    vin = _vin(vin) if vin else None
    temporada = _temporada_en(db, fecha)
    otra = "USD" if moneda == "GTQ" else "GTQ"
    alcances = []
    if vin:
        if temporada:
            alcances.append((temporada.id, None, vin))
        alcances.append((None, None, vin))
    if temporada:
        alcances.append((temporada.id, tipo, None))
    alcances.append((None, tipo, None))
    for temporada_id, tipo_alcance, vin_alcance in alcances:
        for moneda_busqueda in (moneda, otra):
            tarifa = _tarifa_vigente(
                db, fecha, temporada_id, tipo_alcance, vin_alcance, modalidad, moneda_busqueda
            )
            if tarifa is not None:
                return tarifa
    raise ErrorNegocio(
        f"No hay tarifa {modalidad} vigente al {fecha:%d/%m/%Y} para el tipo {tipo}", status=404
    )


# ── Conceptos ──────────────────────────────────────────────────────────────────


def _precio_y_moneda(precio: str | None, moneda: str | None) -> tuple[Decimal | None, str | None]:
    if (precio is None) != (moneda is None):
        raise ErrorNegocio("El precio sugerido y su moneda van juntos")
    return (_monto(precio, "El precio sugerido") if precio is not None else None), moneda


def registrar_concepto(db: Session, datos: ConceptoEntrada) -> ConceptoAlquiler:
    if not datos.nombre:
        raise ErrorNegocio("El nombre del concepto es obligatorio")
    if datos.aplica_iva and datos.naturaleza != "ingreso":
        raise ErrorNegocio("Solo un ingreso lleva IVA; un depósito o un reintegro no")
    precio, moneda = _precio_y_moneda(datos.precio_sugerido, datos.moneda)
    if db.scalar(select(ConceptoAlquiler.id).where(ConceptoAlquiler.nombre.ilike(datos.nombre))):
        raise ErrorNegocio(f"Ya existe el concepto «{datos.nombre}»", status=409)
    concepto = ConceptoAlquiler(
        nombre=datos.nombre,
        naturaleza=datos.naturaleza,
        aplica_iva=datos.aplica_iva,
        precio_sugerido=precio,
        moneda=moneda,
        activo=True,
    )
    db.add(concepto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ErrorNegocio(f"Ya existe el concepto «{datos.nombre}»", status=409) from None
    db.refresh(concepto)
    return concepto


def cambiar_concepto(db: Session, concepto_id: int, datos: ConceptoCambio) -> ConceptoAlquiler:
    """Cambia el precio sugerido o da de baja el concepto. El contrato copia el precio al firmarse,
    así que un cambio no toca contratos firmados; la bitácora guarda el precio anterior."""
    concepto = db.get(ConceptoAlquiler, concepto_id)
    if concepto is None:
        raise ErrorNegocio(f"No existe el concepto {concepto_id}", status=404)
    concepto.precio_sugerido, concepto.moneda = _precio_y_moneda(datos.precio_sugerido, datos.moneda)
    concepto.activo = datos.activo
    db.commit()
    db.refresh(concepto)
    return concepto


def listar_conceptos(db: Session, solo_activos: bool = False) -> list[ConceptoAlquiler]:
    consulta = select(ConceptoAlquiler).order_by(ConceptoAlquiler.naturaleza, ConceptoAlquiler.nombre)
    if solo_activos:
        consulta = consulta.where(ConceptoAlquiler.activo)
    return list(db.scalars(consulta))


# ── Cotización ─────────────────────────────────────────────────────────────────


class _Conversor:
    """Convierte montos a la moneda de la cotización con el tipo de cambio de la fecha de salida;
    lo consulta una sola vez y solo si hace falta."""

    def __init__(self, db: Session, moneda: str, fecha: date):
        self.db, self.moneda, self.fecha = db, moneda, fecha
        self.tipo_cambio: Decimal | None = None

    def __call__(self, monto: Decimal, moneda: str) -> Decimal:
        if moneda == self.moneda:
            return _redondear(monto)
        if self.tipo_cambio is None:
            try:
                self.tipo_cambio = configuracion.tipo_cambio_de(self.db, self.fecha)
            except ErrorNegocio:
                raise ErrorNegocio(
                    f"No hay tipo de cambio del {self.fecha:%d/%m/%Y} para convertir la tarifa a "
                    f"{self.moneda}; cárguelo en Tipo de cambio",
                    status=409,
                ) from None
        convertido = monto * self.tipo_cambio if moneda == "USD" else monto / self.tipo_cambio
        return _redondear(convertido)


def _linea(descripcion, naturaleza, aplica_iva, cantidad, precio, tasa_iva) -> dict:
    total = _redondear(precio * cantidad)
    if naturaleza == "ingreso" and aplica_iva:
        base = _redondear(total / (1 + tasa_iva))
        iva = total - base
    else:
        base, iva = total, Decimal("0.00")
    return {
        "descripcion": descripcion,
        "naturaleza": naturaleza,
        "aplica_iva": aplica_iva,
        "cantidad": Decimal(cantidad),
        "precio_unitario": precio,
        "total": total,
        "base": base,
        "iva": iva,
    }


def cotizar(db: Session, datos: CotizacionEntrada) -> dict:
    """Monto estimado de un alquiler con sus cargos, separado por naturaleza fiscal."""
    if datos.fecha_devolucion < datos.fecha_salida:
        raise ErrorNegocio("La fecha de devolución no puede ser anterior a la de salida")
    dias = max(1, (datos.fecha_devolucion - datos.fecha_salida).days)
    tarifa = tarifa_aplicable(
        db, datos.tipo_vehiculo, datos.vin, datos.modalidad, datos.moneda, datos.fecha_salida
    )
    if datos.modalidad == "kilometraje":
        if datos.km_estimados is None:
            raise ErrorNegocio("Indique los kilómetros estimados para cotizar por kilometraje")
        periodos = 1
    else:
        periodos = math.ceil(dias / _DIAS_POR_PERIODO[datos.modalidad])

    convertir = _Conversor(db, datos.moneda, datos.fecha_salida)
    tasa_iva = configuracion.tasa_vigente(db, "IVA_GENERAL", datos.fecha_salida).tasa
    unidad = {"diaria": "día", "semanal": "semana", "mensual": "mes", "kilometraje": "contrato"}
    nombre = f"Alquiler {datos.modalidad} · {tarifa.vin or tarifa.tipo_vehiculo}"
    if tarifa.temporada is not None:
        nombre += f" · {tarifa.temporada.nombre}"
    lineas = [
        _linea(
            f"{nombre} (por {unidad[datos.modalidad]})",
            "ingreso",
            True,
            periodos,
            convertir(tarifa.monto, tarifa.moneda),
            tasa_iva,
        )
    ]

    if tarifa.km_incluido is not None and tarifa.costo_km_adicional is not None and datos.km_estimados:
        permitidos = tarifa.km_incluido * periodos
        exceso = datos.km_estimados - permitidos
        if exceso > 0:
            lineas.append(
                _linea(
                    f"Kilometraje adicional (incluye {permitidos} km)",
                    "ingreso",
                    True,
                    exceso,
                    convertir(tarifa.costo_km_adicional, tarifa.moneda),
                    tasa_iva,
                )
            )

    for cargo in datos.cargos:
        concepto = db.get(ConceptoAlquiler, cargo.concepto_id)
        if concepto is None or not concepto.activo:
            raise ErrorNegocio(f"El concepto {cargo.concepto_id} no existe o está dado de baja")
        if concepto.precio_sugerido is not None:
            if cargo.precio is not None:
                raise ErrorNegocio(
                    f"«{concepto.nombre}» tiene precio en el tarifario; un precio distinto se "
                    "negocia en el contrato"
                )
            precio = convertir(concepto.precio_sugerido, concepto.moneda)
        else:
            if cargo.precio is None:
                raise ErrorNegocio(
                    f"Indique el monto de «{concepto.nombre}»: no tiene precio en el tarifario"
                )
            precio = _monto(cargo.precio, f"El monto de «{concepto.nombre}»")
        lineas.append(
            _linea(
                concepto.nombre, concepto.naturaleza, concepto.aplica_iva, cargo.cantidad, precio, tasa_iva
            )
        )

    def suma(campo: str, naturaleza: str | None = None) -> Decimal:
        return sum(
            (linea[campo] for linea in lineas if naturaleza is None or linea["naturaleza"] == naturaleza),
            Decimal("0.00"),
        )

    return {
        "moneda": datos.moneda,
        "tarifa": tarifa,
        "periodos": periodos,
        "dias": dias,
        "tipo_cambio": convertir.tipo_cambio,
        "tasa_iva": tasa_iva,
        "lineas": lineas,
        "total_ingresos": suma("total", "ingreso"),
        "total_base": suma("base", "ingreso"),
        "total_iva": suma("iva", "ingreso"),
        "total_depositos": suma("total", "deposito"),
        "total_reintegros": suma("total", "reintegro"),
        "total_a_pagar": suma("total"),
    }
