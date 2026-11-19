"""HU-1.01: perfil fiscal de la empresa con vigencia por cambio y permisos."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion import service
from tests.conftest import CLAVE_PRUEBAS

URL = "/api/v1/configuracion/perfil-fiscal"
PERFIL = {
    "vigente_desde": "2026-01-01",
    "razon_social": "Kilómetro Cero, S. A.",
    "nombre_comercial": "Kilómetro Cero",
    "nit": "1234567-9",
    "direccion_fiscal": "Zona 10, Ciudad de Guatemala",
    "establecimiento": "1",
    "regimen_isr": "utilidades",
    "agente_retencion_iva": True,
    "agente_retencion_isr": False,
}


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("DELETE FROM perfil_fiscal"))
        db.commit()


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


def con_rol(correo: str) -> TestClient:
    cliente = TestClient(app)
    token = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}).json()[
        "token"
    ]
    cliente.headers["Authorization"] = f"Bearer {token}"
    return cliente


def test_guarda_el_perfil_con_nit_normalizado_y_lo_consulta(cliente):
    assert cliente.get(URL).status_code == 404
    respuesta = cliente.post(URL, json={**PERFIL, "nit": " 1234567-9 "})
    assert respuesta.status_code == 201
    assert respuesta.json()["nit"] == "1234567-9"
    assert cliente.get(URL).json()["razon_social"] == "Kilómetro Cero, S. A."


@pytest.mark.parametrize("nit", ["1234567-8", "abc", "1234567-K"])
def test_rechaza_nit_con_verificador_incorrecto(cliente, nit):
    assert cliente.post(URL, json={**PERFIL, "nit": nit}).status_code == 400
    assert cliente.get(f"{URL}/historial").json() == []


@pytest.mark.parametrize("campo", ["razon_social", "nombre_comercial", "direccion_fiscal", "establecimiento"])
def test_exige_los_datos_obligatorios(cliente, campo):
    assert cliente.post(URL, json={**PERFIL, campo: "   "}).status_code == 422


def test_rechaza_regimen_desconocido(cliente):
    assert cliente.post(URL, json={**PERFIL, "regimen_isr": "otro"}).status_code == 422


def test_un_cambio_agrega_version_y_conserva_la_anterior(cliente):
    cliente.post(URL, json=PERFIL)
    cambio = {
        **PERFIL,
        "vigente_desde": "2026-07-01",
        "razon_social": "KM Cero, S. A.",
        "regimen_isr": "simplificado",
    }
    assert cliente.post(URL, json=cambio).status_code == 201

    assert [p["vigente_desde"] for p in cliente.get(f"{URL}/historial").json()] == [
        "2026-07-01",
        "2026-01-01",
    ]
    assert cliente.get(URL, params={"fecha": "2026-03-15"}).json()["razon_social"] == "Kilómetro Cero, S. A."
    assert cliente.get(URL, params={"fecha": "2026-07-01"}).json()["regimen_isr"] == "simplificado"
    assert cliente.get(URL, params={"fecha": "2025-12-31"}).status_code == 404


def test_la_vigencia_debe_ser_posterior_a_la_ultima(cliente):
    cliente.post(URL, json=PERFIL)
    assert cliente.post(URL, json=PERFIL).status_code == 409
    assert cliente.post(URL, json={**PERFIL, "vigente_desde": "2025-06-01"}).status_code == 409


def test_el_service_devuelve_el_perfil_vigente_por_fecha(cliente):
    cliente.post(URL, json=PERFIL)
    cliente.post(URL, json={**PERFIL, "vigente_desde": "2026-07-01", "nombre_comercial": "KM"})
    with SessionLocal() as db:
        assert service.perfil_fiscal_vigente(db, date(2026, 2, 1)).nombre_comercial == "Kilómetro Cero"
        assert service.perfil_fiscal_vigente(db, date(2026, 8, 1)).nombre_comercial == "KM"
        assert service.perfil_fiscal_vigente(db, date(2025, 1, 1)) is None


def test_un_cambio_queda_en_la_bitacora(cliente):
    cliente.post(URL, json=PERFIL)
    with SessionLocal() as db:
        n = db.scalar(
            text("SELECT count(*) FROM bitacora WHERE entidad = 'perfil_fiscal' AND accion = 'crear'")
        )
    assert n >= 1


def test_sin_sesion_responde_401(cliente_contador):
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, json=PERFIL).status_code == 401


@pytest.mark.parametrize("correo", ["auxiliar@empresa.gt", "gerencia@empresa.gt"])
def test_otros_roles_leen_pero_no_modifican(cliente_contador, correo):
    otro = con_rol(correo)
    assert otro.post(URL, json=PERFIL).status_code == 403
    assert otro.get(URL).status_code == 404  # sin perfil aún, pero con permiso de lectura


def test_el_gerente_financiero_puede_modificar(cliente_contador):
    assert con_rol("gerente.financiero@empresa.gt").post(URL, json=PERFIL).status_code == 201
