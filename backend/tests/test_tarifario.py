"""HU-3.05: tarifario de alquiler por tipo de vehículo o por unidad, con vigencias sin traslape."""

from datetime import date

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.alquileres import service
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/alquileres/tarifas"
VIN = "1HGCM82633A004352"

SEDAN = {
    "tipo_vehiculo": "sedan",
    "modalidad": "diaria",
    "moneda": "GTQ",
    "monto": "350.00",
    "km_incluido": 150,
    "precio_km_adicional": "2.50",
    "vigente_desde": "2026-01-01",
}


@pytest.fixture(autouse=True)
def tablas_vacias():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE unidad, tarifa RESTART IDENTITY CASCADE"))
        db.commit()


@pytest.fixture
def unidad(cliente_contador):
    cuerpo = {
        "vin": VIN,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2003,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "linea_negocio": "alquiler",
    }
    assert cliente_contador.post(f"{API}/unidades", json=cuerpo).status_code == 201


def vigente(db, fecha, **cambios):
    datos = {"modalidad": "diaria", "moneda": "GTQ", "tipo_vehiculo": "sedan", **cambios}
    return service.tarifa_vigente(db, date.fromisoformat(fecha), **datos)


def test_registra_tarifa_por_tipo_de_vehiculo(cliente_contador):
    respuesta = cliente_contador.post(URL, json=SEDAN)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["monto"] == "350.000000"
    assert cuerpo["precio_km_adicional"] == "2.500000"
    assert cuerpo["km_incluido"] == 150
    assert cuerpo["vin"] is None
    assert cuerpo["vigente_hasta"] is None


def test_registra_tarifa_de_excepcion_por_vin(cliente_contador, unidad):
    datos = {**SEDAN, "tipo_vehiculo": None, "vin": VIN.lower(), "monto": "500"}

    respuesta = cliente_contador.post(URL, json=datos)

    assert respuesta.status_code == 201
    assert respuesta.json()["vin"] == VIN
    assert respuesta.json()["tipo_vehiculo"] is None


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"tipo_vehiculo": None}, "tipo de vehículo o"),
        ({"vin": VIN}, "solo uno"),
        ({"tipo_vehiculo": "tractor"}, "Tipo de vehículo desconocido"),
        ({"tipo_vehiculo": None, "vin": VIN}, "No existe una unidad"),
        ({"monto": "0"}, "mayor que cero"),
        ({"monto": "abc"}, "no es un número válido"),
        ({"precio_km_adicional": "-1"}, "no puede ser negativo"),
        ({"vigente_hasta": "2025-12-31"}, "termina antes de empezar"),
    ],
)
def test_rechaza_tarifas_invalidas(cliente_contador, cambio, mensaje):
    respuesta = cliente_contador.post(URL, json={**SEDAN, **cambio})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_los_montos_deben_ser_texto(cliente_contador):
    assert cliente_contador.post(URL, json={**SEDAN, "monto": 350.5}).status_code == 422


def test_una_tarifa_nueva_cierra_la_abierta_y_no_toca_sus_valores(cliente_contador):
    vieja = cliente_contador.post(URL, json=SEDAN).json()

    nueva = cliente_contador.post(URL, json={**SEDAN, "monto": "400", "vigente_desde": "2026-07-01"})
    tarifas = {t["id"]: t for t in cliente_contador.get(URL).json()}

    assert nueva.status_code == 201
    assert tarifas[vieja["id"]]["vigente_hasta"] == "2026-06-30"
    assert tarifas[vieja["id"]]["monto"] == "350.000000"
    with SessionLocal() as db:
        assert vigente(db, "2026-06-30").monto == 350
        assert vigente(db, "2026-07-01").monto == 400


def test_rechaza_vigencias_traslapadas(cliente_contador):
    cliente_contador.post(URL, json={**SEDAN, "vigente_hasta": "2026-06-30"})

    dentro = cliente_contador.post(URL, json={**SEDAN, "vigente_desde": "2026-06-01"})
    antes = cliente_contador.post(
        URL, json={**SEDAN, "vigente_desde": "2025-01-01", "vigente_hasta": "2026-01-01"}
    )

    assert dentro.status_code == 409 and "se traslapa" in dentro.json()["detail"]
    assert antes.status_code == 409


def test_misma_vigencia_en_otra_modalidad_moneda_o_tipo_no_choca(cliente_contador):
    cliente_contador.post(URL, json=SEDAN)

    for cambio in ({"modalidad": "semanal"}, {"moneda": "USD"}, {"tipo_vehiculo": "suv"}):
        assert cliente_contador.post(URL, json={**SEDAN, **cambio}).status_code == 201


def test_tarifa_vigente_prefiere_la_de_la_unidad(cliente_contador, unidad):
    cliente_contador.post(URL, json=SEDAN)
    cliente_contador.post(URL, json={**SEDAN, "tipo_vehiculo": None, "vin": VIN, "monto": "500"})

    with SessionLocal() as db:
        assert vigente(db, "2026-03-01", vin=VIN).monto == 500
        assert vigente(db, "2026-03-01").monto == 350


def test_tarifa_vigente_sin_tarifa_falla(cliente_contador):
    cliente_contador.post(URL, json={**SEDAN, "vigente_desde": "2026-06-01"})

    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="No hay tarifa"):
        vigente(db, "2026-05-31")


def test_consulta_de_tarifa_vigente_y_filtros(cliente_contador):
    cliente_contador.post(URL, json=SEDAN)
    cliente_contador.post(URL, json={**SEDAN, "modalidad": "semanal", "monto": "2000"})

    ruta = f"{URL}/vigente"
    parametros = {"modalidad": "diaria", "moneda": "GTQ", "tipo_vehiculo": "sedan", "fecha": "2026-02-01"}
    assert cliente_contador.get(ruta, params=parametros).json()["monto"] == "350.000000"
    assert cliente_contador.get(ruta, params={**parametros, "tipo_vehiculo": "suv"}).status_code == 404
    assert len(cliente_contador.get(URL, params={"modalidad": "semanal"}).json()) == 1
    assert "sedan" in cliente_contador.get(f"{URL}/catalogos").json()["tipos_vehiculo"]


def test_sin_sesion_responde_401(cliente):
    assert cliente.get(URL).status_code == 401
    assert cliente.post(URL, json=SEDAN).status_code == 401


def test_auxiliar_registra_y_gerencia_solo_consulta(cliente, sesion_contador):
    def sesion(correo):
        token = cliente.post(
            f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}
        ).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    assert cliente.post(URL, json=SEDAN, headers=sesion("auxiliar@empresa.gt")).status_code == 201
    assert cliente.post(URL, json=SEDAN, headers=sesion("gerencia@empresa.gt")).status_code == 403
    assert cliente.get(URL, headers=sesion("gerencia@empresa.gt")).status_code == 200
