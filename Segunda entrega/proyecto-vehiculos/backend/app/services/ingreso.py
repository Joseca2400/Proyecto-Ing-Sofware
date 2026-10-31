"""Ingreso de la unidad: E6 (clientes, FEL, cobros), E3 (contratos) y E7 (reportes)."""

import uuid
from collections import Counter
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app import config
from app.models import Cliente, Cobro, Contrato, EstadoUnidad, Factura, Moneda, Unidad
from app.services.base import Conflicto, ErrorNegocio, obtener, q2, registrar_bitacora, validar_nit
from app.services.ciclo import (
    CTA_FLOTA,
    CTA_MANTENIMIENTO,
    CTA_UNIDADES_PROCESO,
    contrato_activo,
    obtener_unidad,
)
from app.services.contabilidad import LineaIn, mayor, partida_automatica, saldo_cuenta_vin, tipo_cambio_de

CTA_BANCOS = {Moneda.GTQ: "1.1.01", Moneda.USD: "1.1.02"}
CTA_CLIENTES = {Moneda.GTQ: "1.1.03", Moneda.USD: "1.1.04"}
CTA_IVA_DEBITO = "2.1.03"
CTA_INGRESO_ALQUILER = "4.1.01"
CTA_DIFERENCIAL = "7.1.01"
SERIE_SIMULADA = "SIM-A"


# ======================================================================= Clientes (HU-6.01)

def crear_cliente(db: Session, datos, usuario: str) -> Cliente:
    nit = validar_nit(datos.nit) if datos.nit else None
    if not (nit or datos.cui or datos.pasaporte):
        raise ErrorNegocio("El cliente debe tener NIT, CUI o pasaporte")
    if datos.cui and (len(datos.cui) != 13 or not datos.cui.isdigit()):
        raise ErrorNegocio("El CUI debe tener 13 dígitos")
    condiciones = []
    if nit:
        condiciones.append(Cliente.nit == nit)
    if datos.cui:
        condiciones.append(Cliente.cui == datos.cui)
    if datos.pasaporte:
        condiciones.append(Cliente.pasaporte == datos.pasaporte)
    if dup := db.scalar(select(Cliente).where(or_(*condiciones))):
        raise Conflicto(f"Ya existe el cliente '{dup.nombre}' con esa identificación")
    cliente = Cliente(tipo=datos.tipo, nombre=datos.nombre, nit=nit, cui=datos.cui, pasaporte=datos.pasaporte,
                      pais=datos.pais, direccion=datos.direccion, telefono=datos.telefono, correo=datos.correo)
    db.add(cliente)
    db.flush()
    db.commit()
    return cliente


# ======================================================================= Contratos (HU-3.06, HU-3.08)

def dias_contrato(salida: date, fin: date) -> int:
    return max(1, (fin - salida).days)


def registrar_contrato(db: Session, datos, usuario: str) -> Contrato:
    cliente = obtener(db, Cliente, datos.cliente_id, "El cliente")
    unidad = obtener_unidad(db, datos.unidad_id)
    if unidad.estado != EstadoUnidad.EN_FLOTA:
        raise Conflicto(f"La unidad {unidad.vin} no está disponible (estado: {unidad.estado})")
    if activo := contrato_activo(db, unidad.id):
        raise Conflicto(f"La unidad {unidad.vin} ya está alquilada (contrato #{activo.id})")
    if unidad.fecha_alta_flota and datos.fecha_salida < unidad.fecha_alta_flota:
        raise ErrorNegocio("La fecha de salida es anterior al alta de la unidad en la flota")
    if datos.fecha_prevista < datos.fecha_salida:
        raise ErrorNegocio("La fecha prevista de devolución es anterior a la salida")
    km = datos.km_salida if datos.km_salida is not None else unidad.kilometraje
    if km < unidad.kilometraje:
        raise ErrorNegocio(f"El kilometraje de salida no puede ser menor al de la unidad ({unidad.kilometraje})")
    contrato = Contrato(cliente_id=cliente.id, unidad_id=unidad.id, fecha_salida=datos.fecha_salida,
                        fecha_prevista=datos.fecha_prevista, tarifa_diaria=q2(datos.tarifa_diaria),
                        moneda=datos.moneda, km_salida=km, registrado_por=usuario)
    db.add(contrato)
    db.flush()
    db.commit()
    return contrato


def monto_estimado(c: Contrato) -> Decimal:
    return q2(c.tarifa_diaria * dias_contrato(c.fecha_salida, c.fecha_prevista))


def cerrar_contrato(db: Session, contrato_id: int, datos, usuario: str) -> dict:
    contrato = obtener(db, Contrato, contrato_id, "El contrato")
    if contrato.estado != "ACTIVO":
        raise Conflicto("El contrato ya está cerrado")
    if datos.fecha_devolucion < contrato.fecha_salida:
        raise ErrorNegocio("La fecha de devolución es anterior a la salida")
    if datos.km_entrada < contrato.km_salida:
        raise ErrorNegocio("El kilometraje de entrada no puede ser menor al de salida")
    contrato.fecha_devolucion = datos.fecha_devolucion
    contrato.km_entrada = datos.km_entrada
    contrato.observaciones = datos.observaciones
    contrato.estado = "CERRADO"
    contrato.unidad.kilometraje = datos.km_entrada
    registrar_bitacora(db, usuario, "CERRAR", "Contrato", contrato.id, contrato.unidad.vin,
                       f"{datos.km_entrada - contrato.km_salida} km")
    db.commit()
    return resumen_cierre(contrato)


def resumen_cierre(c: Contrato) -> dict:
    dias = dias_contrato(c.fecha_salida, c.fecha_devolucion)
    return {"contrato": c, "dias": dias, "km_recorridos": c.km_entrada - c.km_salida,
            "monto": q2(c.tarifa_diaria * dias)}


# ======================================================================= Factura FEL (HU-6.02, HU-3.10)

def facturar_contrato(db: Session, contrato_id: int, fecha: date, consumidor_final: bool, usuario: str) -> Factura:
    contrato = obtener(db, Contrato, contrato_id, "El contrato")
    if contrato.estado != "CERRADO":
        raise Conflicto("En el corte se factura al cerrar el contrato (facturación recurrente: HU-3.10)")
    if db.scalar(select(Factura).where(Factura.origen_tipo == "CONTRATO", Factura.origen_id == contrato.id)):
        raise Conflicto(f"El contrato #{contrato.id} ya fue facturado")

    dias = dias_contrato(contrato.fecha_salida, contrato.fecha_devolucion)
    total = q2(contrato.tarifa_diaria * dias)  # tarifa con IVA incluido
    base = q2(total / (1 + config.TASA_IVA))
    iva = total - base
    tc = tipo_cambio_de(db, fecha) if contrato.moneda == Moneda.USD else None
    total_q = q2(total * tc) if tc else total
    iva_q = q2(iva * tc) if tc else iva
    base_q = total_q - iva_q

    if consumidor_final and total_q >= config.UMBRAL_CONSUMIDOR_FINAL:
        raise ErrorNegocio(
            f"Una factura de Q{total_q:,.2f} no puede emitirse a Consumidor Final "
            f"(umbral SAT: Q{config.UMBRAL_CONSUMIDOR_FINAL:,.2f}); use el NIT o CUI del cliente"
        )
    unidad = contrato.unidad
    numero = (db.scalar(select(func.max(Factura.numero_dte)).where(Factura.serie == SERIE_SIMULADA)) or 0) + 1
    try:
        factura = Factura(
            cliente_id=None if consumidor_final else contrato.cliente_id, fecha=fecha, moneda=contrato.moneda,
            tipo_cambio=tc, base=base, iva=iva, total=total, total_q=total_q, saldo=total,
            descripcion=f"Alquiler {unidad.marca} {unidad.linea} {unidad.modelo_anio}, {dias} días "
                        f"({contrato.fecha_salida:%d/%m/%Y} al {contrato.fecha_devolucion:%d/%m/%Y})",
            linea_negocio="ALQUILER", unidad_id=unidad.id, origen_tipo="CONTRATO", origen_id=contrato.id,
            # Certificación simulada: se reemplaza por el certificador FEL cuando se elija.
            serie=SERIE_SIMULADA, numero_dte=numero, autorizacion=str(uuid.uuid4()).upper(), simulada=True,
        )
        db.add(factura)
        db.flush()
        m = contrato.moneda
        partida = partida_automatica(db, fecha, f"Factura {factura.serie}-{numero} contrato #{contrato.id}", [
            LineaIn(CTA_CLIENTES[m], "DEBE", total, m, linea_negocio="ALQUILER", unidad_id=unidad.id,
                    detalle=contrato.cliente.nombre, monto_q=total_q),
            LineaIn(CTA_INGRESO_ALQUILER, "HABER", base, m, unidad_id=unidad.id,
                    detalle=f"Contrato #{contrato.id}", monto_q=base_q),
            LineaIn(CTA_IVA_DEBITO, "HABER", iva, m, detalle="IVA débito", monto_q=iva_q),
        ], "FACTURA", factura.id, usuario)
        factura.partida_id = partida.id
        registrar_bitacora(db, usuario, "FACTURAR", "Factura", factura.id, unidad.vin,
                           f"{factura.serie}-{numero} {m} {total} (certificación simulada)")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return factura


# ======================================================================= Cobros (HU-6.07, HU-2.09)

def registrar_cobro(db: Session, factura_id: int, datos, usuario: str) -> Cobro:
    factura = obtener(db, Factura, factura_id, "La factura")
    monto = q2(datos.monto)
    if monto <= 0:
        raise ErrorNegocio("El monto debe ser mayor que 0")
    if monto > factura.saldo:
        raise ErrorNegocio(f"El cobro excede el saldo de la factura ({factura.moneda} {factura.saldo})")
    m = factura.moneda
    try:
        if m == Moneda.USD:
            tc_cobro = tipo_cambio_de(db, datos.fecha)
            q_cobro = q2(monto * tc_cobro)
            q_factura = q2(monto * factura.tipo_cambio)
        else:
            tc_cobro, q_cobro, q_factura = None, monto, monto
        diferencial = q_cobro - q_factura  # positivo = ganancia cambiaria
        cobro = Cobro(factura_id=factura.id, fecha=datos.fecha, forma=datos.forma, monto=monto,
                      tipo_cambio=tc_cobro, diferencial_q=diferencial, referencia=datos.referencia)
        db.add(cobro)
        db.flush()
        lineas = [
            LineaIn(CTA_BANCOS[m], "DEBE", monto, m, tipo_cambio=tc_cobro, monto_q=q_cobro,
                    detalle=f"{datos.forma} {datos.referencia or ''}".strip()),
            LineaIn(CTA_CLIENTES[m], "HABER", monto, m, linea_negocio="ALQUILER", unidad_id=factura.unidad_id,
                    tipo_cambio=factura.tipo_cambio, monto_q=q_factura, detalle=f"Factura {factura.serie}-{factura.numero_dte}"),
        ]
        if diferencial:
            lineas.append(LineaIn(CTA_DIFERENCIAL, "HABER" if diferencial > 0 else "DEBE", abs(diferencial),
                                  detalle="Ganancia cambiaria" if diferencial > 0 else "Pérdida cambiaria"))
        partida = partida_automatica(db, datos.fecha, f"Cobro factura {factura.serie}-{factura.numero_dte}",
                                     lineas, "COBRO", cobro.id, usuario)
        cobro.partida_id = partida.id
        factura.saldo -= monto
        registrar_bitacora(db, usuario, "COBRAR", "Factura", factura.id, None,
                           f"{m} {monto}; diferencial Q{diferencial}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    return cobro


# ======================================================================= Reportes (E7)

ETAPAS = [EstadoUnidad.EN_TRANSITO, EstadoUnidad.EN_ADUANA, EstadoUnidad.EN_TALLER,
          EstadoUnidad.LISTA, EstadoUnidad.EN_FLOTA]


def valor_unidad(db: Session, unidad: Unidad) -> Decimal:
    if unidad.estado == EstadoUnidad.EN_FLOTA or unidad.fecha_alta_flota:
        return saldo_cuenta_vin(db, CTA_FLOTA, unidad.id)
    return saldo_cuenta_vin(db, CTA_UNIDADES_PROCESO, unidad.id)


def unidades_por_etapa(db: Session) -> dict:
    """HU-7.04: cantidad y capital invertido por etapa del ciclo."""
    unidades = list(db.scalars(select(Unidad)))
    etapas = []
    for etapa in ETAPAS:
        del_estado = [u for u in unidades if u.estado == etapa]
        valores = [(u, valor_unidad(db, u)) for u in del_estado]
        etapas.append({
            "estado": etapa, "cantidad": len(del_estado),
            "valor_q": sum((v for _, v in valores), Decimal("0")),
            "unidades": [{"vin": u.vin, "descripcion": f"{u.marca} {u.linea} {u.modelo_anio}", "valor_q": v,
                          "alquilada": contrato_activo(db, u.id) is not None} for u, v in valores],
        })
    total = sum((e["valor_q"] for e in etapas), Decimal("0"))
    return {"etapas": etapas, "total_unidades": len(unidades), "capital_invertido_q": total}


def rentabilidad_unidades(db: Session, estado: str | None = None) -> list[dict]:
    """HU-7.02 (versión del corte): las cifras salen del mayor filtrado por VIN."""
    stmt = select(Unidad).order_by(Unidad.id)
    if estado:
        stmt = stmt.where(Unidad.estado == estado)
    resultado = []
    for u in db.scalars(stmt):
        proceso = mayor(db, CTA_UNIDADES_PROCESO, unidad_id=u.id)["movimientos"]
        costo = sum((m["debe"] for m in proceso), Decimal("0"))
        ingresos = saldo_cuenta_vin(db, CTA_INGRESO_ALQUILER, u.id)
        mantenimiento = saldo_cuenta_vin(db, CTA_MANTENIMIENTO, u.id)
        resultado_op = ingresos - mantenimiento
        contratos = db.scalars(select(Contrato).where(Contrato.unidad_id == u.id)).all()
        dias_alquilada = sum(dias_contrato(c.fecha_salida, c.fecha_devolucion)
                             for c in contratos if c.fecha_devolucion)
        resultado.append({
            "vin": u.vin, "descripcion": f"{u.marca} {u.linea} {u.modelo_anio}", "estado": u.estado,
            "costo_adquisicion_q": costo, "ingresos_alquiler_q": ingresos, "mantenimiento_q": mantenimiento,
            "resultado_q": resultado_op,
            "rentabilidad_sobre_costo": round(float(resultado_op / costo), 4) if costo else None,
            "contratos": len(contratos), "dias_alquilada": dias_alquilada,
            "pendiente": "Depreciación (HU-2.07), seguro y marchamo (HU-3.04) se suman en sprints siguientes",
        })
    return resultado


def resumen_por_estado(db: Session) -> dict:
    return dict(Counter(u.estado for u in db.scalars(select(Unidad))))
