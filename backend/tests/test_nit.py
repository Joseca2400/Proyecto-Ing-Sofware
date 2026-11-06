"""Validación del NIT con dígito verificador (`comun/nit.py`), compartida por HU-4.01, HU-1.01 y HU-6.01."""

import pytest

from app.comun.nit import NITInvalido, digito_verificador, es_nit_valido, formatear_nit, normalizar_nit


@pytest.mark.parametrize(
    ("cuerpo", "verificador"),
    [
        ("1234567", "9"),  # 8·1 + 7·2 + 6·3 + 5·4 + 4·5 + 3·6 + 2·7 = 112; (11 - 112 % 11) % 11 = 9
        ("1669394", "9"),  # NIT de la SAT
        ("576937", "K"),  # el resto da 10 y se escribe K
        ("14", "0"),
        ("9", "4"),
    ],
)
def test_digito_verificador(cuerpo, verificador):
    assert digito_verificador(cuerpo) == verificador


@pytest.mark.parametrize(
    ("texto", "normalizado"),
    [
        ("1234567-9", "12345679"),
        ("12345679", "12345679"),
        ("  1234567 - 9 ", "12345679"),
        ("576937-k", "576937K"),
        ("576937K", "576937K"),
        ("001234567-9", "12345679"),  # los ceros a la izquierda no cambian el verificador
        ("16693949", "16693949"),
    ],
)
def test_normaliza_los_nit_validos(texto, normalizado):
    assert normalizar_nit(texto) == normalizado
    assert es_nit_valido(texto)


@pytest.mark.parametrize(
    "texto",
    ["1234567-8", "576937-0", "12345670", "16693948"],
)
def test_rechaza_verificador_incorrecto(texto):
    with pytest.raises(NITInvalido, match="dígito verificador"):
        normalizar_nit(texto)


@pytest.mark.parametrize(
    "texto",
    ["", "   ", "CF", "K", "7", "12A4567-9", "1234567-X", "1234567890123-4"],
)
def test_rechaza_forma_invalida(texto):
    assert not es_nit_valido(texto)


def test_rechaza_nit_cero():
    # "0-0" cumple el verificador (suma 0 → 0) pero no es un NIT.
    with pytest.raises(NITInvalido, match="cero"):
        normalizar_nit("0-0")


def test_formatea_con_guion():
    assert formatear_nit("12345679") == "1234567-9"
    assert formatear_nit("576937K") == "576937-K"
