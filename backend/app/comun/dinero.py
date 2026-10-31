"""Precisión monetaria (acuerdo 2 de K1): siempre Decimal, nunca float.

En la base los montos son NUMERIC(18, 6) y el tipo de cambio NUMERIC(18, 8).
En la API viajan como texto para que el navegador no calcule con punto flotante.
"""

from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Numeric

MONTO = Numeric(18, 6)
TIPO_CAMBIO = Numeric(18, 8)

MONEDAS = ("GTQ", "USD")


def a_decimal(valor: Decimal | int | str) -> Decimal:
    """Convierte a Decimal. Rechaza float para no arrastrar errores de representación."""
    if isinstance(valor, float):
        raise TypeError("Los montos no se aceptan como float; use str o Decimal")
    return Decimal(valor)


def redondear(valor: Decimal | int | str, decimales: int = 2) -> Decimal:
    """Redondeo explícito, mitad hacia arriba, como en los documentos contables."""
    return a_decimal(valor).quantize(Decimal(1).scaleb(-decimales), rounding=ROUND_HALF_UP)


def convertir(monto: Decimal | str, tipo_cambio: Decimal | str) -> Decimal:
    """Convierte USD a GTQ con el tipo de cambio dado, sin redondear (se redondea al presentar)."""
    return a_decimal(monto) * a_decimal(tipo_cambio)
