"""Costo de la unidad: E1 (unidades por VIN), E4 (compra e importación), E5 (taller) y E3 (alta en flota)."""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.models import (
    Contrato,
    DocumentoPorPagar,
    EstadoPartida,
    EstadoUnidad,
    GastoImportacion,
    HistorialEstado,
    LineaPartida,
    ManoObra,
    Moneda,
    OrdenTrabajo,
    Partida,
    Proveedor,
    Unidad,
)
from app.services.base import (
    Conflicto,
    ErrorNegocio,
    NoEncontrado,
    obtener,
    q2,
    registrar_bitacora,
    validar_nit,
    validar_vin,
)
from app.services.contabilidad import LineaIn, partida_automatica, saldo_cuenta_vin, tipo_cambio_de

CTA_UNIDADES_PROCESO = "1.1.06"
CTA_FLOTA = "1.2.01"
CTA_IVA_CREDITO = "1.1.05"
CTA_PROV_LOCAL = "2.1.01"
CTA_PROV_EXTERIOR = "2.1.02"
CTA_MO_APLICADA = "5.1.01"
CTA_MANTENIMIENTO = "6.1.01"

CONCEPTOS_IMPORTACION = {
    "FLETE": "Flete", "SEGURO": "Seguro de transporte", "AGENTE_ADUANAL": "Agente aduanal",
    "ALMACENAJE": "Almacenaje", "DAI": "DAI", "IVA_IMPORTACION": "IVA de importación",
    "IPRIMA": "IPRIMA", "PLACAS": "Placas", "OTROS": "Otros",
}

# HU-5.01: coherencia entre tipo de orden y estado de la unidad (tabla de la Épica 5).
TIPO_ORDEN_ESTADOS = {
    "REACONDICIONAMIENTO": {EstadoUnidad.EN_ADUANA, EstadoUnidad.EN_TALLER},
    "MANTENIMIENTO": {EstadoUnidad.EN_FLOTA},
}


# ======================================================================= Unidades (HU-1.05, HU-4.07)

def cambiar_estado(db: Session, unidad: Unidad, nuevo: str, usuario: str, documento: str) -> None:
    anterior = unidad.estado
    unidad.estado = nuevo
    unidad.historial.append(HistorialEstado(estado_anterior=anterior, estado_nuevo=nuevo,
                                            usuario=usuario, documento=documento))
    registrar_bitacora(db, usuario, "CAMBIAR_ESTADO", "Unidad", unidad.id, unidad.vin,
                       f"{anterior} → {nuevo} ({documento})")


def obtener_unidad(db: Session, unidad_id: int) -> Unidad:
    return obtener(db, Unidad, unidad_id, "La unidad")


def unidad_por_vin(db: Session, vin: str) -> Unidad:
    unidad = db.scalar(select(Unidad).where(Unidad.vin == vin.strip().upper()))
    if unidad is None:
        raise NoEncontrado(f"No existe una unidad con VIN {vin}")
    return unidad


def listar_unidades(db: Session, estado: str | None = None) -> list[Unidad]:
    stmt = select(Unidad).order_by(Unidad.id)
    if estado:
        stmt = stmt.where(Unidad.estado == estado)
    return list(db.scalars(stmt))


def ordenes_abiertas(db: Session, unidad_id: int) -> list[OrdenTrabajo]:
    return list(db.scalars(select(OrdenTrabajo).where(
        OrdenTrabajo.unidad_id == unidad_id, OrdenTrabajo.estado == "ABIERTA")))


def contrato_activo(db: Session, unidad_id: int) -> Contrato | None:
    return db.scalar(select(Contrato).where(Contrato.unidad_id == unidad_id, Contrato.estado == "ACTIVO"))


def avanzar_importacion(db: Session, unidad_id: int, nuevo: str, documento: str, usuario: str) -> Unidad:
    """HU-4.07: en tránsito → en aduana; en taller → lista. El paso a taller se hace al abrir la orden."""
    unidad = obtener_unidad(db, unidad_id)
    permitidos = {
        (EstadoUnidad.EN_TRANSITO, EstadoUnidad.EN_ADUANA),
        (EstadoUnidad.EN_TALLER, EstadoUnidad.LISTA),
    }
    if (unidad.estado, nuevo) not in permitidos:
        if nuevo == EstadoUnidad.EN_TALLER:
            raise ErrorNegocio("La unidad pasa a taller al abrir su orden de reacondicionamiento")
        raise Conflicto(f"No se puede pasar de {unidad.estado} a {nuevo}")
    if nuevo == EstadoUnidad.LISTA and ordenes_abiertas(db, unidad.id):
        raise Conflicto("La unidad tiene órdenes de reacondicionamiento abiertas")
    cambiar_estado(db, unidad, nuevo, usuario, documento)
    db.commit()
    return unidad


# ======================================================================= Proveedores (HU-4.01)

def crear_proveedor(db: Session, datos, usuario: str) -> Proveedor:
    nit = None
    if datos.tipo == "LOCAL":
        if not datos.nit:
            raise ErrorNegocio("El proveedor local requiere NIT")
        nit = validar_nit(datos.nit)
        if db.scalar(select(Proveedor).where(Proveedor.nit == nit)):
            raise Conflicto(f"Ya existe un proveedor con NIT {nit}")
    proveedor = Proveedor(nombre=datos.nombre, tipo=datos.tipo, nit=nit,
                          pais=datos.pais or ("Guatemala" if datos.tipo == "LOCAL" else "Estados Unidos"),
                          rubro=datos.rubro, moneda=datos.moneda)
    db.add(proveedor)
    db.flush()
    db.commit()
    return proveedor


# ======================================================================= Compra en EE. UU. (HU-4.02)

def registrar_compra(db: Session, datos, usuario: str) -> dict:
    proveedor = obtener(db, Proveedor, datos.proveedor_id, "El proveedor")
    vin = validar_vin(datos.vin)
    if db.scalar(select(Unidad).where(Unidad.vin == vin)):
        raise Conflicto(f"La unidad {vin} ya está registrada")
    total_usd = q2(datos.precio_usd + datos.cargos_usd)
    tc = tipo_cambio_de(db, datos.fecha)
    try:
        unidad = Unidad(vin=vin, marca=datos.marca, linea=datos.linea, modelo_anio=datos.modelo_anio,
                        color=datos.color, tipo_vehiculo=datos.tipo_vehiculo, estado=EstadoUnidad.EN_TRANSITO)
        db.add(unidad)
        db.flush()
        unidad.historial.append(HistorialEstado(estado_anterior=None, estado_nuevo=EstadoUnidad.EN_TRANSITO,
                                                usuario=usuario, documento=f"Compra lote {datos.numero_lote}"))
        doc = DocumentoPorPagar(proveedor_id=proveedor.id, tipo="COMPRA_UNIDAD", referencia=datos.numero_lote,
                                fecha=datos.fecha, moneda=Moneda.USD, monto=total_usd, saldo=total_usd,
                                tipo_cambio=tc, unidad_id=unidad.id)
        db.add(doc)
        db.flush()
        monto_q = q2(total_usd * tc)
        partida = partida_automatica(db, datos.fecha, f"Compra de unidad {vin} a {proveedor.nombre}", [
            LineaIn(CTA_UNIDADES_PROCESO, "DEBE", total_usd, Moneda.USD, unidad_id=unidad.id,
                    detalle="Compra", monto_q=monto_q),
            LineaIn(CTA_PROV_EXTERIOR, "HABER", total_usd, Moneda.USD, linea_negocio="ALQUILER",
                    unidad_id=unidad.id, detalle=proveedor.nombre, monto_q=monto_q),
        ], "COMPRA_UNIDAD", doc.id, usuario)
        doc.partida_id = partida.id
        registrar_bitacora(db, usuario, "COMPRA", "Unidad", unidad.id, vin, f"USD {total_usd} a TC {tc}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"unidad": unidad, "documento": doc, "partida": partida}


# ======================================================================= Gastos de importación (HU-4.04)

def registrar_gasto_importacion(db: Session, datos, usuario: str) -> dict:
    unidad = obtener_unidad(db, datos.unidad_id)
    if unidad.estado not in (EstadoUnidad.EN_TRANSITO, EstadoUnidad.EN_ADUANA,
                             EstadoUnidad.EN_TALLER, EstadoUnidad.LISTA):
        raise Conflicto(f"La unidad ya está en {unidad.estado}; los gastos de importación se registran antes del alta")
    proveedor = obtener(db, Proveedor, datos.proveedor_id, "El proveedor")
    if datos.concepto not in CONCEPTOS_IMPORTACION:
        raise ErrorNegocio(f"Concepto inválido. Opciones: {', '.join(CONCEPTOS_IMPORTACION)}")
    monto = q2(datos.monto)
    tc = tipo_cambio_de(db, datos.fecha) if datos.moneda == Moneda.USD else None
    try:
        doc = DocumentoPorPagar(proveedor_id=proveedor.id, tipo="GASTO_IMPORTACION", referencia=datos.referencia,
                                fecha=datos.fecha, moneda=datos.moneda, monto=monto, saldo=monto,
                                tipo_cambio=tc, unidad_id=unidad.id)
        db.add(doc)
        db.flush()
        gasto = GastoImportacion(unidad_id=unidad.id, concepto=datos.concepto, documento_id=doc.id)
        db.add(gasto)
        db.flush()
        nombre = CONCEPTOS_IMPORTACION[datos.concepto]
        # El IVA de importación es crédito fiscal: no forma parte del costo de la unidad.
        cuenta_debe = CTA_IVA_CREDITO if datos.concepto == "IVA_IMPORTACION" else CTA_UNIDADES_PROCESO
        cuenta_haber = CTA_PROV_EXTERIOR if datos.moneda == Moneda.USD else CTA_PROV_LOCAL
        monto_q = q2(monto * tc) if tc else monto
        partida = partida_automatica(db, datos.fecha, f"{nombre} – unidad {unidad.vin}", [
            LineaIn(cuenta_debe, "DEBE", monto, datos.moneda, unidad_id=unidad.id,
                    detalle=f"Importación · {nombre}", monto_q=monto_q),
            LineaIn(cuenta_haber, "HABER", monto, datos.moneda, linea_negocio="ALQUILER",
                    unidad_id=unidad.id, detalle=proveedor.nombre, monto_q=monto_q),
        ], "GASTO_IMPORTACION", gasto.id, usuario)
        doc.partida_id = partida.id
        registrar_bitacora(db, usuario, "GASTO_IMPORTACION", "Unidad", unidad.id, unidad.vin,
                           f"{nombre}: {datos.moneda} {monto}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"gasto": gasto, "documento": doc, "partida": partida, "capitalizable": cuenta_debe == CTA_UNIDADES_PROCESO}


# ======================================================================= Taller (HU-5.01, HU-5.03, HU-5.07)

def abrir_orden(db: Session, datos, usuario: str) -> OrdenTrabajo:
    unidad = obtener_unidad(db, datos.unidad_id)
    if datos.tipo not in TIPO_ORDEN_ESTADOS:
        raise ErrorNegocio("Tipo de orden inválido para el corte: REACONDICIONAMIENTO o MANTENIMIENTO")
    if unidad.estado not in TIPO_ORDEN_ESTADOS[datos.tipo]:
        raise ErrorNegocio(
            f"Una orden de {datos.tipo.lower()} no es coherente con una unidad {unidad.estado}"
        )
    if datos.tipo == "MANTENIMIENTO" and contrato_activo(db, unidad.id):
        raise Conflicto("La unidad está alquilada; cierre el contrato antes de enviarla a taller")
    orden = OrdenTrabajo(unidad_id=unidad.id, tipo=datos.tipo, descripcion=datos.descripcion,
                         responsable=datos.responsable, kilometraje=datos.kilometraje or unidad.kilometraje,
                         fecha_apertura=datos.fecha)
    db.add(orden)
    db.flush()
    if unidad.estado != EstadoUnidad.EN_TALLER:
        cambiar_estado(db, unidad, EstadoUnidad.EN_TALLER, usuario, f"Orden de trabajo #{orden.id}")
    registrar_bitacora(db, usuario, "ABRIR_ORDEN", "OrdenTrabajo", orden.id, unidad.vin, datos.tipo)
    db.commit()
    return orden


def registrar_mano_obra(db: Session, orden_id: int, datos, usuario: str) -> OrdenTrabajo:
    orden = obtener(db, OrdenTrabajo, orden_id, "La orden")
    if orden.estado != "ABIERTA":
        raise Conflicto("No se pueden registrar horas en una orden cerrada")
    tarifa = config.TARIFA_HORA_TALLER
    orden.mano_obra.append(ManoObra(mecanico=datos.mecanico, fecha=datos.fecha, horas=datos.horas,
                                    tarifa=tarifa, costo=q2(datos.horas * tarifa), descripcion=datos.descripcion))
    registrar_bitacora(db, usuario, "MANO_OBRA", "OrdenTrabajo", orden.id, orden.unidad.vin,
                       f"{datos.horas} h × Q{tarifa}")
    db.commit()
    db.refresh(orden)
    return orden


def costo_orden(orden: OrdenTrabajo) -> Decimal:
    return sum((m.costo for m in orden.mano_obra), Decimal("0"))


def cerrar_orden(db: Session, orden_id: int, fecha: date, justificacion: str | None, usuario: str) -> dict:
    """Ninguna orden queda sin destino contable: reacondicionamiento se capitaliza, mantenimiento es gasto."""
    orden = obtener(db, OrdenTrabajo, orden_id, "La orden")
    if orden.estado != "ABIERTA":
        raise Conflicto("La orden ya está cerrada")
    costo = costo_orden(orden)
    if costo == 0 and not justificacion:
        raise ErrorNegocio("Una orden sin costo sólo puede cerrarse con una justificación")
    unidad = orden.unidad
    try:
        partida = None
        if costo > 0:
            destino = CTA_UNIDADES_PROCESO if orden.tipo == "REACONDICIONAMIENTO" else CTA_MANTENIMIENTO
            partida = partida_automatica(db, fecha, f"Cierre orden #{orden.id} ({orden.tipo.lower()}) – {unidad.vin}", [
                LineaIn(destino, "DEBE", costo, unidad_id=unidad.id,
                        detalle="Reacondicionamiento · mano de obra" if destino == CTA_UNIDADES_PROCESO
                        else "Mantenimiento · mano de obra"),
                LineaIn(CTA_MO_APLICADA, "HABER", costo, detalle=f"Orden #{orden.id}"),
            ], "ORDEN_TRABAJO", orden.id, usuario)
            orden.partida_id = partida.id
        orden.estado = "CERRADA"
        orden.fecha_cierre = fecha
        orden.justificacion_cero = justificacion
        if orden.tipo == "MANTENIMIENTO":
            cambiar_estado(db, unidad, EstadoUnidad.EN_FLOTA, usuario, f"Cierre orden #{orden.id}")
        registrar_bitacora(db, usuario, "CERRAR_ORDEN", "OrdenTrabajo", orden.id, unidad.vin, f"Q{costo}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"orden": orden, "costo": costo, "partida": partida}


# ======================================================================= Hoja de costo (HU-4.08)

def hoja_costo(db: Session, unidad_id: int) -> dict:
    unidad = obtener_unidad(db, unidad_id)
    filas = db.execute(
        select(LineaPartida, Partida)
        .join(Partida)
        .where(LineaPartida.unidad_id == unidad.id, Partida.estado == EstadoPartida.CONTABILIZADA,
               LineaPartida.cuenta.has(codigo=CTA_UNIDADES_PROCESO))
        .order_by(Partida.fecha, LineaPartida.id)
    ).all()

    grupos: dict[str, dict] = defaultdict(lambda: {"total_q": Decimal("0"), "detalle": []})
    trasladado = Decimal("0")
    for linea, partida in filas:
        if linea.haber > 0:
            trasladado += linea.haber
            continue
        if partida.origen_tipo == "COMPRA_UNIDAD":
            grupo = "Compra"
        elif partida.origen_tipo == "GASTO_IMPORTACION":
            grupo = "Importación"
        else:
            grupo = "Reacondicionamiento"
        grupos[grupo]["total_q"] += linea.debe
        grupos[grupo]["detalle"].append({
            "fecha": partida.fecha, "concepto": linea.detalle, "monto_q": linea.debe,
            "moneda": linea.moneda, "monto_original": linea.monto_original, "tipo_cambio": linea.tipo_cambio,
            "partida_numero": partida.numero,
        })
    orden_grupos = ["Compra", "Importación", "Reacondicionamiento"]
    componentes = [{"grupo": g, **grupos[g]} for g in orden_grupos if g in grupos]
    total = sum((c["total_q"] for c in componentes), Decimal("0"))
    saldo_mayor = saldo_cuenta_vin(db, CTA_UNIDADES_PROCESO, unidad.id)
    return {
        "vin": unidad.vin, "estado": unidad.estado, "componentes": componentes, "costo_total": total,
        "trasladado_a_flota": trasladado, "saldo_unidades_en_proceso": saldo_mayor,
        "cuadra_con_mayor": total - trasladado == saldo_mayor,
    }


# ======================================================================= Alta en flota (HU-3.01, HU-3.02)

def dar_alta_flota(db: Session, unidad_id: int, fecha: date, vida_util_meses: int,
                   valor_residual: Decimal, usuario: str) -> dict:
    unidad = obtener_unidad(db, unidad_id)
    if unidad.estado != EstadoUnidad.LISTA:
        raise Conflicto(f"Sólo se dan de alta unidades en estado LISTA (estado actual: {unidad.estado})")
    if ordenes_abiertas(db, unidad.id):
        raise Conflicto("La unidad tiene órdenes de reacondicionamiento abiertas")
    costo = saldo_cuenta_vin(db, CTA_UNIDADES_PROCESO, unidad.id)
    if costo <= 0:
        raise ErrorNegocio("La unidad no tiene costo acumulado en su hoja de costo")
    if valor_residual >= costo:
        raise ErrorNegocio("El valor residual debe ser menor que el costo de alta")
    try:
        partida = partida_automatica(db, fecha, f"Alta en flota de la unidad {unidad.vin}", [
            LineaIn(CTA_FLOTA, "DEBE", costo, unidad_id=unidad.id, detalle="Alta en flota"),
            LineaIn(CTA_UNIDADES_PROCESO, "HABER", costo, unidad_id=unidad.id, detalle="Traslado a flota"),
        ], "ALTA_FLOTA", unidad.id, usuario)
        unidad.fecha_alta_flota = fecha
        unidad.costo_alta = costo
        unidad.vida_util_meses = vida_util_meses
        unidad.valor_residual = q2(valor_residual)
        cambiar_estado(db, unidad, EstadoUnidad.EN_FLOTA, usuario, f"Alta en flota, partida {partida.numero}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"unidad": unidad, "costo_alta": costo, "partida": partida}
