"""HU-6.01: alta y consulta de clientes individuales o empresas, con NIT, CUI o pasaporte y país."""

import pytest
from sqlalchemy import func, select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal

URL = "/api/v1/facturacion/clientes"

INDIVIDUAL = {
    "tipo": "individual",
    "nombre": "María Fernanda López",
    "cui": "2584 12345 0101",
    "nit": "1234567-9",
    "direccion": "4a. avenida 10-20 zona 1, Guatemala",
    "telefono": "5555-1234",
    "correo": "Maria.Lopez@Correo.com",
}

EMPRESA = {
    "tipo": "empresa",
    "nombre": "Distribuidora La Ceiba, S.A.",
    "nit": "576937-k",
    "agente_retencion_iva": True,
}

EXTRANJERO = {
    "tipo": "individual",
    "nombre": "John Smith",
    "pasaporte": "x1234567",
    "pais": "us",
}


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE cliente RESTART IDENTITY CASCADE"))
        db.commit()


def test_registra_cliente_individual_normalizado(cliente):
    respuesta = cliente.post(URL, json=INDIVIDUAL)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo"] == "individual"
    assert cuerpo["cui"] == "2584123450101"
    assert cuerpo["nit"] == "12345679"
    assert cuerpo["nit_formateado"] == "1234567-9"
    assert cuerpo["correo"] == "maria.lopez@correo.com"
    assert cuerpo["agente_retencion_iva"] is False
    assert cuerpo["agente_retencion_isr"] is False


def test_registra_empresa_agente_de_retencion(cliente):
    respuesta = cliente.post(URL, json=EMPRESA)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nit"] == "576937K"
    assert cuerpo["agente_retencion_iva"] is True
    assert cuerpo["agente_retencion_isr"] is False


def test_registra_extranjero_con_pasaporte_y_pais(cliente):
    respuesta = cliente.post(URL, json=EXTRANJERO)

    assert respuesta.status_code == 201
    assert respuesta.json()["pasaporte"] == "X1234567"
    assert respuesta.json()["pais"] == "US"
    assert respuesta.json()["nit"] is None


def test_rechaza_nit_con_verificador_incorrecto(cliente):
    respuesta = cliente.post(URL, json={**EMPRESA, "nit": "1234567-8"})

    assert respuesta.status_code == 400
    assert "dígito verificador" in respuesta.json()["detail"]


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        ({"tipo": "individual", "nombre": "Sin identificación"}, "Indique el NIT o el CUI"),
        ({**EMPRESA, "nit": None}, "Una empresa se identifica con su NIT"),
        ({**EMPRESA, "cui": "2584123450101"}, "solo con su NIT"),
        ({**INDIVIDUAL, "cui": "12345"}, "13 dígitos"),
        ({**EXTRANJERO, "pais": None}, "pasaporte y país"),
        ({**EXTRANJERO, "pais": "GT"}, "guatemalteco"),
        ({**EXTRANJERO, "pais": "U1"}, "dos letras"),
        ({**INDIVIDUAL, "correo": "sin-arroba"}, "correo"),
        ({**EMPRESA, "nombre": "   "}, "nombre del cliente es obligatorio"),
    ],
)
def test_valida_la_identificacion_y_los_datos(cliente, datos, mensaje):
    respuesta = cliente.post(URL, json=datos)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


@pytest.mark.parametrize(
    ("primero", "repetido", "mensaje"),
    [
        (EMPRESA, {**INDIVIDUAL, "nit": "576937K", "cui": None}, "NIT 576937-K"),
        (INDIVIDUAL, {**INDIVIDUAL, "nit": None, "cui": "2584-12345-0101"}, "CUI 2584123450101"),
        (EXTRANJERO, {**EXTRANJERO, "nombre": "Otro", "pasaporte": "X1234567"}, "pasaporte X1234567"),
    ],
)
def test_evita_clientes_duplicados(cliente, primero, repetido, mensaje):
    assert cliente.post(URL, json=primero).status_code == 201

    respuesta = cliente.post(URL, json=repetido)

    assert respuesta.status_code == 409
    assert mensaje in respuesta.json()["detail"]


def test_registra_cliente_exento_de_iva_con_su_motivo(cliente):
    respuesta = cliente.post(URL, json={**EMPRESA, "exento_iva": True, "motivo_exencion": "diplomatico"})

    assert respuesta.status_code == 201
    assert respuesta.json()["exento_iva"] is True
    assert respuesta.json()["motivo_exencion"] == "diplomatico"


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        ({"exento_iva": True}, "motivo de la exención"),
        ({"exento_iva": False, "motivo_exencion": "ong"}, "solo aplica a un cliente exento"),
    ],
)
def test_la_exencion_lleva_motivo(cliente, datos, mensaje):
    respuesta = cliente.post(URL, json={**EMPRESA, **datos})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_el_mismo_pasaporte_de_otro_pais_no_es_duplicado(cliente):
    assert cliente.post(URL, json=EXTRANJERO).status_code == 201

    assert cliente.post(URL, json={**EXTRANJERO, "pais": "MX"}).status_code == 201


def test_lista_y_busca_clientes(cliente):
    for datos in (INDIVIDUAL, EMPRESA, EXTRANJERO):
        assert cliente.post(URL, json=datos).status_code == 201

    nombres = [c["nombre"] for c in cliente.get(URL).json()]
    assert nombres == ["Distribuidora La Ceiba, S.A.", "John Smith", "María Fernanda López"]

    assert [c["nombre"] for c in cliente.get(URL, params={"tipo": "empresa"}).json()] == [
        "Distribuidora La Ceiba, S.A."
    ]
    assert [c["nombre"] for c in cliente.get(URL, params={"buscar": "576937-k"}).json()] == [
        "Distribuidora La Ceiba, S.A."
    ]
    assert [c["nombre"] for c in cliente.get(URL, params={"buscar": "2584 1234"}).json()] == [
        "María Fernanda López"
    ]
    assert [c["nombre"] for c in cliente.get(URL, params={"buscar": "x123"}).json()] == ["John Smith"]


def test_consulta_un_cliente(cliente):
    creado = cliente.post(URL, json=EMPRESA).json()

    assert cliente.get(f"{URL}/{creado['id']}").json()["nombre"] == EMPRESA["nombre"]
    assert cliente.get(f"{URL}/999").status_code == 404


def test_el_alta_queda_en_la_bitacora(cliente):
    # La bitácora no se vacía entre pruebas: se cuentan solo los registros nuevos.
    with SessionLocal() as db:
        desde = db.scalar(select(func.coalesce(func.max(RegistroBitacora.id), 0)))
    creado = cliente.post(URL, json=INDIVIDUAL).json()

    with SessionLocal() as db:
        registro = db.scalars(
            select(RegistroBitacora).where(
                RegistroBitacora.id > desde,
                RegistroBitacora.entidad == "cliente",
                RegistroBitacora.registro_id == str(creado["id"]),
            )
        ).one()
    assert registro.accion == "crear"
    assert registro.nuevos["cui"] == "2584123450101"
