"""HU-5.03 (versión delgada): mano de obra en la orden, costeada con la tarifa vigente."""

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from tests.test_taller_ordenes import API, OTRO_VIN, URL, VIN, _token, base_limpia, orden, unidad  # noqa: F401
from tests.test_taller_ordenes import cliente as cliente  # noqa: F401


def tarifa(valor: str, desde: str):
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO tarifa_mano_obra (tarifa_hora, vigente_desde) VALUES (:v, :d)"),
            {"v": valor, "d": desde},
        )
        db.commit()


def horas(**cambios) -> dict:
    return {
        "mecanico": "Luis Pérez",
        "fecha": "2026-11-12",
        "horas": "2.5",
        "tarea": "Cambio de frenos",
        **cambios,
    }


@pytest.fixture
def orden_id(cliente) -> int:
    tarifa("45", "2026-11-01")
    return cliente.post(URL, json=orden()).json()["id"]


def test_costea_con_la_tarifa_vigente_y_la_guarda(cliente, orden_id):
    respuesta = cliente.post(f"{URL}/{orden_id}/horas", json=horas())
    assert respuesta.status_code == 201, respuesta.text
    hora = respuesta.json()
    assert (hora["horas"], hora["tarifa_hora"], hora["costo"]) == ("2.50", "45.000000", "112.500000")
    # La orden acumula el costo de sus horas.
    assert cliente.get(f"{URL}/{orden_id}").json()["costo_acumulado"] == "112.500000"
    assert len(cliente.get(f"{URL}/{orden_id}/horas").json()) == 1


def test_un_cambio_de_tarifa_no_altera_lo_ya_costeado(cliente, orden_id):
    cliente.post(f"{URL}/{orden_id}/horas", json=horas())
    tarifa("60", "2026-11-15")
    antes = cliente.post(f"{URL}/{orden_id}/horas", json=horas(fecha="2026-11-14", horas="1")).json()
    despues = cliente.post(f"{URL}/{orden_id}/horas", json=horas(fecha="2026-11-15", horas="1")).json()
    assert (antes["costo"], despues["costo"]) == ("45.000000", "60.000000")
    registradas = cliente.get(f"{URL}/{orden_id}/horas").json()
    assert [h["costo"] for h in registradas] == ["112.500000", "45.000000", "60.000000"]
    assert cliente.get(f"{URL}/{orden_id}").json()["costo_acumulado"] == "217.500000"


def test_redondea_el_costo_a_centavos_mitad_hacia_arriba(cliente, orden_id):
    tarifa("33.33", "2026-11-11")
    hora = cliente.post(f"{URL}/{orden_id}/horas", json=horas(horas="0.25", fecha="2026-11-11")).json()
    assert hora["costo"] == "8.330000"  # 8.3325 → 8.33
    hora = cliente.post(f"{URL}/{orden_id}/horas", json=horas(horas="0.35", fecha="2026-11-11")).json()
    assert hora["costo"] == "11.670000"  # 11.6655 → 11.67


@pytest.mark.parametrize("valor", ["0", "-1", "abc", "1.234", "24.5", "NaN"])
def test_rechaza_horas_invalidas(cliente, orden_id, valor):
    assert cliente.post(f"{URL}/{orden_id}/horas", json=horas(horas=valor)).status_code == 400


def test_rechaza_fechas_y_datos_invalidos(cliente, orden_id):
    ruta = f"{URL}/{orden_id}/horas"
    assert cliente.post(ruta, json=horas(fecha="2999-01-01")).status_code == 400
    assert cliente.post(ruta, json=horas(fecha="2026-11-09")).status_code == 400  # antes de la apertura
    assert cliente.post(ruta, json=horas(mecanico=" ")).status_code == 422
    assert cliente.post(ruta, json=horas(tarea="")).status_code == 422
    assert cliente.post(f"{URL}/999/horas", json=horas()).status_code == 404
    assert cliente.get(f"{URL}/{orden_id}/horas").json() == []


def test_sin_tarifa_vigente_en_la_fecha_no_se_registran_horas(cliente, orden_id):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE tarifa_mano_obra"))
        db.commit()
    respuesta = cliente.post(f"{URL}/{orden_id}/horas", json=horas())
    assert respuesta.status_code == 409
    assert "No hay tarifa" in respuesta.json()["detail"]


def test_no_admite_horas_en_una_orden_cerrada(cliente, orden_id):
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE orden_trabajo SET estado = 'cerrada', fecha_cierre = '2026-11-13',"
                " costo_total = 0 WHERE id = :id"
            ),
            {"id": orden_id},
        )
        db.commit()
    respuesta = cliente.post(f"{URL}/{orden_id}/horas", json=horas())
    assert respuesta.status_code == 409
    assert "cerrada" in respuesta.json()["detail"]


def test_permisos(cliente, orden_id):
    from fastapi.testclient import TestClient

    from app.main import app

    anonimo = TestClient(app)
    ruta = f"{URL}/{orden_id}/horas"
    assert anonimo.get(ruta).status_code == 401
    assert anonimo.post(ruta, json=horas()).status_code == 401
    gerencia = _token(anonimo, "gerencia@empresa.gt")
    assert anonimo.get(ruta, headers=gerencia).status_code == 200
    assert anonimo.post(ruta, json=horas(), headers=gerencia).status_code == 403
    auxiliar = _token(anonimo, "auxiliar@empresa.gt")
    assert anonimo.post(ruta, json=horas(), headers=auxiliar).status_code == 201
