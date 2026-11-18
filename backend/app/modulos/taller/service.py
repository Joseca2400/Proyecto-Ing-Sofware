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

HU-5.03 (incluido): horas por mecánico (nombre), fecha, horas (hasta 24 por registro y 2
decimales) y tarea; el costo es horas por la tarifa vigente en la fecha de las horas, redondeado
a centavos, y se guarda con su tarifa. No se registran horas en una orden cerrada ni anteriores a
su apertura. El crédito a "mano de obra aplicada" (criterio 3) lo genera el cierre (HU-5.07).
HU-5.03 (diferido): comparar al cierre de mes lo aplicado con el costo real del taller (criterio 3).

HU-5.07 (incluido): cerrar una orden de reacondicionamiento capitaliza su mano de obra: la partida
carga "unidades en proceso" (VIN y línea de negocio de la unidad) y acredita "mano de obra de
taller aplicada" (VIN y línea taller), con las cuentas de las reglas `orden_trabajo`; pasa la
unidad de "en taller" a "lista"; todo en una transacción. Sin costo no cierra sin justificación y,
con ella, cierra sin partida. `costo_taller_de_unidad` y `ordenes_de_unidad` alimentan la ficha de
costo de la unidad (HU-4.08).
HU-5.07 (diferido): los demás destinos (mantenimiento a gasto, mejora a activo fijo, garantía,
postventa facturable: Sprint 5) y reabrir o cambiar el tipo de una orden cerrada con aprobación
del contador (criterio 4). Las órdenes abiertas al cierre de mes (criterio 5) se ven en el listado.
"""

from datetime import date
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.dinero import redondear
from app.comun.errores import ErrorNegocio
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from app.modulos.taller.models import HoraTrabajo, OrdenTrabajo, TarifaManoObra
from app.modulos.taller.schemas import CierreEntrada, HoraEntrada, OrdenEntrada, TarifaEntrada
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


# ── HU-5.03: mano de obra ─────────────────────────────────────────────────────


def _horas(texto: str) -> Decimal:
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        raise ErrorNegocio("Las horas no son un número válido") from None
    if not valor.is_finite() or valor <= 0:
        raise ErrorNegocio("Las horas deben ser un número mayor que cero")
    if -valor.as_tuple().exponent > 2:  # type: ignore[operator]
        raise ErrorNegocio("Las horas admiten hasta 2 decimales")
    if valor > 24:
        raise ErrorNegocio("Un registro no puede pasar de 24 horas")
    return valor


def registrar_horas(
    db: Session, orden_id: int, datos: HoraEntrada, usuario_id: int | None = None
) -> HoraTrabajo:
    """Costea las horas con la tarifa vigente en su fecha y las guarda con esa tarifa."""
    horas = _horas(datos.horas)
    # Bloquea la orden: un cierre simultáneo no deja horas sin partida.
    orden = db.get(OrdenTrabajo, orden_id, with_for_update=True)
    if orden is None:
        raise ErrorNegocio(f"No existe la orden de trabajo {orden_id}", 404)
    if orden.estado != "abierta":
        raise ErrorNegocio(f"La orden {orden.numero} está cerrada: no admite más horas", 409)
    if datos.fecha > date.today():
        raise ErrorNegocio("La fecha de las horas no puede ser futura")
    if datos.fecha < orden.fecha_apertura:
        raise ErrorNegocio("Las horas no pueden ser anteriores a la apertura de la orden")
    tarifa = tarifa_costo_vigente(db, datos.fecha)
    hora = HoraTrabajo(
        orden_id=orden.id,
        mecanico=datos.mecanico,
        fecha=datos.fecha,
        horas=horas,
        tarea=datos.tarea,
        tarifa_hora=tarifa,
        costo=redondear(horas * tarifa, 2),
        registrado_por=usuario_id,
    )
    db.add(hora)
    db.commit()
    db.refresh(hora)
    return hora


def listar_horas(db: Session, orden_id: int) -> list[HoraTrabajo]:
    return list(obtener_orden(db, orden_id).horas)


# ── HU-5.07: cierre de la orden ───────────────────────────────────────────────

DOCUMENTO_ORDEN = "orden_trabajo"


def cerrar_orden(
    db: Session, orden_id: int, datos: CierreEntrada, usuario_id: int | None = None
) -> OrdenTrabajo:
    """Cierra la orden con su partida y pasa la unidad a "lista", en una transacción, o no guarda nada."""
    orden = db.get(OrdenTrabajo, orden_id, with_for_update=True)
    if orden is None:
        raise ErrorNegocio(f"No existe la orden de trabajo {orden_id}", 404)
    if orden.estado != "abierta":
        raise ErrorNegocio(f"La orden {orden.numero} ya está cerrada", 409)
    suma = db.scalar(
        select(func.coalesce(func.sum(HoraTrabajo.costo), 0)).where(HoraTrabajo.orden_id == orden.id)
    )
    total = redondear(suma, 2)
    if total == 0 and not datos.justificacion:
        raise ErrorNegocio("Una orden sin costo se cierra solo con una justificación")
    unidad = unidades.obtener_por_vin(db, orden.vin)
    hoy = date.today()
    try:
        if total > 0:
            en_proceso = contabilidad.cuenta_regla(db, DOCUMENTO_ORDEN, "unidad_en_proceso")
            aplicada = contabilidad.cuenta_regla(db, DOCUMENTO_ORDEN, "mano_obra_aplicada")
        unidades.cambiar_estado(
            db, orden.vin, "lista", f"Cierre de la orden {orden.numero}", usuario_id, confirmar=False
        )
        if total > 0:
            partida = contabilidad.registrar_automatica(
                db,
                fecha=hoy,
                concepto=f"Reacondicionamiento de la unidad {orden.vin}, orden {orden.numero}"[:300],
                lineas=[
                    LineaEntrada(
                        cuenta_id=en_proceso,
                        lado="debe",
                        monto=f"{total:.6f}",
                        linea_negocio=unidad.linea_negocio,
                        vin=orden.vin,
                    ),
                    LineaEntrada(
                        cuenta_id=aplicada,
                        lado="haber",
                        monto=f"{total:.6f}",
                        linea_negocio="taller",
                        vin=orden.vin,
                    ),
                ],
                documento_tipo=DOCUMENTO_ORDEN,
                documento_id=orden.id,
                usuario_id=usuario_id,
            )
            orden.partida_id = partida.id
        orden.estado = "cerrada"
        orden.fecha_cierre = hoy
        orden.cerrada_por = usuario_id
        orden.costo_total = total
        orden.justificacion = datos.justificacion
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(orden)
    return orden


def ordenes_de_unidad(db: Session, vin: str) -> list[OrdenTrabajo]:
    """Órdenes de la unidad para su ficha de costo (número, estado, fechas y costo), de la más antigua."""
    return list(reversed(listar_ordenes(db, vin=vin)))


def costo_taller_de_unidad(db: Session, vin: str) -> Decimal:
    """Mano de obra capitalizada de las órdenes de reacondicionamiento CERRADAS de la unidad."""
    total = db.scalar(
        select(func.coalesce(func.sum(OrdenTrabajo.costo_total), 0)).where(
            OrdenTrabajo.vin == vin.strip().upper(),
            OrdenTrabajo.estado == "cerrada",
            OrdenTrabajo.tipo == "reacondicionamiento",
        )
    )
    return redondear(total, 2)
