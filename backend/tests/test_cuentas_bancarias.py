"""HU-1.08: cuentas bancarias en quetzales y dólares ligadas al catálogo."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion import service
from app.modulos.configuracion.models import Cuenta
from tests.conftest import CLAVE_PRUEBAS

URL = "/api/v1/configuracion/cuentas-bancarias"


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("DELETE FROM cuenta_bancaria"))
        db.commit()


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


@pytest.fixture
def ids():
    """Ids de cuentas de la semilla: bancos GTQ, bancos USD, caja general y la agrupación de caja y bancos."""
    with SessionLocal() as db:
        por_codigo = {c.codigo: c.id for c in db.scalars(select(Cuenta))}
    return {
        "gtq": por_codigo["1.1.01.02"],
        "usd": por_codigo["1.1.01.03"],
        "caja": por_codigo["1.1.01.01"],
        "grupo": por_codigo["1.1.01"],
    }


def datos(cuenta_id, **cambios):
    return {
        "banco": "Banco Industrial",
        "numero": "123-456-7",
        "tipo": "monetaria",
        "moneda": "GTQ",
        "cuenta_id": cuenta_id,
        **cambios,
    }


def con_rol(correo: str) -> TestClient:
    cliente = TestClient(app)
    token = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}).json()[
        "token"
    ]
    cliente.headers["Authorization"] = f"Bearer {token}"
    return cliente


def test_crea_cuentas_en_quetzales_y_dolares_y_las_filtra_por_moneda(cliente, ids):
    assert cliente.post(URL, json=datos(ids["gtq"], siguiente_cheque=100)).status_code == 201
    usd = cliente.post(URL, json=datos(ids["usd"], numero="987", moneda="USD", tipo="ahorro"))
    assert usd.status_code == 201
    assert usd.json()["moneda"] == "USD"

    assert len(cliente.get(URL).json()) == 2
    assert [c["moneda"] for c in cliente.get(URL, params={"moneda": "USD"}).json()] == ["USD"]


def test_una_cuenta_en_usd_exige_cuenta_contable_monetaria_usd(cliente, ids):
    respuesta = cliente.post(URL, json=datos(ids["gtq"], moneda="USD"))
    assert respuesta.status_code == 400
    assert "monetaria en USD" in respuesta.json()["detail"]


def test_la_cuenta_contable_debe_ser_de_detalle_y_existir(cliente, ids):
    assert cliente.post(URL, json=datos(ids["grupo"])).status_code == 400
    assert cliente.post(URL, json=datos(999999)).status_code == 404


def test_rechaza_datos_invalidos(cliente, ids):
    assert cliente.post(URL, json=datos(ids["gtq"], moneda="EUR")).status_code == 422
    assert cliente.post(URL, json=datos(ids["gtq"], tipo="otro")).status_code == 422
    assert cliente.post(URL, json=datos(ids["gtq"], banco="  ")).status_code == 422
    assert cliente.post(URL, json=datos(ids["gtq"], siguiente_cheque=0)).status_code == 400


def test_no_repite_numero_de_banco_ni_cuenta_contable(cliente, ids):
    assert cliente.post(URL, json=datos(ids["gtq"])).status_code == 201
    assert cliente.post(URL, json=datos(ids["caja"])).status_code == 409  # mismo banco y número
    assert (
        cliente.post(URL, json=datos(ids["gtq"], numero="otra")).status_code == 409
    )  # misma cuenta contable


def test_configura_la_numeracion_de_cheques(cliente, ids):
    creada = cliente.post(URL, json=datos(ids["gtq"])).json()
    assert creada["siguiente_cheque"] is None
    ruta = f"{URL}/{creada['id']}/cheques"
    assert cliente.put(ruta, json={"siguiente_cheque": 501}).json()["siguiente_cheque"] == 501
    assert cliente.put(ruta, json={"siguiente_cheque": 0}).status_code == 400
    assert cliente.put(f"{URL}/9999/cheques", json={"siguiente_cheque": 1}).status_code == 404


def test_solo_se_inactiva_no_se_elimina(cliente, ids):
    creada = cliente.post(URL, json=datos(ids["gtq"])).json()
    assert cliente.delete(f"{URL}/{creada['id']}").status_code in (404, 405)  # no hay ruta para borrar

    assert cliente.post(f"{URL}/{creada['id']}/inactivar").json()["activa"] is False
    assert cliente.get(URL, params={"solo_activas": True}).json() == []
    assert len(cliente.get(URL).json()) == 1
    assert cliente.post(f"{URL}/{creada['id']}/activar").json()["activa"] is True


def test_el_service_lista_y_obtiene_para_otros_modulos(cliente, ids):
    gtq = cliente.post(URL, json=datos(ids["gtq"])).json()
    usd = cliente.post(URL, json=datos(ids["usd"], numero="987", moneda="USD")).json()
    cliente.post(f"{URL}/{usd['id']}/inactivar")
    with SessionLocal() as db:
        assert [c.id for c in service.listar_cuentas_bancarias(db)] == [gtq["id"]]
        assert [c.id for c in service.listar_cuentas_bancarias(db, solo_activas=False)] == [
            gtq["id"],
            usd["id"],
        ]
        assert service.listar_cuentas_bancarias(db, moneda="USD") == []
        assert service.obtener_cuenta_bancaria(db, usd["id"]).moneda == "USD"


def test_un_cambio_queda_en_la_bitacora(cliente, ids):
    cliente.post(URL, json=datos(ids["gtq"]))
    with SessionLocal() as db:
        n = db.scalar(text("SELECT count(*) FROM bitacora WHERE entidad = 'cuenta_bancaria'"))
    assert n >= 1


def test_sin_sesion_responde_401(cliente_contador, ids):
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, json=datos(ids["gtq"])).status_code == 401


@pytest.mark.parametrize("correo", ["auxiliar@empresa.gt", "gerencia@empresa.gt"])
def test_otros_roles_leen_pero_no_modifican(cliente, ids, correo):
    creada = cliente.post(URL, json=datos(ids["gtq"])).json()
    otro = con_rol(correo)
    assert otro.get(URL).status_code == 200
    assert otro.post(URL, json=datos(ids["usd"], moneda="USD", numero="1")).status_code == 403
    assert otro.put(f"{URL}/{creada['id']}/cheques", json={"siguiente_cheque": 5}).status_code == 403
    assert otro.post(f"{URL}/{creada['id']}/inactivar").status_code == 403


def test_el_gerente_financiero_puede_modificar(cliente_contador, ids):
    gerente = con_rol("gerente.financiero@empresa.gt")
    assert gerente.post(URL, json=datos(ids["gtq"])).status_code == 201
