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

HU-3.01 (incluido, versión delgada): alta en flota (`dar_de_alta`) de una unidad "lista" sin orden
de taller abierta; su costo es el total de la hoja de costo (HU-4.08), que debe ser mayor que cero
y cuadrar con el mayor. En una transacción: registro del alta (VIN único), partida `alta_flota`
que traslada el costo de unidades en proceso a activo fijo – flota con el VIN, y paso a "en flota",
desde donde la unidad se puede alquilar. Una unidad lista no pasa a "en flota" sin su alta.
HU-3.01 (diferido): que el auxiliar registre el alta y el contador la apruebe (criterio 5, Sprint 5);
hoy solo el contador la registra.

HU-3.02 (incluido): parámetros de depreciación por unidad, financieros (vida útil en meses, valor
residual, línea recta) y fiscal (porcentaje anual), con valores por defecto por tipo de vehículo que
se proponen al alta y el contador cambia. Cada cambio es una versión nueva con su vigencia (desde el
mes en curso): las cuotas ya devengadas no se recalculan; la bitácora guarda cada versión.
`valor_en_libros` da la depreciación acumulada y el valor en libros a cualquier fecha (sin partidas:
la depreciación mensual contabilizada es HU-2.07, Sprint 3). Convención de meses (supuesto que
confirma el contador): el mes del alta no se deprecia; cada fin de mes posterior devenga una cuota.
"""

import re
from calendar import monthrange
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app.comun.dinero import redondear
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from app.modulos.unidades.models import (
    ESTADOS,
    AltaFlota,
    CambioEstadoUnidad,
    DepreciacionTipoVehiculo,
    ParametroDepreciacion,
    Unidad,
)
from app.modulos.unidades.schemas import UnidadEntrada

TIPOS_VEHICULO = ("sedan", "hatchback", "suv", "pickup", "camioneta", "microbus", "motocicleta", "otro")
# "alquilada" solo la pone el contrato de alquiler (HU-3.06).
ESTADOS_INICIALES = tuple(e for e in ESTADOS if e not in ("vendida", "recuperada", "alquilada"))
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
        raise ErrorNegocio("Una unidad nueva no puede darse de alta como vendida, recuperada ni alquilada")
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


def fijar_kilometraje(db: Session, vin: str, kilometraje: int) -> Unidad:
    """Para la devolución de un alquiler (HU-3.08): actualiza el kilometraje sin confirmar; lo
    confirma el llamador con su documento. El kilometraje no retrocede."""
    unidad = obtener_por_vin(db, vin)
    if unidad.kilometraje is not None and kilometraje < unidad.kilometraje:
        raise ErrorNegocio(
            f"El kilometraje {kilometraje} es menor que el registrado en la unidad ({unidad.kilometraje} km)"
        )
    unidad.kilometraje = kilometraje
    db.flush()
    return unidad


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
    # HU-3.06/HU-3.08: en flota → alquilada → en flota, o al taller si regresa con daños.
    if nuevo == "alquilada" and actual != "en_flota":
        raise ErrorNegocio("Solo una unidad en flota puede alquilarse")
    if actual == "alquilada" and nuevo not in ("en_flota", "en_taller"):
        raise ErrorNegocio("Una unidad alquilada solo puede volver a la flota o pasar al taller")
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
    (la orden de reacondicionamiento, HU-5.01 y HU-5.07, y el contrato de alquiler, HU-3.06).
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
    if unidad.estado == "lista" and estado == "en_flota" and alta_de_unidad(db, unidad.vin) is None:
        raise ErrorNegocio(
            "Una unidad lista entra a la flota con su alta como activo fijo (Alta en flota)", 409
        )
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


# ── HU-3.01: alta de la unidad como activo fijo de la flota ───────────────────

DOCUMENTO_ALTA = "alta_flota"


def alta_de_unidad(db: Session, vin: str) -> AltaFlota | None:
    return db.scalar(select(AltaFlota).where(AltaFlota.vin == vin.strip().upper()))


def costo_de_alta(db: Session, vin: str) -> Decimal | None:
    """Para `compras` (hoja de costo, HU-4.08): el costo congelado en el alta, o None sin alta."""
    alta = alta_de_unidad(db, vin)
    return alta.costo if alta else None


def candidatas_alta(db: Session) -> list[dict]:
    """Unidades en "lista" con el costo de su hoja de costo, su cuadre y si tienen orden abierta."""
    # Import diferido: `compras` y `taller` ya importan este service al cargarse.
    from app.modulos.compras import service as compras
    from app.modulos.taller import service as taller

    candidatas = []
    for unidad in listar_unidades(db, estado="lista"):
        hoja = compras.hoja_de_costo(db, unidad.vin)
        candidatas.append(
            {
                "vin": unidad.vin,
                "marca": unidad.marca,
                "linea": unidad.linea,
                "modelo": unidad.modelo,
                "tipo_vehiculo": unidad.tipo_vehiculo,
                "costo": hoja["total_gtq"],
                "cuadra": hoja["cuadra"],
                "diferencia": hoja["diferencia_gtq"],
                "orden_abierta": taller.tiene_orden_abierta(db, unidad.vin),
                **propuesta_depreciacion(db, unidad.tipo_vehiculo, hoja["total_gtq"]),
            }
        )
    return candidatas


def dar_de_alta(
    db: Session,
    vin: str,
    fecha: date,
    usuario_id: int | None = None,
    vida_util_meses: int | None = None,
    valor_residual: str | None = None,
    porcentaje_fiscal: str | None = None,
) -> AltaFlota:
    """Alta en flota: registro, partida (unidades en proceso → activo fijo – flota, con el VIN),
    primera versión de los parámetros de depreciación (HU-3.02; lo no enviado se toma de la
    propuesta del tipo de vehículo) y paso a "en flota", en una transacción, o nada."""
    from app.modulos.compras import service as compras  # import diferido, ver arriba
    from app.modulos.taller import service as taller

    unidad = obtener_por_vin(db, vin)
    db.refresh(unidad, with_for_update=True)  # dos altas simultáneas: la segunda ve "en flota"
    if unidad.estado != "lista":
        raise ErrorNegocio(
            f"Solo una unidad lista se da de alta en la flota; la unidad está {unidad.estado}", 409
        )
    if taller.tiene_orden_abierta(db, unidad.vin):
        raise ErrorNegocio("La unidad tiene una orden de taller abierta; ciérrela antes del alta", 409)
    if fecha > date.today():
        raise ErrorNegocio("La fecha del alta no puede ser futura")
    hoja = compras.hoja_de_costo(db, unidad.vin)
    costo = hoja["total_gtq"]
    if costo <= 0:
        raise ErrorNegocio("La hoja de costo de la unidad está en cero: no hay costo que dar de alta", 409)
    if not hoja["cuadra"]:
        raise ErrorNegocio(
            f"La hoja de costo no cuadra con el mayor (diferencia {hoja['diferencia_gtq']:.2f}); "
            "corrija la diferencia antes del alta",
            409,
        )
    propuesta = propuesta_depreciacion(db, unidad.tipo_vehiculo, costo)
    parametros = _parametros(
        costo,
        vida_util_meses if vida_util_meses is not None else propuesta["vida_util_meses"],
        valor_residual if valor_residual is not None else f"{propuesta['valor_residual']}",
        porcentaje_fiscal if porcentaje_fiscal is not None else f"{propuesta['porcentaje_fiscal']}",
    )
    try:
        activo = contabilidad.cuenta_regla(db, DOCUMENTO_ALTA, "activo_flota")
        en_proceso = contabilidad.cuenta_regla(db, DOCUMENTO_ALTA, "unidad_en_proceso")
        alta_id = db.scalar(select(func.nextval("alta_flota_id_seq")))
        partida = contabilidad.registrar_automatica(
            db,
            fecha=fecha,
            concepto=f"Alta en flota de la unidad {unidad.vin}",
            lineas=[
                LineaEntrada(
                    cuenta_id=activo,
                    lado="debe",
                    monto=f"{costo:.6f}",
                    linea_negocio="alquiler",
                    vin=unidad.vin,
                ),
                LineaEntrada(
                    cuenta_id=en_proceso,
                    lado="haber",
                    monto=f"{costo:.6f}",
                    linea_negocio=unidad.linea_negocio,
                    vin=unidad.vin,
                ),
            ],
            documento_tipo=DOCUMENTO_ALTA,
            documento_id=alta_id,
            usuario_id=usuario_id,
        )
        alta = AltaFlota(
            id=alta_id, vin=unidad.vin, fecha=fecha, costo=costo, partida_id=partida.id, usuario_id=usuario_id
        )
        db.add(alta)
        db.add(
            ParametroDepreciacion(vin=unidad.vin, vigente_desde=fecha, usuario_id=usuario_id, **parametros)
        )
        db.flush()  # el alta existe antes del cambio de estado, que la exige
        cambiar_estado(db, unidad.vin, "en_flota", f"Alta en flota {alta_id}", usuario_id, confirmar=False)
        db.commit()
    except ErrorNegocio:
        db.rollback()
        raise
    db.refresh(alta)
    return alta


# ── HU-3.02: parámetros de depreciación y valor en libros ─────────────────────


def _decimal(texto: str, campo: str, decimales: int) -> Decimal:
    try:
        valor = Decimal(str(texto).strip())
    except InvalidOperation:
        raise ErrorNegocio(f"{campo} no es un número válido") from None
    if not valor.is_finite() or valor < 0:
        raise ErrorNegocio(f"{campo} debe ser un número no negativo")
    if valor >= Decimal(10) ** 12:
        raise ErrorNegocio(f"{campo} excede el máximo permitido")
    if valor != round(valor, decimales):  # "7719.690000" vale; "7719.695" no
        raise ErrorNegocio(f"{campo} admite hasta {decimales} decimales")
    return valor


def _validar_vida_y_fiscal(vida_util_meses: int, fiscal: Decimal) -> None:
    if not 0 < vida_util_meses <= 600:
        raise ErrorNegocio("La vida útil es un número de meses entre 1 y 600")
    if not 0 < fiscal <= 100:
        raise ErrorNegocio("El porcentaje fiscal anual debe ser mayor que 0 y hasta 100")


def _parametros(costo: Decimal, vida_util_meses: int, valor_residual: str, porcentaje_fiscal: str) -> dict:
    """Valida los parámetros de una unidad contra su costo."""
    residual = _decimal(valor_residual, "El valor residual", 2)
    fiscal = _decimal(porcentaje_fiscal, "El porcentaje fiscal", 2)
    _validar_vida_y_fiscal(vida_util_meses, fiscal)
    if residual >= costo:
        raise ErrorNegocio("El valor residual debe ser menor que el costo de la unidad")
    return {"vida_util_meses": vida_util_meses, "valor_residual": residual, "porcentaje_fiscal": fiscal}


def _tipo(db: Session, tipo_vehiculo: str) -> DepreciacionTipoVehiculo | None:
    return db.scalar(
        select(DepreciacionTipoVehiculo).where(DepreciacionTipoVehiculo.tipo_vehiculo == tipo_vehiculo)
    )


def listar_depreciacion_tipos(db: Session) -> list[DepreciacionTipoVehiculo]:
    return list(db.scalars(select(DepreciacionTipoVehiculo).order_by(DepreciacionTipoVehiculo.id)))


def definir_depreciacion_tipo(
    db: Session,
    tipo_vehiculo: str,
    vida_util_meses: int,
    porcentaje_residual: str,
    porcentaje_fiscal: str,
    usuario_id: int | None = None,
) -> DepreciacionTipoVehiculo:
    """Cambia los valores por defecto de un tipo (criterio 2): solo afectan las altas siguientes y
    la bitácora guarda los anteriores."""
    tipo = _tipo(db, tipo_vehiculo)
    if tipo is None:
        raise ErrorNegocio(f"Tipo de vehículo desconocido: {tipo_vehiculo}", 404)
    residual = _decimal(porcentaje_residual, "El porcentaje residual", 2)
    fiscal = _decimal(porcentaje_fiscal, "El porcentaje fiscal", 2)
    _validar_vida_y_fiscal(vida_util_meses, fiscal)
    if residual >= 100:
        raise ErrorNegocio("El porcentaje residual debe ser menor que 100")
    tipo.vida_util_meses = vida_util_meses
    tipo.porcentaje_residual = residual
    tipo.porcentaje_fiscal = fiscal
    tipo.actualizado_por = usuario_id
    db.commit()
    db.refresh(tipo)
    return tipo


def propuesta_depreciacion(db: Session, tipo_vehiculo: str, costo: Decimal) -> dict:
    """Parámetros que se proponen al alta: los del tipo, con el residual en quetzales sobre el costo."""
    tipo = _tipo(db, tipo_vehiculo)
    if tipo is None:  # sin valores del tipo: 20 % fiscal de vehículos, 60 meses y sin residual
        return {
            "vida_util_meses": 60,
            "valor_residual": Decimal("0.00"),
            "porcentaje_fiscal": Decimal("20.00"),
        }
    return {
        "vida_util_meses": tipo.vida_util_meses,
        "valor_residual": redondear(costo * tipo.porcentaje_residual / 100, 2),
        "porcentaje_fiscal": tipo.porcentaje_fiscal,
    }


def parametros_depreciacion(db: Session, vin: str) -> list[ParametroDepreciacion]:
    """Versiones de los parámetros de la unidad, de la más antigua (la del alta) a la vigente."""
    unidad = obtener_por_vin(db, vin)
    return list(
        db.scalars(
            select(ParametroDepreciacion)
            .where(ParametroDepreciacion.vin == unidad.vin)
            .order_by(ParametroDepreciacion.vigente_desde)
        )
    )


def _indice_mes(fecha: date) -> int:
    return fecha.year * 12 + fecha.month - 1


def _fin_de_mes(indice: int) -> date:
    anio, mes = divmod(indice, 12)
    return date(anio, mes + 1, monthrange(anio, mes + 1)[1])


def meses_depreciados(fecha_alta: date, fecha: date) -> int:
    """Cuotas devengadas a `fecha`: una por cada mes cerrado (fin de mes <= fecha) posterior al mes
    del alta. El mes del alta no se deprecia; la primera cuota es la del cierre del mes siguiente."""
    cerrado = _indice_mes(fecha) - (0 if fecha == _fin_de_mes(_indice_mes(fecha)) else 1)
    return max(cerrado - _indice_mes(fecha_alta), 0)


def calcular_depreciacion(costo: Decimal, fecha_alta: date, versiones: list, fecha: date) -> dict:
    """Depreciación acumulada a `fecha`, financiera y fiscal, mes a mes.

    Cada mes usa la versión vigente a su fin de mes. Financiera, línea recta: la cuota es lo que
    falta depreciar (valor en libros menos residual) entre los meses que faltan de la vida útil,
    redondeada a centavos mitad hacia arriba; así un cambio aplica solo hacia adelante, la última
    cuota absorbe los centavos y nunca se baja del residual. Fiscal: costo por porcentaje anual
    entre 12, sin residual, hasta llegar a cero.
    """
    meses = meses_depreciados(fecha_alta, fecha)
    financiera = fiscal = Decimal(0)
    vigente = versiones[0]
    for k in range(1, meses + 1):
        fin = _fin_de_mes(_indice_mes(fecha_alta) + k)
        vigente = [v for v in versiones if v.vigente_desde <= fin][-1]
        faltan = max(vigente.vida_util_meses - (k - 1), 1)
        financiera += max(redondear((costo - financiera - vigente.valor_residual) / faltan, 2), Decimal(0))
        fiscal += min(redondear(costo * vigente.porcentaje_fiscal / 1200, 2), costo - fiscal)
    return {
        "meses_depreciados": meses,
        "vida_util_meses": vigente.vida_util_meses,
        "valor_residual": vigente.valor_residual,
        "porcentaje_fiscal": vigente.porcentaje_fiscal,
        "depreciacion_financiera": financiera,
        "valor_libros_financiero": costo - financiera,
        "depreciacion_fiscal": fiscal,
        "valor_libros_fiscal": costo - fiscal,
    }


def valor_en_libros(db: Session, vin: str, fecha: date) -> dict:
    """Costo, depreciación acumulada y valor en libros, financieros y fiscales, a `fecha`.

    Lo reutilizan la ficha, los reportes y la depreciación mensual (HU-2.07), para que todos usen el
    mismo cálculo. Requiere el alta en flota."""
    alta = alta_de_unidad(db, vin)
    if alta is None:
        raise ErrorNegocio(f"La unidad {vin.strip().upper()} no tiene alta en la flota", 404)
    return {
        "vin": alta.vin,
        "fecha": fecha,
        "fecha_alta": alta.fecha,
        "costo": alta.costo,
        **calcular_depreciacion(alta.costo, alta.fecha, parametros_depreciacion(db, alta.vin), fecha),
    }


def cambiar_parametros(
    db: Session,
    vin: str,
    vigente_desde: date,
    vida_util_meses: int,
    valor_residual: str,
    porcentaje_fiscal: str,
    usuario_id: int | None = None,
) -> ParametroDepreciacion:
    """Nueva versión de los parámetros, prospectiva (criterio 3): vigente desde el mes en curso o
    uno posterior, así no recalcula cuotas de meses ya cerrados."""
    alta = alta_de_unidad(db, vin)
    if alta is None:
        raise ErrorNegocio(f"La unidad {vin.strip().upper()} no tiene alta en la flota", 404)
    ultima = parametros_depreciacion(db, alta.vin)[-1]
    if vigente_desde < date.today().replace(day=1):
        raise ErrorNegocio("El cambio es prospectivo: su vigencia no puede ser anterior al mes en curso")
    if vigente_desde <= ultima.vigente_desde:
        raise ErrorNegocio(
            f"Ya hay parámetros vigentes desde el {ultima.vigente_desde}; use una fecha posterior"
        )
    parametros = _parametros(alta.costo, vida_util_meses, valor_residual, porcentaje_fiscal)
    # Meses ya devengados al cierre del mes anterior a la vigencia: la vida nueva debe superarlos.
    devengados = meses_depreciados(alta.fecha, _fin_de_mes(_indice_mes(vigente_desde) - 1))
    if vida_util_meses <= devengados:
        raise ErrorNegocio(f"La vida útil debe ser mayor que los {devengados} meses ya depreciados")
    version = ParametroDepreciacion(
        vin=alta.vin, vigente_desde=vigente_desde, usuario_id=usuario_id, **parametros
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def catalogos() -> dict[str, list[str]]:
    return {
        "estados": list(ESTADOS),
        "tipos_vehiculo": list(TIPOS_VEHICULO),
        "lineas_negocio": list(configuracion.LINEAS_NEGOCIO),
    }
