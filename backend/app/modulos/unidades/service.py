"""Reglas del módulo de unidades (Sprint 1, equipo B).

HU-1.05 (incluido): VIN de 17 caracteres sin I, O ni Q, con el dígito verificador de la posición 9
cuando el VIN es de Norteamérica (empieza con 1 a 5); VIN único; ficha mínima (marca, línea,
modelo, color, tipo de vehículo y línea de negocio de `configuracion`); un solo estado a la vez y
el historial de cada cambio con fecha, usuario y documento que lo originó.
HU-1.05 (diferido): placa, número de motor y expediente (criterio 2); los movimientos contables
ligados al VIN en la ficha (criterio 5), cuando exista `contabilidad` (HU-2.01/HU-2.03).

Pendiente para otras historias:
- HU-4.02 (compra en EE. UU.): la compra crea la unidad con `registrar_unidad` en su misma
  transacción (agregar un parámetro para no confirmar aquí) y el documento es la compra.
- HU-4.07 (etapas de importación): el orden tránsito → aduana → taller → lista se valida allá;
  aquí solo se impide lo que nunca tiene sentido (ver `_validar_transicion`).
- HU-1.09: con sesión, el router pasa `usuario.id` como `usuario_id` del cambio de estado.
"""

import re
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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


def registrar_unidad(db: Session, datos: UnidadEntrada, usuario_id: int | None = None) -> Unidad:
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


def _validar_transicion(actual: str, nuevo: str) -> None:
    if nuevo == actual:
        raise ErrorNegocio(f"La unidad ya está en estado {nuevo}")
    if actual == "vendida" and nuevo != "recuperada":
        raise ErrorNegocio("Una unidad vendida solo puede pasar a recuperada")
    if nuevo == "recuperada" and actual != "vendida":
        raise ErrorNegocio("Solo una unidad vendida puede pasar a recuperada")


def cambiar_estado(
    db: Session, vin: str, estado: str, documento: str, usuario_id: int | None = None
) -> Unidad:
    """Cambia el estado vigente y guarda el cambio en el historial, en la misma transacción."""
    if not documento:
        raise ErrorNegocio("Indique el documento que origina el cambio de estado")
    unidad = obtener_por_vin(db, vin)
    # Bloquea la fila: dos cambios simultáneos no dejan el historial desordenado.
    db.refresh(unidad, with_for_update=True)
    _validar_transicion(unidad.estado, estado)
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


def catalogos() -> dict[str, list[str]]:
    return {
        "estados": list(ESTADOS),
        "tipos_vehiculo": list(TIPOS_VEHICULO),
        "lineas_negocio": list(configuracion.LINEAS_NEGOCIO),
    }
