"""Reportes gerenciales (Sprint 2). Solo leen: piden los datos a los services de otros módulos y no
tienen tablas propias.

HU-7.04 (incluido): unidades por estado del ciclo con su cantidad y su valor (costo acumulado de la
hoja de costo mientras está en proceso; valor en libros financiero una vez dada de alta en la
flota), los días promedio en cada estado (contados como en las etapas de importación, desde el
último cambio del historial), las unidades que superan un plazo de días (parámetro con valor por
defecto en `comun/config.py`) y el listado de las unidades de cada estado.
Supuesto: una unidad vendida vale cero (ya no es capital invertido) mientras no exista la baja.
HU-7.04 (diferido): exportar a PDF y Excel (HU-7.09, Sprint 5).
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy.orm import Session

from app.modulos.compras import service as compras
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
