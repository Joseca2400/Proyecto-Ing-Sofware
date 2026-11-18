"""Reglas del módulo de taller (Sprint 2, versión delgada).

HU-5.02 (incluido): tarifa horaria de costo general en quetzales con vigencia. Un cambio es una
fila nueva y aplica solo a las horas con fecha igual o posterior a su `vigente_desde` (criterio 3).
HU-5.02 (diferido): tarifa por mecánico o especialidad (criterio 1) y tarifa de venta para la
postventa facturable (criterio 2), con la postventa (Sprint 5).

HU-5.01 (incluido): orden con número correlativo (su id), VIN de una unidad registrada, tipo de
trabajo, fecha, kilometraje, descripción y responsable. Solo existe el tipo `reacondicionamiento`:
se abre únicamente para una unidad en aduana o ya en taller de la importación y la pasa a "en
taller" (`unidades.cambiar_estado`, en la misma transacción); una sola orden abierta por unidad.
HU-5.01 (diferido): ligar la postventa al comprador y a la venta (criterio 4), ligar la orden a
un contrato de alquiler (criterio 5) y los demás tipos de trabajo (Sprints 5 y 6).
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.modulos.taller.models import OrdenTrabajo, TarifaManoObra
from app.modulos.taller.schemas import OrdenEntrada, TarifaEntrada
from app.modulos.unidades import service as unidades

_LIMITE_MONTO = Decimal(10) ** 12


def _monto(texto: str, campo: str) -> Decimal:
    """Número positivo enviado como texto, con hasta 6 decimales; nunca float."""
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio(f"{campo} no es un número válido") from None
    if not valor.is_finite():
        raise ErrorNegocio(f"{campo} no es un número válido")
    if -valor.as_tuple().exponent > 6:  # type: ignore[operator]
        raise ErrorNegocio(f"{campo} admite hasta 6 decimales")
    if valor <= 0:
        raise ErrorNegocio(f"{campo} debe ser mayor que cero")
    if valor >= _LIMITE_MONTO:
        raise ErrorNegocio(f"{campo} excede el máximo permitido")
    return valor


# ── HU-5.02: tarifas de mano de obra ──────────────────────────────────────────


def crear_tarifa(db: Session, datos: TarifaEntrada, usuario_id: int | None = None) -> TarifaManoObra:
    tarifa_hora = _monto(datos.tarifa_hora, "La tarifa por hora")
    if db.scalar(select(TarifaManoObra.id).where(TarifaManoObra.vigente_desde == datos.vigente_desde)):
        raise ErrorNegocio(f"Ya existe una tarifa vigente desde el {datos.vigente_desde}", 409)
    tarifa = TarifaManoObra(tarifa_hora=tarifa_hora, vigente_desde=datos.vigente_desde, creado_por=usuario_id)
    db.add(tarifa)
    db.commit()
    db.refresh(tarifa)
    return tarifa


def listar_tarifas(db: Session) -> list[TarifaManoObra]:
    """De la vigencia más reciente a la más antigua."""
    return list(db.scalars(select(TarifaManoObra).order_by(TarifaManoObra.vigente_desde.desc())))


def tarifa_costo_vigente(db: Session, fecha: date) -> Decimal:
    """Tarifa horaria de costo en vigor en `fecha` (la de `vigente_desde` más reciente hasta ella)."""
    tarifa = db.scalar(
        select(TarifaManoObra.tarifa_hora)
        .where(TarifaManoObra.vigente_desde <= fecha)
        .order_by(TarifaManoObra.vigente_desde.desc())
        .limit(1)
    )
    if tarifa is None:
        raise ErrorNegocio(
            f"No hay tarifa de mano de obra vigente al {fecha}: defínala en las tarifas de taller", 409
        )
    return tarifa


# ── HU-5.01: órdenes de trabajo ───────────────────────────────────────────────

_ESTADOS_PARA_REACONDICIONAR = ("en_aduana", "en_taller")


def abrir_orden(db: Session, datos: OrdenEntrada, usuario_id: int | None = None) -> OrdenTrabajo:
    """Abre la orden y pasa la unidad a "en taller" en una transacción, o no guarda nada."""
    unidad = unidades.obtener_por_vin(db, datos.vin)
    if datos.fecha_apertura > date.today():
        raise ErrorNegocio("La fecha de apertura no puede ser futura")
    # En taller solo cuenta el de la importación: el de una unidad de flota es mantenimiento.
    if unidad.estado not in _ESTADOS_PARA_REACONDICIONAR or not unidades.esta_en_importacion(db, unidad.vin):
        raise ErrorNegocio(
            "Una orden de reacondicionamiento se abre para una unidad en aduana o en taller de la "
            f"importación; la unidad {unidad.vin} está {unidad.estado}"
        )
    if db.scalar(
        select(OrdenTrabajo.id).where(OrdenTrabajo.vin == unidad.vin, OrdenTrabajo.estado == "abierta")
    ):
        raise ErrorNegocio(f"La unidad {unidad.vin} ya tiene una orden de trabajo abierta", 409)
    orden = OrdenTrabajo(
        vin=unidad.vin,
        tipo=datos.tipo,
        fecha_apertura=datos.fecha_apertura,
        kilometraje=datos.kilometraje,
        descripcion=datos.descripcion,
        responsable=datos.responsable,
        abierta_por=usuario_id,
    )
    db.add(orden)
    try:
        db.flush()  # el id es el número de la orden y el documento del cambio de estado
        if unidad.estado == "en_aduana":
            unidades.cambiar_estado(
                db, unidad.vin, "en_taller", f"Orden de trabajo {orden.numero}", usuario_id, confirmar=False
            )
        db.commit()
    except IntegrityError:  # dos aperturas simultáneas: gana el índice único de órdenes abiertas
        db.rollback()
        raise ErrorNegocio(f"La unidad {unidad.vin} ya tiene una orden de trabajo abierta", 409) from None
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(orden)
    return orden


def listar_ordenes(db: Session, estado: str | None = None, vin: str | None = None) -> list[OrdenTrabajo]:
    """De la más reciente a la más antigua, opcionalmente solo las abiertas o cerradas o las de un VIN."""
    consulta = select(OrdenTrabajo).order_by(OrdenTrabajo.id.desc())
    if estado:
        consulta = consulta.where(OrdenTrabajo.estado == estado)
    if vin and vin.strip():
        consulta = consulta.where(OrdenTrabajo.vin == vin.strip().upper())
    return list(db.scalars(consulta))


def obtener_orden(db: Session, orden_id: int) -> OrdenTrabajo:
    orden = db.get(OrdenTrabajo, orden_id)
    if orden is None:
        raise ErrorNegocio(f"No existe la orden de trabajo {orden_id}", 404)
    return orden
