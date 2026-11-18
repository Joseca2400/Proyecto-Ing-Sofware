"""Reglas del módulo de unidades (Sprint 1, equipo B).

HU-1.05 (incluido): VIN de 17 caracteres sin I, O ni Q, con el dígito verificador de la posición 9
cuando el VIN es de Norteamérica (empieza con 1 a 5); VIN único; ficha mínima (marca, línea,
modelo, color, tipo de vehículo y línea de negocio de `configuracion`); un solo estado a la vez y
el historial de cada cambio con fecha, usuario y documento que lo originó.
HU-1.05 (diferido): placa, número de motor y expediente (criterio 2); los movimientos contables
ligados al VIN en la ficha (criterio 5), cuando exista `contabilidad` (HU-2.01/HU-2.03).

Pendiente para otras historias:
- HU-4.02 (compra en EE. UU.): hecho. La compra crea la unidad con `registrar_unidad` y
  `confirmar=False`, en su misma transacción; el documento del alta es la compra.
- HU-1.09: con sesión, el router pasa `usuario.id` como `usuario_id` del cambio de estado.

HU-4.07 (incluido): una unidad en importación avanza solo en orden, en tránsito → en aduana → en
taller → lista, sin saltarse etapas ni regresar (`_validar_transicion`); cada paso queda en el
historial y en la bitácora como cualquier cambio de estado. La unidad está "en importación"
mientras su historial no tenga ningún estado de lista en adelante. Una vez lista no regresa a
ninguna etapa; ya en flota o en venta no vuelve a tránsito, aduana ni lista, pero sí puede entrar
al taller (mantenimiento y postventa, que regula HU-5.01). El listado por etapa
(`etapas_importacion`) da los días que lleva cada unidad en su etapa, desde su último cambio en el
historial, y su costo acumulado (compra más gastos que suman al costo, calculado por `compras` con
la misma regla de la ficha), con el total de cada etapa.
HU-4.07 (diferido):
- Criterio 2: hecho. La orden de reacondicionamiento (HU-5.01) pasa la unidad a "en taller" al
  abrirse y a "lista" al cerrarse (HU-5.07), con `cambiar_estado(..., confirmar=False)`.
- Criterio 3: el paso a "lista" exigirá la DUCA registrada (HU-4.06) y que no haya órdenes de
  reacondicionamiento abiertas (HU-5.01); ver `_validar_paso_a_lista`.
- Las métricas de la etapa (promedios de días, unidades detenidas) quedan para HU-7.04.
"""

import re
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service as configuracion
from app.modulos.unidades.models import ESTADOS, CambioEstadoUnidad, Unidad
from app.modulos.unidades.schemas import UnidadEntrada

TIPOS_VEHICULO = ("sedan", "hatchback", "suv", "pickup", "camioneta", "microbus", "motocicleta", "otro")
ESTADOS_INICIALES = tuple(e for e in ESTADOS if e not in ("vendida", "recuperada"))
MODELO_MINIMO = 1981  # el VIN de 17 caracteres es obligatorio desde los modelos 1981

# ── Validación del VIN (norma de EE. UU., 49 CFR 565) ─────────────────────────

_FORMA_VIN = re.compile(r"[A-HJ-NPR-Z0-9]{17}")
_VALOR = {
    **{str(d): d for d in range(10)},
    **dict(zip("ABCDEFGH", range(1, 9), strict=True)),
    **dict(zip("JKLMN", range(1, 6), strict=True)),
    "P": 7,
    "R": 9,
    **dict(zip("STUVWXYZ", range(2, 10), strict=True)),
}
_PESOS = (8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2)
# Fabricados en Norteamérica (EE. UU., Canadá y México): ahí el verificador es obligatorio.
_REGION_NORTEAMERICA = "12345"


def digito_verificador(vin: str) -> str:
    """Dígito que corresponde a la posición 9 de un VIN con forma válida ("X" cuando el residuo es 10)."""
    residuo = sum(_VALOR[c] * peso for c, peso in zip(vin, _PESOS, strict=True)) % 11
    return "X" if residuo == 10 else str(residuo)


def validar_vin(vin: str) -> str:
    """Devuelve el VIN normalizado (sin espacios, en mayúsculas) o rechaza uno inválido."""
    vin = vin.strip().upper()
    if not _FORMA_VIN.fullmatch(vin):
        raise ErrorNegocio("El VIN debe tener 17 letras o dígitos, sin I, O ni Q")
    if vin[0] in _REGION_NORTEAMERICA:
        esperado = digito_verificador(vin)
        if vin[8] != esperado:
            raise ErrorNegocio(
                f"El VIN {vin} no pasa el dígito verificador: la posición 9 debería ser {esperado}"
            )
    return vin


# ── Unidades ──────────────────────────────────────────────────────────────────


def _vin_repetido(vin: str) -> ErrorNegocio:
    return ErrorNegocio(f"Ya existe una unidad con el VIN {vin}", status=409)


def _validar_linea_negocio(linea: str | None) -> None:
    lineas = configuracion.LINEAS_NEGOCIO
    if linea is not None and linea not in lineas:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea}. Use una de: {', '.join(lineas)}")


def registrar_unidad(
    db: Session, datos: UnidadEntrada, usuario_id: int | None = None, confirmar: bool = True
) -> Unidad:
    """Da de alta la unidad con el alta en su historial.

    Con `confirmar=False` solo la escribe (flush): la confirma el llamador junto con su documento,
    como la compra en EE. UU. (HU-4.02). Si algo falla, el llamador revierte y no queda la unidad.
    """
    vin = validar_vin(datos.vin)
    if not datos.marca or not datos.linea or not datos.color:
        raise ErrorNegocio("La marca, la línea y el color son obligatorios")
    modelo_maximo = date.today().year + 1
    if not MODELO_MINIMO <= datos.modelo <= modelo_maximo:
        raise ErrorNegocio(f"El modelo es el año del vehículo, entre {MODELO_MINIMO} y {modelo_maximo}")
    if datos.tipo_vehiculo not in TIPOS_VEHICULO:
        raise ErrorNegocio(f"Tipo de vehículo desconocido. Use uno de: {', '.join(TIPOS_VEHICULO)}")
    _validar_linea_negocio(datos.linea_negocio)
    if datos.estado not in ESTADOS_INICIALES:
        raise ErrorNegocio("Una unidad nueva no puede darse de alta como vendida ni recuperada")
    if db.scalar(select(Unidad.id).where(Unidad.vin == vin)) is not None:
        raise _vin_repetido(vin)

    unidad = Unidad(
        vin=vin,
        marca=datos.marca,
        linea=datos.linea,
        modelo=datos.modelo,
        color=datos.color,
        tipo_vehiculo=datos.tipo_vehiculo,
        linea_negocio=datos.linea_negocio,
        estado=datos.estado,
    )
    db.add(unidad)
    try:
        db.flush()
    except IntegrityError:
        # Dos altas simultáneas con el mismo VIN: la restricción UNIQUE decide.
        db.rollback()
        raise _vin_repetido(vin) from None
    db.add(
        CambioEstadoUnidad(
            unidad_id=unidad.id,
            estado_anterior=None,
            estado_nuevo=datos.estado,
            documento=datos.documento or "Alta de la unidad",
            usuario_id=usuario_id,
        )
    )
    if not confirmar:
        db.flush()
        return unidad
    db.commit()
    db.refresh(unidad)
    return unidad


def listar_unidades(db: Session, estado: str | None = None, buscar: str | None = None) -> list[Unidad]:
    """Consulta por estado o por texto (VIN, marca o línea), de la más reciente a la más antigua."""
    consulta = select(Unidad).order_by(Unidad.id.desc())
    if estado:
        consulta = consulta.where(Unidad.estado == estado)
    if buscar and buscar.strip():
        escapado = buscar.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        patron = f"%{escapado}%"
        consulta = consulta.where(
            or_(
                Unidad.vin.ilike(patron, escape="\\"),
                Unidad.marca.ilike(patron, escape="\\"),
                Unidad.linea.ilike(patron, escape="\\"),
            )
        )
    return list(db.scalars(consulta))


def buscar_por_vin(db: Session, vin: str) -> Unidad | None:
    return db.scalar(select(Unidad).where(Unidad.vin == vin.strip().upper()))


def obtener_por_vin(db: Session, vin: str) -> Unidad:
    unidad = buscar_por_vin(db, vin)
    if unidad is None:
        raise ErrorNegocio(f"No existe la unidad con VIN {vin.strip().upper()}", status=404)
    return unidad


def existe_vin(db: Session, vin: str) -> bool:
    """Para otros módulos: si la unidad está registrada (compras la exige en cada línea con VIN)."""
    return buscar_por_vin(db, vin) is not None


# ── HU-4.07: etapas de importación ────────────────────────────────────────────

ETAPAS_IMPORTACION = ("en_transito", "en_aduana", "en_taller", "lista")
_SIGUIENTE_ETAPA = dict(zip(ETAPAS_IMPORTACION, ETAPAS_IMPORTACION[1:], strict=False))
# Estados que solo tiene una unidad que ya terminó la importación (o que nunca la tuvo).
_FUERA_DE_IMPORTACION = tuple(e for e in ESTADOS if e not in ETAPAS_IMPORTACION[:-1])
_NOMBRE = {
    "en_transito": "en tránsito",
    "en_aduana": "en aduana",
    "en_taller": "en taller",
    "lista": "lista",
}


def _ya_salio_de_importacion(unidad_id):
    """Condición SQL: el historial de la unidad tiene algún estado de lista en adelante."""
    cambio = aliased(CambioEstadoUnidad)  # alias: la consulta de afuera también une el historial
    return (
        select(cambio.id)
        .where(cambio.unidad_id == unidad_id, cambio.estado_nuevo.in_(_FUERA_DE_IMPORTACION))
        .exists()
    )


def _en_importacion(db: Session, unidad: Unidad) -> bool:
    if unidad.estado not in _SIGUIENTE_ETAPA:
        return False
    return not db.scalar(select(_ya_salio_de_importacion(unidad.id)))


def esta_en_importacion(db: Session, vin: str) -> bool:
    """Para otros módulos: si la unidad sigue en la importación (aún no llega a lista ni a la flota)."""
    return _en_importacion(db, obtener_por_vin(db, vin))


def _validar_paso_a_lista(db: Session, unidad: Unidad) -> None:
    """HU-4.07, criterio 3: una unidad con una orden de taller abierta no pasa a "lista"; la pasa
    el cierre de su orden (HU-5.07). Diferido: exigir la DUCA registrada (`compras`, HU-4.06)."""
    # Import diferido: `taller` ya importa este service al cargarse.
    from app.modulos.taller import service as taller

    if taller.tiene_orden_abierta(db, unidad.vin):
        raise ErrorNegocio("La unidad tiene una orden de taller abierta; ciérrela para pasarla a lista", 409)


def _validar_transicion(actual: str, nuevo: str, en_importacion: bool) -> None:
    if nuevo == actual:
        raise ErrorNegocio(f"La unidad ya está en estado {nuevo}")
    if actual == "vendida" and nuevo != "recuperada":
        raise ErrorNegocio("Una unidad vendida solo puede pasar a recuperada")
    if nuevo == "recuperada" and actual != "vendida":
        raise ErrorNegocio("Solo una unidad vendida puede pasar a recuperada")
    if en_importacion:
        siguiente = _SIGUIENTE_ETAPA[actual]
        if nuevo != siguiente:
            raise ErrorNegocio(
                "La importación avanza en orden: en tránsito → en aduana → en taller → lista; "
                f"una unidad {_NOMBRE[actual]} solo puede pasar a {_NOMBRE[siguiente]}"
            )
    elif nuevo in ETAPAS_IMPORTACION and (nuevo != "en_taller" or actual == "lista"):
        # De lista no se regresa; ya en flota o en venta, el taller es mantenimiento o postventa
        # (HU-5.01) y sí se permite.
        raise ErrorNegocio(f"La unidad ya terminó la importación; no puede volver a {_NOMBRE[nuevo]}")


def cambiar_estado(
    db: Session,
    vin: str,
    estado: str,
    documento: str,
    usuario_id: int | None = None,
    confirmar: bool = True,
) -> Unidad:
    """Cambia el estado vigente y guarda el cambio en el historial, en la misma transacción.

    Con `confirmar=False` solo lo escribe (flush): lo confirma el llamador junto con su documento
    (la orden de reacondicionamiento, HU-5.01 y HU-5.07, lo usa para abrir y cerrar con su partida).
    """
    if not documento:
        raise ErrorNegocio("Indique el documento que origina el cambio de estado")
    unidad = obtener_por_vin(db, vin)
    # Bloquea la fila: dos cambios simultáneos no dejan el historial desordenado.
    db.refresh(unidad, with_for_update=True)
    en_importacion = _en_importacion(db, unidad)
    _validar_transicion(unidad.estado, estado, en_importacion)
    if en_importacion and estado == "lista":
        _validar_paso_a_lista(db, unidad)
    db.add(
        CambioEstadoUnidad(
            unidad_id=unidad.id,
            estado_anterior=unidad.estado,
            estado_nuevo=estado,
            documento=documento,
            usuario_id=usuario_id,
        )
    )
    unidad.estado = estado
    if not confirmar:
        db.flush()
        return unidad
    db.commit()
    db.refresh(unidad)
    return unidad


def historial(db: Session, vin: str) -> list[CambioEstadoUnidad]:
    """Cambios de estado de la unidad, del más antiguo (el alta) al más reciente."""
    unidad = obtener_por_vin(db, vin)
    return list(
        db.scalars(
            select(CambioEstadoUnidad)
            .where(CambioEstadoUnidad.unidad_id == unidad.id)
            .order_by(CambioEstadoUnidad.id)
        )
    )


def etapas_importacion(db: Session, estado: str | None = None) -> dict:
    """Unidades en importación (y las listas para la flota) con los días en su etapa y su costo.

    Los días cuentan desde el último cambio del historial, que es el que dejó la unidad en su
    estado actual. Una unidad en taller que ya terminó la importación (mantenimiento) no aparece.
    """
    if estado is not None and estado not in ETAPAS_IMPORTACION:
        raise ErrorNegocio(f"Etapa desconocida: {estado}. Use una de: {', '.join(ETAPAS_IMPORTACION)}")
    etapas = (estado,) if estado else ETAPAS_IMPORTACION
    ultimo_cambio = (
        select(func.max(CambioEstadoUnidad.id).label("id")).group_by(CambioEstadoUnidad.unidad_id).subquery()
    )
    salio = _ya_salio_de_importacion(Unidad.id)
    filas = db.execute(
        select(Unidad, CambioEstadoUnidad.fecha)
        .join(CambioEstadoUnidad, CambioEstadoUnidad.unidad_id == Unidad.id)
        .join(ultimo_cambio, ultimo_cambio.c.id == CambioEstadoUnidad.id)
        .where(Unidad.estado.in_(etapas), (Unidad.estado == "lista") | ~salio)
        .order_by(CambioEstadoUnidad.fecha, Unidad.id)
    ).all()

    # Import diferido: `compras` ya importa este service al cargarse.
    from app.modulos.compras import service as compras

    costos = compras.costos_de_unidades(db, [unidad.vin for unidad, _ in filas])
    ahora = datetime.now(UTC)
    orden = {etapa: i for i, etapa in enumerate(ETAPAS_IMPORTACION)}
    unidades = sorted(
        (
            {
                "vin": unidad.vin,
                "marca": unidad.marca,
                "linea": unidad.linea,
                "modelo": unidad.modelo,
                "color": unidad.color,
                "estado": unidad.estado,
                "desde": desde,
                "dias_en_etapa": max((ahora - desde).days, 0),
                "costo_total_gtq": costos[unidad.vin],
                "siguiente_etapa": _SIGUIENTE_ETAPA.get(unidad.estado),
            }
            for unidad, desde in filas
        ),
        # Por etapa y, dentro de cada una, las que llevan más tiempo primero.
        key=lambda u: orden[u["estado"]],
    )
    resumen = [
        {
            "estado": etapa,
            "unidades": sum(1 for u in unidades if u["estado"] == etapa),
            "costo_total_gtq": sum(
                (u["costo_total_gtq"] for u in unidades if u["estado"] == etapa), Decimal(0)
            ),
        }
        for etapa in etapas
    ]
    return {"etapas": resumen, "unidades": unidades}


def catalogos() -> dict[str, list[str]]:
    return {
        "estados": list(ESTADOS),
        "tipos_vehiculo": list(TIPOS_VEHICULO),
        "lineas_negocio": list(configuracion.LINEAS_NEGOCIO),
    }
