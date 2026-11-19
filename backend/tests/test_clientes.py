"""HU-6.01: clientes individuales o empresas, con NIT, CUI o pasaporte, sin duplicados."""

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.facturacion import service
from app.modulos.facturacion.schemas import ClienteEntrada
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/facturacion/clientes"

EMPRESA = {
    "tipo": "empresa",
    "nombre": "Transportes del Norte, S.A.",
    "tipo_identificacion": "nit",
    "identificacion": "1234567-9",
    "direccion": "5a avenida 10-20, zona 1",
    "telefono": "2222-3333",
    "correo": "compras@transportes.gt",
    "agente_retencion_iva": True,
}
INDIVIDUAL = {
    "tipo": "individual",
    "nombre": "María López",
    "tipo_identificacion": "cui",
    "identificacion": "2547 12345 0101",
}
EXTRANJERO = {
    "tipo": "individual",
    "nombre": "John Smith",
    "tipo_identificacion": "pasaporte",
    "identificacion": "x1234567",
    "pais": "us",
}


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE cliente RESTART IDENTITY CASCADE"))
        db.commit()


def test_registra_empresa_con_nit_normalizado(cliente_contador):
    respuesta = cliente_contador.post(URL, json=EMPRESA)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["identificacion"] == "12345679"
    assert cuerpo["identificacion_formateada"] == "1234567-9"
    assert cuerpo["agente_retencion_iva"] is True
    assert cuerpo["agente_retencion_isr"] is False
    assert cliente_contador.get(f"{URL}/{cuerpo['id']}").json()["nombre"] == EMPRESA["nombre"]


def test_registra_individual_con_cui_y_extranjero_con_pasaporte(cliente_contador):
    cui = cliente_contador.post(URL, json=INDIVIDUAL).json()
    pasaporte = cliente_contador.post(URL, json=EXTRANJERO).json()

    assert cui["identificacion"] == "2547123450101"
    assert pasaporte["identificacion"] == "X1234567"
    assert pasaporte["pais"] == "US"


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"identificacion": "1234567-8"}, "verificador"),
        ({"nombre": "  "}, "nombre"),
        ({"correo": "no-es-correo"}, "correo"),
        ({"tipo_identificacion": "cui", "identificacion": "123"}, "Una empresa"),
        ({"pais": "US"}, "pasaporte"),
    ],
)
def test_rechaza_datos_invalidos(cliente_contador, cambio, mensaje):
    respuesta = cliente_contador.post(URL, json={**EMPRESA, **cambio})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_rechaza_cui_corto_y_pasaporte_sin_pais(cliente_contador):
    cui = cliente_contador.post(URL, json={**INDIVIDUAL, "identificacion": "123"})
    sin_pais = cliente_contador.post(URL, json={**EXTRANJERO, "pais": None})

    assert cui.status_code == 400 and "13 dígitos" in cui.json()["detail"]
    assert sin_pais.status_code == 400 and "país" in sin_pais.json()["detail"]


@pytest.mark.parametrize("cliente_repetido", [EMPRESA, INDIVIDUAL, EXTRANJERO])
def test_no_duplica_por_identificacion(cliente_contador, cliente_repetido):
    assert cliente_contador.post(URL, json=cliente_repetido).status_code == 201

    otra_vez = cliente_contador.post(URL, json={**cliente_repetido, "nombre": "Otro nombre"})

    assert otra_vez.status_code == 409
    assert "Ya existe un cliente" in otra_vez.json()["detail"]


def test_la_restriccion_unica_decide_en_altas_simultaneas(cliente_contador, monkeypatch):
    cliente_contador.post(URL, json=EMPRESA)
    with SessionLocal() as db:
        # Simula la carrera: la revisión previa no ve al cliente que otra transacción ya confirmó.
        monkeypatch.setattr(db, "scalar", lambda *args, **kwargs: None)
        with pytest.raises(ErrorNegocio) as error:
            service.registrar_cliente(db, ClienteEntrada(**EMPRESA))
    assert error.value.status == 409


def test_lista_y_busca_por_nombre_o_identificacion(cliente_contador):
    for datos in (EMPRESA, INDIVIDUAL, EXTRANJERO):
        cliente_contador.post(URL, json=datos)

    todos = [c["nombre"] for c in cliente_contador.get(URL).json()]
    por_nombre = cliente_contador.get(URL, params={"buscar": "transportes"}).json()
    por_nit = cliente_contador.get(URL, params={"buscar": "1234567-9"}).json()
    por_pasaporte = cliente_contador.get(URL, params={"buscar": "x1234"}).json()

    assert todos == ["John Smith", "María López", "Transportes del Norte, S.A."]
    assert [c["nombre"] for c in por_nombre] == [EMPRESA["nombre"]]
    assert [c["nombre"] for c in por_nit] == [EMPRESA["nombre"]]
    assert [c["nombre"] for c in por_pasaporte] == ["John Smith"]


def test_cliente_inexistente_es_404(cliente_contador):
    assert cliente_contador.get(f"{URL}/999").status_code == 404


def test_sin_sesion_responde_401(cliente):
    assert cliente.get(URL).status_code == 401
    assert cliente.post(URL, json=EMPRESA).status_code == 401


def _con_rol(cliente, sesion_contador, correo) -> dict[str, str]:
    # `sesion_contador` garantiza que las cuentas iniciales existen.
    token = cliente.post(f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}).json()[
        "token"
    ]
    return {"Authorization": f"Bearer {token}"}


def test_auxiliar_registra_y_gerencia_solo_consulta(cliente, sesion_contador):
    auxiliar = _con_rol(cliente, sesion_contador, "auxiliar@empresa.gt")
    gerencia = _con_rol(cliente, sesion_contador, "gerencia@empresa.gt")

    assert cliente.post(URL, json=EMPRESA, headers=auxiliar).status_code == 201
    assert cliente.post(URL, json=INDIVIDUAL, headers=gerencia).status_code == 403
    assert cliente.get(URL, headers=gerencia).status_code == 200
