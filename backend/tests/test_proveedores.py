"""HU-4.01 (versión delgada): alta y consulta de proveedores locales o del exterior, con el
régimen de IVA del proveedor local que pide HU-4.09."""

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal

URL = "/api/v1/compras/proveedores"

LOCAL = {
    "tipo": "local",
    "nombre": "Repuestos El Volante, S.A.",
    "nit": "1234567-9",
    "regimen": "general",
    "rubro": "repuestos",
    "moneda_habitual": "GTQ",
    "dias_credito": 30,
    "banco": "Banco Industrial",
    "cuenta_bancaria": "000-123456-7",
}

EXTERIOR = {
    "tipo": "exterior",
    "nombre": "Copart Inc.",
    "identificacion_fiscal": "94-2867490",
    "pais": "us",
    "rubro": "subasta",
    "moneda_habitual": "USD",
}


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE proveedor RESTART IDENTITY CASCADE"))
        db.commit()


def test_registra_proveedor_local_con_nit_normalizado(cliente):
    respuesta = cliente.post(URL, json=LOCAL)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "local"
    assert cuerpo["nit"] == "12345679"
    assert cuerpo["nit_formateado"] == "1234567-9"
    assert cuerpo["identificacion_fiscal"] is None
    assert cuerpo["pais"] is None
    assert cuerpo["regimen"] == "general"
    assert cuerpo["rubro"] == "repuestos"
    assert cuerpo["moneda_habitual"] == "GTQ"
    assert cuerpo["dias_credito"] == 30
    assert cuerpo["banco"] == "Banco Industrial"
    assert cuerpo["cuenta_bancaria"] == "000-123456-7"


def test_registra_proveedor_del_exterior(cliente):
    respuesta = cliente.post(URL, json=EXTERIOR)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "exterior"
    assert cuerpo["nit"] is None
    assert cuerpo["nit_formateado"] is None
    assert cuerpo["identificacion_fiscal"] == "94-2867490"
    assert cuerpo["pais"] == "US"
    assert cuerpo["regimen"] is None
    assert cuerpo["dias_credito"] == 0  # contado por defecto


def test_registra_proveedor_local_pequeno_contribuyente(cliente):
    respuesta = cliente.post(URL, json={**LOCAL, "regimen": "pequeno_contribuyente"})

    assert respuesta.status_code == 201
    assert respuesta.json()["regimen"] == "pequeno_contribuyente"


def test_proveedor_local_exige_regimen(cliente):
    sin_regimen = {k: v for k, v in LOCAL.items() if k != "regimen"}
    respuesta = cliente.post(URL, json=sin_regimen)

    assert respuesta.status_code == 400
    assert "régimen" in respuesta.json()["detail"]


def test_proveedor_del_exterior_no_lleva_regimen(cliente):
    respuesta = cliente.post(URL, json={**EXTERIOR, "regimen": "general"})

    assert respuesta.status_code == 400
    assert "solo aplica a proveedores locales" in respuesta.json()["detail"]


def test_acepta_nit_con_k(cliente):
    respuesta = cliente.post(URL, json={**LOCAL, "nit": "576937-k"})

    assert respuesta.status_code == 201
    assert respuesta.json()["nit"] == "576937K"


def test_rechaza_nit_con_verificador_incorrecto(cliente):
    respuesta = cliente.post(URL, json={**LOCAL, "nit": "1234567-8"})

    assert respuesta.status_code == 400
    assert "dígito verificador" in respuesta.json()["detail"]


def test_rechaza_nit_repetido_aunque_se_escriba_distinto(cliente):
    assert cliente.post(URL, json=LOCAL).status_code == 201
    respuesta = cliente.post(URL, json={**LOCAL, "nombre": "Otro nombre", "nit": "0012345679"})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Ya existe un proveedor con el NIT 1234567-9"


def test_varios_proveedores_del_exterior_sin_nit(cliente):
    assert cliente.post(URL, json=EXTERIOR).status_code == 201
    otro = {**EXTERIOR, "nombre": "IAA Inc.", "identificacion_fiscal": "36-4003020"}
    assert cliente.post(URL, json=otro).status_code == 201


def test_proveedor_local_exige_nit(cliente):
    sin_nit = {k: v for k, v in LOCAL.items() if k != "nit"}
    respuesta = cliente.post(URL, json=sin_nit)

    assert respuesta.status_code == 400
    assert "NIT es obligatorio" in respuesta.json()["detail"]


def test_proveedor_local_no_lleva_datos_del_exterior(cliente):
    respuesta = cliente.post(URL, json={**LOCAL, "pais": "US"})

    assert respuesta.status_code == 400


@pytest.mark.parametrize("faltante", ["identificacion_fiscal", "pais"])
def test_proveedor_del_exterior_exige_identificacion_y_pais(cliente, faltante):
    respuesta = cliente.post(URL, json={**EXTERIOR, faltante: "  "})

    assert respuesta.status_code == 400
    assert "identificación fiscal y país" in respuesta.json()["detail"]


def test_proveedor_del_exterior_no_lleva_nit(cliente):
    respuesta = cliente.post(URL, json={**EXTERIOR, "nit": "1234567-9"})

    assert respuesta.status_code == 400


@pytest.mark.parametrize("pais", ["USA", "U1", "ÑA"])
def test_rechaza_pais_que_no_es_codigo_de_dos_letras(cliente, pais):
    respuesta = cliente.post(URL, json={**EXTERIOR, "pais": pais})

    assert respuesta.status_code in (400, 422)


def test_proveedor_guatemalteco_no_es_del_exterior(cliente):
    respuesta = cliente.post(URL, json={**EXTERIOR, "pais": "GT"})

    assert respuesta.status_code == 400
    assert "local" in respuesta.json()["detail"]


def test_rechaza_nombre_vacio(cliente):
    respuesta = cliente.post(URL, json={**LOCAL, "nombre": "   "})

    assert respuesta.status_code == 400
    assert "nombre" in respuesta.json()["detail"]


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("rubro", "transporte"),
        ("moneda_habitual", "EUR"),
        ("tipo", "otro"),
        ("dias_credito", -1),
        ("regimen", "especial"),
    ],
)
def test_rechaza_valores_fuera_del_catalogo(cliente, campo, valor):
    respuesta = cliente.post(URL, json={**LOCAL, campo: valor})

    assert respuesta.status_code == 422


def test_lista_en_orden_alfabetico_y_filtra(cliente):
    cliente.post(URL, json=LOCAL)
    cliente.post(URL, json=EXTERIOR)
    cliente.post(URL, json={**EXTERIOR, "nombre": "Naviera Atlántico", "rubro": "naviera"})

    todos = cliente.get(URL).json()
    assert [p["nombre"] for p in todos] == [
        "Copart Inc.",
        "Naviera Atlántico",
        "Repuestos El Volante, S.A.",
    ]
    assert [p["nombre"] for p in cliente.get(URL, params={"tipo": "local"}).json()] == [
        "Repuestos El Volante, S.A."
    ]
    assert [p["nombre"] for p in cliente.get(URL, params={"rubro": "naviera"}).json()] == [
        "Naviera Atlántico"
    ]


@pytest.mark.parametrize(
    ("buscar", "esperado"),
    [
        ("volante", "Repuestos El Volante, S.A."),
        ("1234567-9", "Repuestos El Volante, S.A."),
        ("94-28", "Copart Inc."),
    ],
)
def test_busca_por_nombre_nit_o_identificacion(cliente, buscar, esperado):
    cliente.post(URL, json=LOCAL)
    cliente.post(URL, json=EXTERIOR)

    encontrados = cliente.get(URL, params={"buscar": buscar}).json()
    assert [p["nombre"] for p in encontrados] == [esperado]


@pytest.mark.parametrize(
    ("buscar", "esperado"),
    [
        ("1669394", ["Agencia Norte"]),  # NIT parcial, sin el verificador
        ("669394", ["Agencia Norte"]),  # parte central del NIT
        ("576937k", ["Taller Sur"]),  # verificador K escrito en minúscula
        ("576937-k", ["Taller Sur"]),  # con guion y K minúscula
        ("0016693949", ["Agencia Norte"]),  # NIT completo con ceros a la izquierda
        ("8", []),
    ],
)
def test_busca_por_nit_parcial_o_con_k_minuscula(cliente, buscar, esperado):
    cliente.post(URL, json={**LOCAL, "nombre": "Agencia Norte", "nit": "16693949"})
    cliente.post(URL, json={**LOCAL, "nombre": "Taller Sur", "nit": "576937K"})

    encontrados = cliente.get(URL, params={"buscar": buscar}).json()
    assert [p["nombre"] for p in encontrados] == esperado


@pytest.mark.parametrize("comodin", ["%", "_"])
def test_la_busqueda_trata_los_comodines_como_texto(cliente, comodin):
    cliente.post(URL, json=LOCAL)

    assert cliente.get(URL, params={"buscar": comodin}).json() == []


def test_consulta_un_proveedor_por_id(cliente):
    creado = cliente.post(URL, json=LOCAL).json()

    respuesta = cliente.get(f"{URL}/{creado['id']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == LOCAL["nombre"]

    faltante = cliente.get(f"{URL}/999999")
    assert faltante.status_code == 404
    assert "No existe el proveedor" in faltante.json()["detail"]


def test_la_base_exige_nit_a_un_proveedor_local_aunque_se_salte_el_servicio():
    with SessionLocal() as db, pytest.raises(Exception, match="ck_proveedor_identificacion"):
        db.execute(
            text(
                "INSERT INTO proveedor (tipo, nombre, rubro, moneda_habitual, dias_credito) "
                "VALUES ('local', 'Sin NIT', 'otros', 'GTQ', 0)"
            )
        )
        db.commit()
