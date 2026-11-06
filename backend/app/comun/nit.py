"""Validación del NIT guatemalteco con su dígito verificador (módulo 11).

Compartido por todos los módulos que capturan un NIT: proveedores (HU-4.01), perfil fiscal de la
empresa (HU-1.01) y clientes (HU-6.01). No depende de ningún módulo ni de la base de datos.

El NIT son de 1 a 12 dígitos seguidos del verificador, que es un dígito o la letra K. Se acepta
con o sin guion y con espacios ("1234567-9", "12345679", " 576937-k ") y se guarda normalizado:
sin guion ni espacios, en mayúsculas y sin ceros a la izquierda ("12345679", "576937K"), para que
la regla de "no se repite" no dependa de cómo se escribió.

Cálculo del verificador: cada dígito del cuerpo se multiplica por su posición contada desde la
derecha empezando en 2; el verificador es (11 - suma % 11) % 11, y si da 10 se escribe K.

"CF" (consumidor final) no es un NIT: lo decide el módulo que lo admita (facturación, clientes).
"""

import re

_FORMA = re.compile(r"^(\d{1,12})([0-9K])$")


class NITInvalido(ValueError):
    """El texto no es un NIT válido. El mensaje está listo para mostrarse al usuario."""


def digito_verificador(cuerpo: str) -> str:
    """Verificador ("0"–"9" o "K") que corresponde al cuerpo del NIT (solo dígitos)."""
    if not cuerpo.isdigit():
        raise NITInvalido("El cuerpo del NIT solo puede tener dígitos")
    suma = sum(int(digito) * peso for peso, digito in enumerate(reversed(cuerpo), start=2))
    resto = (11 - suma % 11) % 11
    return "K" if resto == 10 else str(resto)


def normalizar_nit(texto: str) -> str:
    """Valida el NIT y lo devuelve normalizado. Lanza `NITInvalido` si la forma o el verificador fallan."""
    limpio = re.sub(r"[\s-]", "", texto or "").upper()
    coincidencia = _FORMA.match(limpio)
    if coincidencia is None:
        raise NITInvalido(
            "El NIT debe tener solo dígitos y un verificador (dígito o K), por ejemplo 1234567-9"
        )
    cuerpo, verificador = coincidencia.groups()
    cuerpo = cuerpo.lstrip("0")
    if not cuerpo:
        raise NITInvalido("El NIT no puede ser cero")
    if digito_verificador(cuerpo) != verificador:
        raise NITInvalido("El NIT no es válido: el dígito verificador no corresponde")
    return cuerpo + verificador


def es_nit_valido(texto: str) -> bool:
    try:
        normalizar_nit(texto)
    except NITInvalido:
        return False
    return True


def formatear_nit(nit: str) -> str:
    """Presentación con guion antes del verificador: "12345679" → "1234567-9"."""
    return f"{nit[:-1]}-{nit[-1]}"
