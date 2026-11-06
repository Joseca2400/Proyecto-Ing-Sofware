"""HU-4.09 (versión delgada): facturas de compras y gastos locales con su cuenta por pagar."""

from datetime import date, timedelta

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal

URL = "/api/v1/compras/facturas"
URL_PROVEEDORES = "/api/v1/compras/proveedores"
URL_UNIDADES = "/api/v1/unidades"
VIN = "1HGCM82633A004352"
UNIDAD = {
    "vin": VIN,
    "marca": "Honda",
    "linea": "Accord",
    "modelo": 2003,
    "color": "Gris",
    "tipo_vehiculo": "sedan",
}

GENERAL = {
    "tipo": "local",
    "nombre": "Repuestos El Volante, S.A.",
    "nit": "1234567-9",
    "regimen": "general",
    "rubro": "repuestos",
    "moneda_habitual": "GTQ",
    "dias_credito": 30,
}
PEQUENO = {
    **GENERAL,
    "nombre": "Taller Don Chepe",
    "nit": "576937-K",
    "regimen": "pequeno_contribuyente",
    "rubro": "servicios",
    "dias_credito": 0,
}
EXTERIOR = {
    "tipo": "exterior",
    "nombre": "Copart Inc.",
    "identificacion_fiscal": "94-2867490",
    "pais": "US",
    "rubro": "subasta",
    "moneda_habitual": "USD",
}

AUTORIZACION = "1A2B3C4D-1234-4ABC-9DEF-0123456789AB"


def _linea(**cambios) -> dict:
    return {
        "descripcion": "Juego de pastillas de freno",
        "cuenta": "5.1.02",
        "linea_negocio": "taller",
        "vin": None,
        "base": "1000.00",
        "iva": "120.00",
        **cambios,
    }


def _factura(proveedor_id: int, **cambios) -> dict:
    return {
        "proveedor_id": proveedor_id,
        "serie": "1A2B3C4D",
        "numero": "305419896",
        "autorizacion": AUTORIZACION,
        "fecha": "2026-10-15",
        "lineas": [_linea()],
        **cambios,
    }


@pytest.fixture(autouse=True)
def tablas_vacias(cliente):
    """Sin facturas ni unidades previas; solo existe la unidad con VIN que usan las líneas (HU-1.05)."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE proveedor, unidad RESTART IDENTITY CASCADE"))
        db.commit()
    assert cliente.post(URL_UNIDADES, json=UNIDAD).status_code == 201


@pytest.fixture
def general(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=GENERAL).json()["id"]


@pytest.fixture
def pequeno(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=PEQUENO).json()["id"]


def _cuantas_facturas() -> int:
    with SessionLocal() as db:
        return db.scalar(text("SELECT count(*) FROM factura_compra"))


def test_registra_factura_con_credito_fiscal_y_cuenta_por_pagar(cliente, general):
    lineas = [
        _linea(),
        _linea(
            descripcion="Pintura de puerta",
            cuenta="5.1.03",
            vin=" 1hgcm82633a004352 ",
            base="250.50",
            iva="30.06",
        ),
    ]
    respuesta = cliente.post(URL, json=_factura(general, lineas=lineas))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["proveedor"]["nombre"] == "Repuestos El Volante, S.A."
    assert cuerpo["proveedor"]["nit_formateado"] == "1234567-9"
    assert cuerpo["serie"] == "1A2B3C4D"
    assert cuerpo["numero"] == "305419896"
    assert cuerpo["autorizacion"] == AUTORIZACION
    assert cuerpo["regimen_proveedor"] == "general"
    assert cuerpo["genera_credito_fiscal"] is True
    assert cuerpo["total_base"] == "1250.500000"
    assert cuerpo["total_iva"] == "150.060000"
    assert cuerpo["credito_fiscal"] == "150.060000"
    assert cuerpo["total"] == "1400.560000"

    assert [linea["numero_linea"] for linea in cuerpo["lineas"]] == [1, 2]
    segunda = cuerpo["lineas"][1]
    assert segunda["vin"] == "1HGCM82633A004352"
    assert segunda["cuenta"] == "5.1.03"
    assert segunda["linea_negocio"] == "taller"
    assert segunda["base"] == "250.500000"
    assert segunda["iva"] == "30.060000"
    assert cuerpo["lineas"][0]["vin"] is None

    cxp = cuerpo["cuenta_por_pagar"]
    assert cxp["moneda"] == "GTQ"
    assert cxp["monto"] == "1400.560000"
    assert cxp["saldo"] == "1400.560000"
    assert cxp["fecha"] == "2026-10-15"
    assert cxp["fecha_vencimiento"] == "2026-11-14"  # 30 días de crédito


def test_pequeno_contribuyente_no_genera_credito_fiscal(cliente, pequeno):
    respuesta = cliente.post(URL, json=_factura(pequeno, lineas=[_linea(base="500.00", iva="25.00")]))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["regimen_proveedor"] == "pequeno_contribuyente"
    assert cuerpo["genera_credito_fiscal"] is False
    assert cuerpo["total_iva"] == "25.000000"
    assert cuerpo["credito_fiscal"] == "0.000000"
    # El IVA no recuperable sigue siendo parte de lo que se le debe al proveedor.
    assert cuerpo["total"] == "525.000000"
    assert cuerpo["cuenta_por_pagar"]["monto"] == "525.000000"
    assert cuerpo["cuenta_por_pagar"]["fecha_vencimiento"] == "2026-10-15"  # contado


def test_suma_los_montos_sin_punto_flotante(cliente, general):
    lineas = [_linea(base="0.10", iva="0"), _linea(base="0.20", iva="0.000001")]
    cuerpo = cliente.post(URL, json=_factura(general, lineas=lineas)).json()

    assert cuerpo["total_base"] == "0.300000"
    assert cuerpo["total"] == "0.300001"


@pytest.mark.parametrize(
    "repetido",
    [
        {},
        {"serie": "1a2b3c4d"},  # misma serie y número aunque se escriba en minúsculas
        {"serie": "FFFF0000", "numero": "1"},  # misma autorización
        {"autorizacion": "11111111-2222-4333-8444-555555555555"},  # misma serie y número
    ],
)
def test_no_registra_dos_veces_el_mismo_dte_del_mismo_proveedor(cliente, general, repetido):
    assert cliente.post(URL, json=_factura(general)).status_code == 201

    respuesta = cliente.post(URL, json=_factura(general, **repetido))

    assert respuesta.status_code == 409
    assert "ya está registrado" in respuesta.json()["detail"]
    assert _cuantas_facturas() == 1


def test_el_mismo_numero_de_otro_proveedor_si_se_registra(cliente, general, pequeno):
    assert cliente.post(URL, json=_factura(general)).status_code == 201
    assert cliente.post(URL, json=_factura(pequeno)).status_code == 201


def test_rechaza_proveedor_del_exterior(cliente):
    exterior = cliente.post(URL_PROVEEDORES, json=EXTERIOR).json()["id"]

    respuesta = cliente.post(URL, json=_factura(exterior))

    assert respuesta.status_code == 400
    assert "proveedores locales" in respuesta.json()["detail"]


def test_rechaza_proveedor_inexistente(cliente):
    assert cliente.post(URL, json=_factura(999)).status_code == 404


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"serie": "1A2B-3C4D"}, "serie"),
        ({"numero": "12A"}, "número"),
        ({"autorizacion": "no-es-un-uuid"}, "autorización"),
        ({"autorizacion": "1A2B3C4D12344ABC9DEF0123456789AB"}, "autorización"),
        ({"lineas": []}, "al menos una línea"),
        ({"fecha": (date.today() + timedelta(days=1)).isoformat()}, "futura"),
    ],
)
def test_valida_los_datos_del_dte(cliente, general, cambios, mensaje):
    respuesta = cliente.post(URL, json=_factura(general, **cambios))

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"descripcion": "   "}, "descripción"),
        ({"cuenta": "Gastos varios"}, "código del catálogo"),
        ({"cuenta": "5..1"}, "código del catálogo"),
        ({"vin": "1HGCM82633A00435"}, "VIN"),  # 16 caracteres
        ({"vin": "1HGCM82633A0O4352"}, "VIN"),  # lleva O
        ({"vin": "1HGCM82623A004352"}, "dígito verificador"),
        ({"vin": "1FTFW1ET9DFC10312"}, "no existe la unidad"),  # VIN válido sin registrar
        ({"linea_negocio": "sucursal"}, "línea de negocio desconocida"),
        ({"base": "0"}, "mayor que cero"),
        ({"base": "-10"}, "mayor que cero"),
        ({"iva": "-1"}, "negativo"),
        ({"base": "abc"}, "número válido"),
        ({"base": "NaN"}, "número válido"),
        ({"base": "1.0000001"}, "6 decimales"),
        ({"base": "1e15"}, "máximo"),
    ],
)
def test_valida_cada_linea(cliente, general, cambios, mensaje):
    respuesta = cliente.post(URL, json=_factura(general, lineas=[_linea(), _linea(**cambios)]))

    assert respuesta.status_code == 400
    detalle = respuesta.json()["detail"]
    assert detalle.startswith("Línea 2:")
    assert mensaje in detalle
    assert _cuantas_facturas() == 0


@pytest.mark.parametrize(
    "cambios",
    [{"base": 1000.0}, {"iva": 120}],
)
def test_rechaza_montos_numericos(cliente, general, cambios):
    respuesta = cliente.post(URL, json=_factura(general, lineas=[_linea(**cambios)]))

    assert respuesta.status_code == 422


def test_lista_y_consulta_facturas(cliente, general, pequeno):
    primera = cliente.post(URL, json=_factura(general, fecha="2026-10-01")).json()
    segunda = cliente.post(URL, json=_factura(general, numero="2", autorizacion=AUTORIZACION[:-1] + "C"))
    tercera = cliente.post(URL, json=_factura(pequeno, fecha="2026-10-20")).json()

    todas = cliente.get(URL).json()
    assert [f["id"] for f in todas] == [tercera["id"], segunda.json()["id"], primera["id"]]

    del_general = cliente.get(URL, params={"proveedor_id": general}).json()
    assert [f["id"] for f in del_general] == [segunda.json()["id"], primera["id"]]

    consulta = cliente.get(f"{URL}/{primera['id']}")
    assert consulta.status_code == 200
    assert consulta.json() == primera

    assert cliente.get(f"{URL}/999").status_code == 404


def test_la_base_impide_credito_fiscal_a_un_pequeno_contribuyente(cliente, pequeno):
    factura = cliente.post(URL, json=_factura(pequeno)).json()

    with SessionLocal() as db, pytest.raises(Exception, match="ck_factura_compra_credito_fiscal"):
        db.execute(
            text("UPDATE factura_compra SET credito_fiscal = total_iva WHERE id = :id"),
            {"id": factura["id"]},
        )


def test_la_base_liga_la_linea_a_una_unidad_existente(cliente, general):
    """HU-1.05: el VIN de la línea es llave foránea a la unidad."""
    factura = cliente.post(URL, json=_factura(general, lineas=[_linea(vin=VIN)])).json()

    with SessionLocal() as db, pytest.raises(Exception, match="fk_linea_factura_compra_vin_unidad"):
        db.execute(
            text("UPDATE linea_factura_compra SET vin = '1FTFW1ET9DFC10312' WHERE factura_id = :id"),
            {"id": factura["id"]},
        )
