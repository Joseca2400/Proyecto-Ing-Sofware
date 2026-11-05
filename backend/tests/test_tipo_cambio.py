"""HU-1.06: carga manual del tipo de cambio y bloqueo cuando falta."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion import service

URL = "/api/v1/configuracion/tipos-cambio"


@pytest.fixture(autouse=True)
def tabla_vacia():
    with SessionLocal() as db:
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()


def test_carga_manual_guarda_fecha_valor_y_origen(cliente):
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "valor": "7.7512"})
    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["fecha"] == "2026-11-02"
    assert cuerpo["valor"] == "7.75120000"  # viaja como texto, con 8 decimales
    assert cuerpo["origen"] == "manual"


def test_consulta_por_fecha_y_listado_del_mas_reciente_al_mas_antiguo(cliente):
    cliente.post(URL, json={"fecha": "2026-11-02", "valor": "7.75"})
    cliente.post(URL, json={"fecha": "2026-11-03", "valor": "7.76"})

    assert cliente.get(f"{URL}/2026-11-03").json()["valor"] == "7.76000000"
    assert [t["fecha"] for t in cliente.get(URL).json()] == ["2026-11-03", "2026-11-02"]
    assert [t["fecha"] for t in cliente.get(URL, params={"desde": "2026-11-03"}).json()] == ["2026-11-03"]


@pytest.mark.parametrize("valor", ["0", "-7.75", "abc", "", "7.123456789", "NaN", "Infinity"])
def test_rechaza_valores_que_no_son_positivos_o_validos(cliente, valor):
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "valor": valor})
    assert respuesta.status_code == 400
    assert "detail" in respuesta.json()


def test_rechaza_el_valor_como_numero_para_no_usar_float(cliente):
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "valor": 7.75})
    assert respuesta.status_code == 422


def test_no_permite_dos_tipos_para_la_misma_fecha(cliente):
    cliente.post(URL, json={"fecha": "2026-11-02", "valor": "7.75"})
    respuesta = cliente.post(URL, json={"fecha": "2026-11-02", "valor": "7.80"})
    assert respuesta.status_code == 409
    assert cliente.get(f"{URL}/2026-11-02").json()["valor"] == "7.75000000"


def test_no_permite_fechas_futuras(cliente):
    manana = (date.today() + timedelta(days=1)).isoformat()
    assert cliente.post(URL, json={"fecha": manana, "valor": "7.75"}).status_code == 400


def test_consultar_una_fecha_sin_tipo_responde_404(cliente):
    respuesta = cliente.get(f"{URL}/2026-01-01")
    assert respuesta.status_code == 404
    assert "01/01/2026" in respuesta.json()["detail"]


def test_tipo_cambio_de_bloquea_la_transaccion_si_falta():
    with SessionLocal() as db:
        with pytest.raises(ErrorNegocio) as error:
            service.tipo_cambio_de(db, date(2026, 1, 1))
    assert error.value.status == 409
    assert "cárguelo antes" in error.value.mensaje


def test_tipo_cambio_de_devuelve_el_decimal_exacto(cliente):
    cliente.post(URL, json={"fecha": "2026-11-02", "valor": "7.75123456"})
    with SessionLocal() as db:
        assert service.tipo_cambio_de(db, date(2026, 11, 2)) == Decimal("7.75123456")


def test_la_base_rechaza_un_valor_no_positivo_aunque_se_salte_el_servicio():
    with SessionLocal() as db, pytest.raises(Exception, match="ck_tipo_cambio_valor_positivo"):
        db.execute(text("INSERT INTO tipo_cambio (fecha, valor, origen) VALUES ('2026-11-02', 0, 'manual')"))
        db.commit()
