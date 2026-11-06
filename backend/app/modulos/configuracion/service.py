"""Catálogo de cuentas y dimensiones analíticas (HU-1.02, HU-1.04).

`resolver_dimensiones` es lo que el motor contable llama por cada línea de una partida.
"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import Cuenta

TIPOS = ("activo", "pasivo", "patrimonio", "ingreso", "costo", "gasto")
NATURALEZAS = ("deudora", "acreedora")
LINEAS_NEGOCIO = ("alquiler", "venta", "taller", "financiamiento", "administracion")
VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA = "obligatorio", "opcional", "no_aplica"
MODOS_VIN = (VIN_OBLIGATORIO, VIN_OPCIONAL, VIN_NO_APLICA)


def listar_cuentas(db: Session, solo_detalle: bool = False) -> list[Cuenta]:
    """Ordenadas por código: con el nivel de cada una basta para dibujar el árbol."""
    consulta = select(Cuenta).order_by(Cuenta.codigo)
    if solo_detalle:
        consulta = consulta.where(Cuenta.es_detalle)
    return list(db.scalars(consulta))


def _cuenta(db: Session, cuenta_id: int) -> Cuenta:
    cuenta = db.get(Cuenta, cuenta_id)
    if cuenta is None:
        raise ErrorNegocio("La cuenta no existe", 404)
    return cuenta


def _fijar_dimensiones(cuenta: Cuenta, linea_obligatoria: bool, vin: str, linea_defecto: str | None) -> None:
    if vin not in MODOS_VIN:
        raise ErrorNegocio(f"VIN debe ser uno de: {', '.join(MODOS_VIN)}")
    if linea_defecto is not None and linea_defecto not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea_defecto}")
    if not cuenta.es_detalle and (linea_obligatoria or vin != VIN_NO_APLICA or linea_defecto):
        raise ErrorNegocio("Las dimensiones solo se definen en cuentas de detalle")
    cuenta.linea_obligatoria, cuenta.vin, cuenta.linea_defecto = linea_obligatoria, vin, linea_defecto


def crear_cuenta(
    db: Session,
    codigo: str,
    nombre: str,
    tipo: str,
    naturaleza: str,
    padre_id: int | None = None,
    es_detalle: bool = True,
    monetaria_usd: bool = False,
    linea_obligatoria: bool = False,
    vin: str = VIN_NO_APLICA,
    linea_defecto: str | None = None,
) -> Cuenta:
    codigo = codigo.strip()
    nombre = nombre.strip()
    if not codigo or not nombre:
        raise ErrorNegocio("El código y el nombre son obligatorios")
    if len(codigo) > 30 or len(nombre) > 200:
        raise ErrorNegocio("El código admite hasta 30 caracteres y el nombre hasta 200", 422)
    if tipo not in TIPOS or naturaleza not in NATURALEZAS:
        raise ErrorNegocio("Tipo o naturaleza desconocidos")
    if db.scalar(select(Cuenta.id).where(Cuenta.codigo == codigo)) is not None:
        raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409)
    nivel = 1
    if padre_id is not None:
        padre = _cuenta(db, padre_id)
        if padre.es_detalle:
            raise ErrorNegocio("Una cuenta de detalle no puede tener cuentas hijas")
        if padre.tipo != tipo:
            raise ErrorNegocio(f"La cuenta hija debe ser del mismo tipo que la cuenta padre ({padre.tipo})")
        nivel = padre.nivel + 1
    cuenta = Cuenta(
        codigo=codigo, nombre=nombre.strip(), tipo=tipo, naturaleza=naturaleza, nivel=nivel,
        padre_id=padre_id, es_detalle=es_detalle, monetaria_usd=monetaria_usd,
    )  # fmt: skip
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.add(cuenta)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if (
            getattr(exc.orig, "sqlstate", None) == "23505"
            and getattr(getattr(exc.orig, "diag", None), "constraint_name", None) == "cuentas_codigo_key"
        ):
            raise ErrorNegocio(f"Ya existe la cuenta {codigo}", 409) from exc
        raise
    return cuenta


def definir_dimensiones(
    db: Session, cuenta_id: int, linea_obligatoria: bool, vin: str, linea_defecto: str | None
) -> Cuenta:
    cuenta = _cuenta(db, cuenta_id)
    _fijar_dimensiones(cuenta, linea_obligatoria, vin, linea_defecto)
    db.commit()
    return cuenta


def resolver_dimensiones(db: Session, cuenta_id: int, linea: str | None, vin: str | None) -> str | None:
    """Valida una línea de partida contra su cuenta y devuelve la línea de negocio a guardar.

    Usa la línea por defecto de la cuenta si no se indicó una. Rechaza lo que la cuenta no admite.
    """
    cuenta = _cuenta(db, cuenta_id)
    if not cuenta.es_detalle:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} es de agrupación y no recibe movimientos")
    linea = linea or cuenta.linea_defecto
    if linea is not None and linea not in LINEAS_NEGOCIO:
        raise ErrorNegocio(f"Línea de negocio desconocida: {linea}")
    if linea is None and cuenta.linea_obligatoria:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige línea de negocio")
    vin = (vin or "").strip()
    if not vin and cuenta.vin == VIN_OBLIGATORIO:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} exige el VIN de la unidad")
    if vin and cuenta.vin == VIN_NO_APLICA:
        raise ErrorNegocio(f"La cuenta {cuenta.codigo} no admite VIN")
    return linea
