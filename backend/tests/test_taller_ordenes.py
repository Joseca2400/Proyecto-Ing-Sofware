"""HU-5.01 (versión delgada): orden de reacondicionamiento ligada a un VIN."""

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.unidades import service as unidades
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/taller/ordenes"
VIN = "1HGCM82633A004352"
OTRO_VIN = "JHMCM56557C404453"


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


def unidad(vin: str = VIN, estado: str = "en_aduana", **cambios) -> dict:
    return {
        "vin": vin,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "linea_negocio": "alquiler",
        "estado": estado,
        **cambios,
    }


def orden(vin: str = VIN, **cambios) -> dict:
    return {
        "vin": vin,
        "tipo": "reacondicionamiento",
        "fecha_apertura": "2026-11-10",
        "kilometraje": 84500,
        "descripcion": "Pintura, frenos y llantas",
        "responsable": "Taller central",
        **cambios,
    }


@pytest.fixture(autouse=True)
def base_limpia(cliente):
    """Sin órdenes, unidades ni partidas; el catálogo cargado y la unidad VIN en aduana."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("TRUNCATE tarifa_mano_obra, unidad, partida RESTART IDENTITY CASCADE"))
        db.commit()
    assert cliente.post(f"{API}/unidades", json=unidad()).status_code == 201


def estado_unidad(cliente, vin: str = VIN) -> str:
    return cliente.get(f"{API}/unidades/{vin}").json()["estado"]


def test_abrir_orden_pasa_la_unidad_a_en_taller_con_su_historial(cliente):
    respuesta = cliente.post(URL, json=orden())
    assert respuesta.status_code == 201, respuesta.text
    creada = respuesta.json()
    assert creada["numero"] == "OT-00001"
    assert creada["estado"] == "abierta"
    assert creada["vin"] == VIN
    assert creada["costo_acumulado"] == "0.000000"
    assert estado_unidad(cliente) == "en_taller"
    ultimo = cliente.get(f"{API}/unidades/{VIN}/historial").json()[-1]
    assert (ultimo["estado_anterior"], ultimo["estado_nuevo"]) == ("en_aduana", "en_taller")
    assert ultimo["documento"] == "Orden de trabajo OT-00001"


def test_los_numeros_son_correlativos_y_se_consultan(cliente):
    assert cliente.post(f"{API}/unidades", json=unidad(OTRO_VIN)).status_code == 201
    primera = cliente.post(URL, json=orden()).json()
    segunda = cliente.post(URL, json=orden(OTRO_VIN)).json()
    assert (primera["numero"], segunda["numero"]) == ("OT-00001", "OT-00002")
    assert cliente.get(f"{URL}/{segunda['id']}").json()["vin"] == OTRO_VIN
    assert [o["numero"] for o in cliente.get(URL).json()] == ["OT-00002", "OT-00001"]
    assert [o["vin"] for o in cliente.get(URL, params={"vin": VIN}).json()] == [VIN]
    assert cliente.get(URL, params={"estado": "cerrada"}).json() == []
    assert cliente.get(f"{URL}/999").status_code == 404


def test_una_unidad_ya_en_taller_de_la_importacion_no_cambia_de_estado(cliente):
    assert cliente.post(f"{API}/unidades", json=unidad(OTRO_VIN, estado="en_taller")).status_code == 201
    assert cliente.post(URL, json=orden(OTRO_VIN)).status_code == 201
    assert len(cliente.get(f"{API}/unidades/{OTRO_VIN}/historial").json()) == 1


@pytest.mark.parametrize("estado", ["en_transito", "lista", "en_flota", "en_venta"])
def test_rechaza_una_unidad_en_otro_estado(cliente, estado):
    assert cliente.post(f"{API}/unidades", json=unidad(OTRO_VIN, estado=estado)).status_code == 201
    respuesta = cliente.post(URL, json=orden(OTRO_VIN))
    assert respuesta.status_code == 400
    assert "aduana o en taller" in respuesta.json()["detail"]
    assert estado_unidad(cliente, OTRO_VIN) == estado


def test_rechaza_el_taller_de_una_unidad_de_flota(cliente):
    """En taller por mantenimiento (ya salió de la importación) no admite reacondicionamiento."""
    assert cliente.post(f"{API}/unidades", json=unidad(OTRO_VIN, estado="en_flota")).status_code == 201
    cambio = {"estado": "en_taller", "documento": "Mantenimiento"}
    assert cliente.post(f"{API}/unidades/{OTRO_VIN}/estado", json=cambio).status_code == 200
    assert cliente.post(URL, json=orden(OTRO_VIN)).status_code == 400


def test_una_sola_orden_abierta_por_unidad(cliente):
    assert cliente.post(URL, json=orden()).status_code == 201
    repetida = cliente.post(URL, json=orden())
    assert repetida.status_code == 409
    assert "ya tiene una orden" in repetida.json()["detail"]


def test_rechaza_datos_invalidos(cliente):
    assert cliente.post(URL, json=orden("1HGCM82633A004353")).status_code in (400, 404)  # VIN sin unidad
    assert cliente.post(URL, json=orden(OTRO_VIN)).status_code == 404
    assert cliente.post(URL, json=orden(tipo="mantenimiento")).status_code == 422
    assert cliente.post(URL, json=orden(kilometraje=-1)).status_code == 422
    assert cliente.post(URL, json=orden(descripcion="  ")).status_code == 422
    assert cliente.post(URL, json=orden(responsable="")).status_code == 422
    assert cliente.post(URL, json=orden(fecha_apertura="2999-01-01")).status_code == 400
    assert estado_unidad(cliente) == "en_aduana"  # nada de lo rechazado movió la unidad


def test_cambiar_estado_sin_confirmar_deja_la_decision_al_llamador():
    """`confirmar=False` solo escribe: al revertir, la unidad y su historial quedan como estaban."""
    with SessionLocal() as db:
        unidades.cambiar_estado(db, VIN, "en_taller", "Prueba", confirmar=False)
        assert unidades.obtener_por_vin(db, VIN).estado == "en_taller"
        db.rollback()
    with SessionLocal() as db:
        assert unidades.obtener_por_vin(db, VIN).estado == "en_aduana"
        assert len(unidades.historial(db, VIN)) == 1


def _token(cliente, correo):
    r = cliente.post(f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_permisos(cliente, sesion_contador):
    from fastapi.testclient import TestClient

    from app.main import app

    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, json=orden()).status_code == 401
    gerencia = _token(anonimo, "gerencia@empresa.gt")
    assert anonimo.get(URL, headers=gerencia).status_code == 200  # cualquier usuario con sesión lee
    assert anonimo.post(URL, json=orden(), headers=gerencia).status_code == 403
    auxiliar = _token(anonimo, "auxiliar@empresa.gt")
    assert anonimo.post(URL, json=orden(), headers=auxiliar).status_code == 201
