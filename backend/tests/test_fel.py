"""Adaptador FEL: el certificador simulado (determinista, sin red) y su selección por configuración."""

import xml.etree.ElementTree as ET
from datetime import date
from decimal import Decimal

import pytest

from app.comun import config, fel


def _linea(descripcion: str) -> fel.LineaFEL:
    total = Decimal("1120.00")
    return fel.LineaFEL(descripcion, Decimal(1), total, total, Decimal("120.00"))


def _documento(**cambios) -> fel.DocumentoFEL:
    datos = {
        "referencia": "15",
        "emisor_nit": "12345679",
        "emisor_nombre": "Kilómetro Cero, S. A.",
        "receptor_id": "12345679",
        "receptor_tipo": "nit",
        "receptor_nombre": "Transportes del Norte",
        "fecha": date(2026, 10, 20),
        "moneda": "GTQ",
        "tipo_cambio": None,
        "lineas": (_linea("Alquiler & <semana>"),),
        "total": Decimal("1120.00"),
        "iva": Decimal("120.00"),
        **cambios,
    }  # fmt: skip
    return fel.DocumentoFEL(**datos)


def test_certifica_con_serie_numero_y_autorizacion_deterministas():
    simulado = fel.CertificadorSimulado()
    uno, otro = simulado.certificar(_documento()), simulado.certificar(_documento())

    assert (uno.serie, uno.numero, uno.autorizacion) == (otro.serie, otro.numero, otro.autorizacion)
    hexa = uno.autorizacion.replace("-", "")
    assert uno.serie == hexa[:8]
    assert uno.numero == str(int(hexa[8:16], 16))
    assert simulado.certificar(_documento(referencia="16")).autorizacion != uno.autorizacion


def test_el_xml_lleva_los_datos_del_documento():
    certificacion = fel.CertificadorSimulado().certificar(
        _documento(moneda="USD", tipo_cambio=Decimal("7.75000000"))
    )
    raiz = ET.fromstring(certificacion.xml)  # noqa: S314 (XML generado por el propio simulador)

    assert raiz.find("Certificacion").get("NumeroAutorizacion") == certificacion.autorizacion
    assert raiz.find("DatosGenerales").get("TipoCambio") == "7.75000000"
    assert raiz.find("Receptor").get("IDReceptor") == "12345679"
    assert raiz.find("Items/Item").get("Descripcion") == "Alquiler & <semana>"
    assert raiz.find("Totales").get("GranTotal") == "1120.00"


@pytest.mark.parametrize(
    ("cambios", "motivo"),
    [
        ({"receptor_id": "12345678"}, "El NIT del receptor 12345678 no es válido"),
        ({"lineas": ()}, "El documento no tiene líneas o su total no es mayor que cero"),
        (
            {"lineas": (_linea("RECHAZAR: receptor inactivo"),)},
            "receptor inactivo",
        ),
    ],
)  # fmt: skip
def test_rechaza_con_su_motivo(cambios, motivo):
    with pytest.raises(fel.RechazoFEL) as error:
        fel.CertificadorSimulado().certificar(_documento(**cambios))
    assert error.value.motivo == motivo


def test_consumidor_final_y_cui_no_se_validan_como_nit():
    simulado = fel.CertificadorSimulado()
    assert simulado.certificar(_documento(receptor_id="CF", receptor_tipo="cf")).serie
    assert simulado.certificar(_documento(receptor_id="2547123450101", receptor_tipo="cui")).serie


def test_el_certificador_se_elige_por_configuracion(monkeypatch):
    assert isinstance(fel.certificador(), fel.CertificadorSimulado)
    monkeypatch.setattr(config, "FEL_CERTIFICADOR", "otro")
    with pytest.raises(RuntimeError):
        fel.certificador()
