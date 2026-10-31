from decimal import Decimal

import pytest

from app.comun.dinero import convertir, redondear


def test_redondeo_mitad_hacia_arriba():
    assert redondear("2.675") == Decimal("2.68")
    assert redondear("2.665") == Decimal("2.67")
    assert redondear("-2.675") == Decimal("-2.68")


def test_redondeo_con_mas_decimales():
    assert redondear("7.123456789", 6) == Decimal("7.123457")


def test_conversion_usd_a_gtq_es_exacta():
    assert convertir("100.10", "7.71234567") == Decimal("772.0058015670")


def test_rechaza_float():
    with pytest.raises(TypeError):
        redondear(0.1)
