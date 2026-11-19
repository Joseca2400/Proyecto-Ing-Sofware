"""Reportes gerenciales (Sprint 2). Solo leen: piden los datos a los services de otros módulos y no
tienen tablas propias.

HU-7.04 (incluido): unidades por estado del ciclo con su cantidad y su valor (costo acumulado de la
hoja de costo mientras está en proceso; valor en libros financiero una vez dada de alta en la
flota), los días promedio en cada estado (contados como en las etapas de importación, desde el
último cambio del historial), las unidades que superan un plazo de días (parámetro con valor por
defecto en `comun/config.py`) y el listado de las unidades de cada estado.
Supuesto: una unidad vendida vale cero (ya no es capital invertido) mientras no exista la baja.
HU-7.04 (diferido): exportar a PDF y Excel (HU-7.09, Sprint 5).

HU-3.13 (incluido): rentabilidad por unidad y por contrato, en quetzales, leída del mayor
(partidas contabilizadas) filtrado por VIN, así que cuadra con la contabilidad. Las cuentas de
cada concepto salen de las reglas `rentabilidad` (ingreso de alquiler, depreciación,
mantenimiento, seguro y marchamo) que el contador cambia en su pantalla; un concepto cuya regla
no tiene cuenta se muestra como pendiente, sin cifra (hoy seguro y marchamo).
- Por unidad (las dadas de alta en la flota) y período: ingreso de alquiler (haber − debe),
  depreciación, mantenimiento, seguro y marchamo (debe − haber) y resultado = ingreso − costos.
- Por contrato (salida dentro del período): de las partidas de sus facturas, el ingreso del primer
  renglón es el alquiler por tiempo y el de los demás, cargos adicionales (km excedentes y, con
  HU-3.09, los otros cargos); el renglón de la partida sigue el orden de la factura.
- Exportar cada consulta a CSV (UTF-8 con BOM, para que Excel respete las tildes).
HU-3.13 (diferido): exportar a Excel (HU-7.09, Sprint 5); costos directos del contrato (taller por
daños y combustible repuesto), que hoy se muestran pendientes porque ni la orden de taller
(Sprint 5) ni el cargo de combustible (HU-3.09) se ligan aún al contrato.
"""

import csv
import io
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.modulos.alquileres import service as alquileres
from app.modulos.compras import service as compras
from app.modulos.contabilidad import service as contabilidad
from app.modulos.facturacion import service as facturacion
from app.modulos.unidades import service as unidades


def unidades_por_etapa(db: Session, limite_dias: int) -> dict:
    filas = unidades.dias_en_estado(db)
    costos = compras.costos_de_unidades(db, [u["vin"] for u in filas])
    hoy = date.today()
    lista = []
    for fila in filas:
        # shortcut: una consulta de valor en libros por unidad; agregar una por lote si la flota crece.
        con_alta = unidades.costo_de_alta(db, fila["vin"]) is not None
        if fila["estado"] == "vendida":
            valor = Decimal(0)
        elif con_alta:
            valor = unidades.valor_en_libros(db, fila["vin"], hoy)["valor_libros_financiero"]
        else:
            valor = costos[fila["vin"]]
        lista.append(
            {
                **fila,
                "valor": valor,
                "valor_en_libros": con_alta,
                "excede": fila["dias_en_estado"] > limite_dias,
            }
        )
    orden = {estado: i for i, estado in enumerate(unidades.ESTADOS)}
    lista.sort(key=lambda u: (orden[u["estado"]], -u["dias_en_estado"]))
    estados = []
    for estado in unidades.ESTADOS:
        del_estado = [u for u in lista if u["estado"] == estado]
        dias = [u["dias_en_estado"] for u in del_estado]
        estados.append(
            {
                "estado": estado,
                "unidades": len(del_estado),
                "valor": sum((u["valor"] for u in del_estado), Decimal(0)),
                "dias_promedio": int((Decimal(sum(dias)) / len(dias)).quantize(Decimal(1), ROUND_HALF_UP))
                if dias
                else 0,
                "excedidas": sum(1 for u in del_estado if u["excede"]),
            }
        )
    return {
        "limite_dias": limite_dias,
        "valor_total": sum((e["valor"] for e in estados), Decimal(0)),
        "estados": estados,
        "unidades": lista,
    }


# ── HU-3.13: rentabilidad por unidad y por contrato ───────────────────────────

REGLA_RENTABILIDAD = "rentabilidad"
# El ingreso es acreedor (haber − debe); los costos, deudores (debe − haber).
CONCEPTOS_INGRESO = ("ingreso_alquiler",)
CONCEPTOS_COSTO = ("depreciacion", "mantenimiento", "seguro", "marchamo")
NOMBRES = {
    "ingreso_alquiler": "Ingreso de alquiler",
    "depreciacion": "Depreciación",
    "mantenimiento": "Mantenimiento",
    "seguro": "Seguro",
    "marchamo": "Marchamo",
}
PENDIENTE_COSTOS_DIRECTOS = (
    "Costos directos del contrato (taller por daños y combustible repuesto): pendientes hasta que "
    "la orden de taller (Sprint 5) y el cargo de combustible (HU-3.09) se liguen al contrato."
)


def cuentas_rentabilidad(db: Session) -> dict[str, int | None]:
    """Cuenta de cada concepto según las reglas `rentabilidad`, o None si la regla no tiene cuenta."""
    cuentas: dict[str, int | None] = {}
    for concepto in (*CONCEPTOS_INGRESO, *CONCEPTOS_COSTO):
        try:
            cuentas[concepto] = contabilidad.cuenta_regla(db, REGLA_RENTABILIDAD, concepto)
        except ErrorNegocio:
            cuentas[concepto] = None
    return cuentas


def pendientes_de_reglas(cuentas: dict[str, int | None]) -> list[str]:
    return [
        f"{NOMBRES[concepto]}: pendiente; asigne una cuenta a la regla «rentabilidad · {concepto}»."
        for concepto, cuenta in cuentas.items()
        if cuenta is None
    ]


def cifras_de_unidad(
    db: Session, vin: str, cuentas: dict[str, int | None], desde: date | None, hasta: date | None
) -> dict:
    """Ingreso y costos de la unidad en el rango (sin fechas: toda su historia), del mayor filtrado
    por su VIN, y el resultado. Un concepto sin cuenta vale None (pendiente) y no entra al resultado.

    shortcut: un balance por VIN; agrupar por VIN en `contabilidad` si la flota crece.
    """
    movimientos = {
        fila["cuenta_id"]: fila
        for fila in contabilidad.balance_comprobacion(db, desde, hasta, vin=vin)["filas"]
    }
    cifras: dict[str, Decimal | None] = {}
    for concepto, cuenta in cuentas.items():
        if cuenta is None:
            cifras[concepto] = None
            continue
        fila = movimientos.get(cuenta)
        neto = (fila["debe"] - fila["haber"]) if fila else Decimal(0)
        cifras[concepto] = (-neto if concepto in CONCEPTOS_INGRESO else neto) + 0
    ingresos = sum((cifras[c] or 0 for c in CONCEPTOS_INGRESO), Decimal(0))
    costos = sum((cifras[c] or 0 for c in CONCEPTOS_COSTO), Decimal(0))
    return {**cifras, "costos": costos, "resultado": ingresos - costos}


def _rango(desde: date | None, hasta: date | None) -> tuple[date, date]:
    """Por defecto, del 1 de enero del año en curso a hoy."""
    hoy = date.today()
    desde = desde or date(hoy.year, 1, 1)
    hasta = hasta or hoy
    if desde > hasta:
        raise ErrorNegocio("La fecha inicial no puede ser posterior a la final")
    return desde, hasta


def sumar(filas: list[dict], campos: tuple[str, ...]) -> dict[str, Decimal | None]:
    """Totales por campo; un campo pendiente (None) en todas las filas queda pendiente."""
    totales: dict[str, Decimal | None] = {}
    for campo in campos:
        valores = [fila[campo] for fila in filas if fila[campo] is not None]
        totales[campo] = sum(valores, Decimal(0)) if valores or not filas else None
    return totales


CAMPOS_UNIDAD = (*CONCEPTOS_INGRESO, *CONCEPTOS_COSTO, "costos", "resultado")


def rentabilidad_unidades(
    db: Session, desde: date | None = None, hasta: date | None = None, vin: str | None = None
) -> dict:
    """HU-3.13: por cada unidad dada de alta en la flota, sus cifras del período."""
    desde, hasta = _rango(desde, hasta)
    cuentas = cuentas_rentabilidad(db)
    filas = []
    vin = vin.strip().upper() if vin and vin.strip() else None
    for unidad in unidades.listar_unidades(db):
        alta = unidades.alta_de_unidad(db, unidad.vin)
        if alta is None or (vin and unidad.vin != vin):
            continue
        filas.append(
            {
                "vin": unidad.vin,
                "marca": unidad.marca,
                "linea": unidad.linea,
                "modelo": unidad.modelo,
                "estado": unidad.estado,
                "fecha_alta": alta.fecha,
                **cifras_de_unidad(db, unidad.vin, cuentas, desde, hasta),
            }
        )
    filas.sort(key=lambda fila: fila["vin"])
    return {
        "desde": desde,
        "hasta": hasta,
        "unidades": filas,
        "totales": sumar(filas, CAMPOS_UNIDAD),
        "pendientes": pendientes_de_reglas(cuentas),
    }


def _ingresos_de_facturas(db: Session, cuenta: int, vin: str, facturas: set[str]) -> tuple[Decimal, Decimal]:
    """(alquiler por tiempo, cargos adicionales) del mayor de la cuenta de ingreso para el VIN, solo
    en las partidas de esas facturas (y sus reversiones). La partida lleva un renglón de ingreso por
    renglón de la factura, en su orden, y el primero de un contrato es el tiempo; los demás, cargos."""
    alquiler = cargos = Decimal(0)
    vistas: set[int] = set()
    for movimiento in contabilidad.mayor(db, cuenta, vin=vin)["movimientos"]:
        if (
            movimiento["documento_tipo"] != facturacion.DOCUMENTO
            or movimiento["documento_id"] not in facturas
        ):
            continue
        monto = movimiento["haber"] - movimiento["debe"]
        if movimiento["partida_id"] in vistas:
            cargos += monto
        else:
            vistas.add(movimiento["partida_id"])
            alquiler += monto
    return alquiler, cargos


CAMPOS_CONTRATO = ("alquiler", "cargos_adicionales", "ingresos", "costos_directos", "resultado")


def rentabilidad_contratos(
    db: Session, desde: date | None = None, hasta: date | None = None, vin: str | None = None
) -> dict:
    """HU-3.13: por cada contrato con salida en el período, sus ingresos facturados según el mayor."""
    desde, hasta = _rango(desde, hasta)
    cuenta = cuentas_rentabilidad(db)["ingreso_alquiler"]
    pendientes = pendientes_de_reglas({"ingreso_alquiler": cuenta}) + [PENDIENTE_COSTOS_DIRECTOS]
    clientes: dict[int, str] = {}
    filas = []
    for contrato in alquileres.listar_contratos(db, vin=vin.strip() if vin and vin.strip() else None):
        if not desde <= contrato.salida.date() <= hasta:
            continue
        facturas = [
            f for f in facturacion.facturas_de_origen(db, "contrato", contrato.id) if f.partida_id is not None
        ]
        alquiler = cargos = Decimal(0)
        if cuenta is not None and facturas:
            alquiler, cargos = _ingresos_de_facturas(db, cuenta, contrato.vin, {str(f.id) for f in facturas})
        if contrato.cliente_id not in clientes:
            clientes[contrato.cliente_id] = facturacion.obtener_cliente(db, contrato.cliente_id).nombre
        ingresos = alquiler + cargos
        costos_directos = Decimal(0)  # pendiente: ver PENDIENTE_COSTOS_DIRECTOS
        filas.append(
            {
                "contrato_id": contrato.id,
                "numero": contrato.numero,
                "vin": contrato.vin,
                "cliente": clientes[contrato.cliente_id],
                "salida": contrato.salida,
                "devolucion": contrato.devolucion,
                "estado": contrato.estado,
                "facturas": [f"{f.serie}-{f.numero}" for f in facturas],
                "alquiler": alquiler,
                "cargos_adicionales": cargos,
                "ingresos": ingresos,
                "costos_directos": costos_directos,
                "resultado": ingresos - costos_directos,
            }
        )
    return {
        "desde": desde,
        "hasta": hasta,
        "contratos": filas,
        "totales": sumar(filas, CAMPOS_CONTRATO),
        "pendientes": pendientes,
    }


def _cifra(valor: Decimal | None) -> str:
    return "pendiente" if valor is None else f"{valor:.2f}"


def _csv(encabezados: list[str], filas: list[list]) -> str:
    """CSV con BOM para que Excel abra las tildes en UTF-8."""
    salida = io.StringIO()
    escritor = csv.writer(salida, lineterminator="\r\n")
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return "﻿" + salida.getvalue()


def csv_rentabilidad_unidades(reporte: dict) -> str:
    campos = CAMPOS_UNIDAD
    encabezados = ["VIN", "Marca", "Línea", "Modelo", "Estado", "Alta en flota"]
    encabezados += [f"{NOMBRES.get(c, c.capitalize())} (GTQ)" for c in campos]
    filas = [
        [u["vin"], u["marca"], u["linea"], u["modelo"], u["estado"], u["fecha_alta"].isoformat()]
        + [_cifra(u[c]) for c in campos]
        for u in reporte["unidades"]
    ]
    filas.append(["Total", "", "", "", "", ""] + [_cifra(reporte["totales"][c]) for c in campos])
    return _csv(encabezados, filas)


def csv_rentabilidad_contratos(reporte: dict) -> str:
    encabezados = [
        "Contrato", "VIN", "Cliente", "Salida", "Devolución", "Estado", "Facturas", "Alquiler (GTQ)",
        "Cargos adicionales (GTQ)", "Ingresos (GTQ)", "Costos directos (GTQ)", "Resultado (GTQ)",
    ]  # fmt: skip
    filas = [
        [
            c["numero"],
            c["vin"],
            c["cliente"],
            c["salida"].date().isoformat(),
            c["devolucion"].date().isoformat() if c["devolucion"] else "",
            c["estado"],
            " ".join(c["facturas"]),
        ]  # fmt: skip
        + [_cifra(c[campo]) for campo in CAMPOS_CONTRATO]
        for c in reporte["contratos"]
    ]
    filas.append(["Total", "", "", "", "", "", ""] + [_cifra(reporte["totales"][c]) for c in CAMPOS_CONTRATO])
    return _csv(encabezados, filas)
