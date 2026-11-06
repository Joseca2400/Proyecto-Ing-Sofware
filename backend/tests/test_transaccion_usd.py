"""HU-1.07: transacciones en USD con monto original, tipo de cambio y equivalente en quetzales."""

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal

URL = "/api/v1/configuracion/transacciones-usd"
URL_TIPO = "/api/v1/configuracion/tipos-cambio"


@pytest.fixture(autouse=True)
def tablas_vacias():
    with SessionLocal() as db:
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()


def test_registra_usando_el_tipo_del_banguat_por_defecto(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": "1000.00"})

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["monto_usd"] == "1000.000000"
    assert cuerpo["tipo_cambio_aplicado"] == "7.75000000"
    assert cuerpo["monto_gtq"] == "7750.000000"
    assert cuerpo["justificacion"] is None
    assert cuerpo["fecha"] == "2026-11-02"


def test_registra_con_tipo_personalizado_y_justificacion(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(
        URL,
        json={
            "fecha": "2026-11-02",
            "monto_usd": "1000.00",
            "tipo_cambio_personalizado": "7.72",
            "justificacion": "El banco aplicó este tipo al comprar divisas",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["tipo_cambio_aplicado"] == "7.72000000"
    assert cuerpo["monto_gtq"] == "7720.000000"
    assert cuerpo["justificacion"] == "El banco aplicó este tipo al comprar divisas"


def test_calcula_el_monto_gtq_correctamente(cliente):
    # 8500 × 7.75120000 = 65885.200000
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75120000"})
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": "8500.00"})

    assert respuesta.status_code == 201
    assert respuesta.json()["monto_gtq"] == "65885.200000"


def test_rechaza_si_no_hay_tipo_cambio_para_la_fecha(cliente):
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": "1000.00"})

    assert respuesta.status_code == 409
    assert "cárguelo antes" in respuesta.json()["detail"]


@pytest.mark.parametrize("monto", ["0", "-100.00", "abc", ""])
def test_rechaza_monto_no_positivo_o_invalido(cliente, monto):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": monto})

    assert respuesta.status_code in (400, 422)
    assert "detail" in respuesta.json()


def test_rechaza_monto_como_numero_para_no_usar_float(cliente):
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": 1000.0})

    assert respuesta.status_code == 422


@pytest.mark.parametrize("tipo", ["0", "-5.00", "abc"])
def test_rechaza_tipo_personalizado_no_positivo_o_invalido(cliente, tipo):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(
        URL,
        json={
            "fecha": "2026-11-02",
            "monto_usd": "1000.00",
            "tipo_cambio_personalizado": tipo,
            "justificacion": "motivo",
        },
    )

    assert respuesta.status_code in (400, 422)
    assert "detail" in respuesta.json()


def test_rechaza_tipo_personalizado_sin_justificacion(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(
        URL,
        json={"fecha": "2026-11-02", "monto_usd": "1000.00", "tipo_cambio_personalizado": "7.72"},
    )

    assert respuesta.status_code == 400
    assert "justificación" in respuesta.json()["detail"]


def test_rechaza_tipo_personalizado_con_justificacion_vacia(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(
        URL,
        json={
            "fecha": "2026-11-02",
            "monto_usd": "1000.00",
            "tipo_cambio_personalizado": "7.72",
            "justificacion": "   ",
        },
    )

    assert respuesta.status_code == 400
    assert "justificación" in respuesta.json()["detail"]


def test_listar_del_mas_reciente_al_mas_antiguo(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    cliente.post(URL_TIPO, json={"fecha": "2026-11-03", "valor": "7.76"})
    cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": "500.00"})
    cliente.post(URL, json={"fecha": "2026-11-03", "monto_usd": "1000.00"})

    todas = cliente.get(URL).json()
    assert len(todas) == 2
    assert todas[0]["fecha"] == "2026-11-03"
    assert todas[1]["fecha"] == "2026-11-02"


def test_listar_con_filtro_desde(cliente):
    cliente.post(URL_TIPO, json={"fecha": "2026-11-02", "valor": "7.75"})
    cliente.post(URL_TIPO, json={"fecha": "2026-11-03", "valor": "7.76"})
    cliente.post(URL, json={"fecha": "2026-11-02", "monto_usd": "500.00"})
    cliente.post(URL, json={"fecha": "2026-11-03", "monto_usd": "1000.00"})

    filtradas = cliente.get(URL, params={"desde": "2026-11-03"}).json()
    assert len(filtradas) == 1
    assert filtradas[0]["fecha"] == "2026-11-03"


def test_la_base_rechaza_monto_no_positivo_aunque_bypass_servicio():
    # monto_usd = 0, pero monto_gtq positivo para que solo dispare la restricción de monto_usd.
    with SessionLocal() as db, pytest.raises(Exception, match="ck_transaccion_usd_monto_positivo"):
        db.execute(
            text(
                "INSERT INTO transaccion_usd (fecha, monto_usd, tipo_cambio_aplicado, monto_gtq) "
                "VALUES ('2026-11-02', 0, 7.75, 7.75)"
            )
        )
        db.commit()
