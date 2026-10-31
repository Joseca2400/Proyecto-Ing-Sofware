"""Utilidades comunes: errores de negocio, redondeo, bitácora, validaciones y datos iniciales."""

import re
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Bitacora, Cuenta, ExigenciaVin, LineaNegocio, Rol, Usuario


class ErrorNegocio(Exception):
    def __init__(self, mensaje: str, status: int = 422):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.status = status


class NoEncontrado(ErrorNegocio):
    def __init__(self, mensaje: str):
        super().__init__(mensaje, 404)


class Conflicto(ErrorNegocio):
    def __init__(self, mensaje: str):
        super().__init__(mensaje, 409)


class Prohibido(ErrorNegocio):
    def __init__(self, mensaje: str):
        super().__init__(mensaje, 403)


CENTAVO = Decimal("0.01")


def q2(valor) -> Decimal:
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def obtener(db: Session, modelo, id_: int, nombre: str):
    obj = db.get(modelo, id_)
    if obj is None:
        raise NoEncontrado(f"{nombre} {id_} no existe")
    return obj


# ----------------------------------------------------------------- Bitácora (HU-1.11)

def registrar_bitacora(db: Session, usuario: str, accion: str, entidad: str,
                       entidad_id: int | None = None, vin: str | None = None,
                       detalle: str | None = None) -> None:
    """Agrega un registro. La bitácora no tiene endpoints de edición ni borrado."""
    db.add(Bitacora(usuario=usuario, accion=accion, entidad=entidad,
                    entidad_id=entidad_id, vin=vin, detalle=detalle))


# ----------------------------------------------------------------- VIN (HU-1.05)

_TRANSLIT = {
    **{str(d): d for d in range(10)},
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 6, "G": 7, "H": 8,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "P": 7, "R": 9,
    "S": 2, "T": 3, "U": 4, "V": 5, "W": 6, "X": 7, "Y": 8, "Z": 9,
}
_PESOS = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]


def digito_verificador_vin(vin: str) -> str:
    total = sum(_TRANSLIT[c] * p for c, p in zip(vin, _PESOS))
    resto = total % 11
    return "X" if resto == 10 else str(resto)


def validar_vin(vin: str) -> str:
    """Valida longitud, caracteres y dígito verificador de la posición 9 (norma de EE. UU.)."""
    vin = vin.strip().upper()
    if len(vin) != 17:
        raise ErrorNegocio("El VIN debe tener 17 caracteres")
    if re.search(r"[IOQ]", vin):
        raise ErrorNegocio("El VIN no puede contener las letras I, O ni Q")
    if not re.fullmatch(r"[A-HJ-NPR-Z0-9]{17}", vin):
        raise ErrorNegocio("El VIN contiene caracteres inválidos")
    esperado = digito_verificador_vin(vin)
    if vin[8] != esperado:
        raise ErrorNegocio(f"VIN inválido: el dígito verificador (posición 9) debería ser {esperado}")
    return vin


# ----------------------------------------------------------------- NIT de Guatemala (HU-1.01, HU-6.01)

def digito_verificador_nit(numero: str) -> str:
    n = len(numero)
    total = sum(int(d) * (n + 1 - i) for i, d in enumerate(numero))
    resto = (11 - total % 11) % 11
    return "K" if resto == 10 else str(resto)


def validar_nit(nit: str) -> str:
    """Normaliza (sin guiones ni espacios, K mayúscula) y valida el dígito verificador."""
    limpio = re.sub(r"[\s-]", "", nit).upper()
    if not re.fullmatch(r"\d{1,12}[0-9K]", limpio):
        raise ErrorNegocio("El NIT debe tener sólo dígitos y terminar en un dígito o K")
    if digito_verificador_nit(limpio[:-1]) != limpio[-1]:
        raise ErrorNegocio("NIT inválido: el dígito verificador no corresponde")
    return limpio


# ----------------------------------------------------------------- Datos iniciales

# Catálogo mínimo del corte (HU-1.02). El catálogo definitivo se decide con el contador.
# (código, nombre, tipo, naturaleza, es_detalle, monetaria_usd, exige_vin, línea por defecto)
CATALOGO_INICIAL = [
    ("1", "ACTIVO", "ACTIVO", "DEUDORA", False, False, "NO_APLICA", None),
    ("1.1", "Activo corriente", "ACTIVO", "DEUDORA", False, False, "NO_APLICA", None),
    ("1.1.01", "Bancos – quetzales", "ACTIVO", "DEUDORA", True, False, "NO_APLICA", "ADMINISTRACION"),
    ("1.1.02", "Bancos – dólares", "ACTIVO", "DEUDORA", True, True, "NO_APLICA", "ADMINISTRACION"),
    ("1.1.03", "Clientes – quetzales", "ACTIVO", "DEUDORA", True, False, "OPCIONAL", None),
    ("1.1.04", "Clientes – dólares", "ACTIVO", "DEUDORA", True, True, "OPCIONAL", None),
    ("1.1.05", "IVA crédito fiscal", "ACTIVO", "DEUDORA", True, False, "OPCIONAL", "ADMINISTRACION"),
    ("1.1.06", "Unidades en proceso (importación y reacondicionamiento)", "ACTIVO", "DEUDORA", True, False, "OBLIGATORIO", "ALQUILER"),
    ("1.2", "Activo no corriente", "ACTIVO", "DEUDORA", False, False, "NO_APLICA", None),
    ("1.2.01", "Activo fijo – flota", "ACTIVO", "DEUDORA", True, False, "OBLIGATORIO", "ALQUILER"),
    ("2", "PASIVO", "PASIVO", "ACREEDORA", False, False, "NO_APLICA", None),
    ("2.1", "Pasivo corriente", "PASIVO", "ACREEDORA", False, False, "NO_APLICA", None),
    ("2.1.01", "Proveedores locales", "PASIVO", "ACREEDORA", True, False, "OPCIONAL", None),
    ("2.1.02", "Proveedores del exterior", "PASIVO", "ACREEDORA", True, True, "OPCIONAL", None),
    ("2.1.03", "IVA débito fiscal", "PASIVO", "ACREEDORA", True, False, "OPCIONAL", "ADMINISTRACION"),
    ("3", "PATRIMONIO", "PATRIMONIO", "ACREEDORA", False, False, "NO_APLICA", None),
    ("3.1.01", "Capital social", "PATRIMONIO", "ACREEDORA", True, False, "NO_APLICA", "ADMINISTRACION"),
    ("4", "INGRESOS", "INGRESO", "ACREEDORA", False, False, "NO_APLICA", None),
    ("4.1.01", "Ingresos por alquiler", "INGRESO", "ACREEDORA", True, False, "OBLIGATORIO", "ALQUILER"),
    ("5", "COSTOS", "COSTO", "DEUDORA", False, False, "NO_APLICA", None),
    ("5.1.01", "Mano de obra aplicada – taller", "COSTO", "ACREEDORA", True, False, "NO_APLICA", "TALLER"),
    ("6", "GASTOS", "GASTO", "DEUDORA", False, False, "NO_APLICA", None),
    ("6.1.01", "Mantenimiento de flota", "GASTO", "DEUDORA", True, False, "OBLIGATORIO", "ALQUILER"),
    ("6.1.02", "Gastos de administración", "GASTO", "DEUDORA", True, False, "NO_APLICA", "ADMINISTRACION"),
    ("7", "OTROS INGRESOS Y GASTOS", "GASTO", "DEUDORA", False, False, "NO_APLICA", None),
    ("7.1.01", "Diferencial cambiario realizado", "GASTO", "DEUDORA", True, False, "NO_APLICA", "ADMINISTRACION"),
]

USUARIOS_INICIALES = [
    ("aux", "Ana López", Rol.AUXILIAR),
    ("contador", "Carlos Pérez", Rol.CONTADOR),
    ("gerente", "María Gómez", Rol.GERENTE_FINANCIERO),
    ("gerencia", "Luis Ramírez", Rol.GERENCIA),
]


def sembrar_datos_iniciales(db: Session) -> None:
    """Crea el catálogo y los usuarios de ejemplo si la base está vacía. Idempotente."""
    if db.scalar(select(Cuenta).limit(1)) is None:
        for codigo, nombre, tipo, nat, det, usd, vin, linea in CATALOGO_INICIAL:
            db.add(Cuenta(codigo=codigo, nombre=nombre, tipo=tipo, naturaleza=nat, es_detalle=det,
                          monetaria_usd=usd, exige_vin=ExigenciaVin(vin),
                          linea_defecto=LineaNegocio(linea) if linea else None))
    if db.scalar(select(Usuario).limit(1)) is None:
        from app import config
        from app.seguridad import hash_password
        for usuario, nombre, rol in USUARIOS_INICIALES:
            db.add(Usuario(usuario=usuario, nombre=nombre, rol=rol,
                           password_hash=hash_password(config.PASSWORD_INICIAL)))
    db.commit()
