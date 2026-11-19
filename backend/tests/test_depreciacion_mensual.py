"""HU-2.07: depreciación mensual de la flota, con su partida en borrador y el detalle fiscal."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.unidades import service as unidades
from tests.test_hoja_costo import API, OTRO_VIN, TOTAL, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

URL = f"{API}/contabilidad/depreciaciones"
# Alta el 10/01/2024 con 48 meses, sin residual y 25 % fiscal: la primera cuota es la de febrero.
PARAMETROS = {"fecha": "2024-01-10", "vida_util_meses": 48, "valor_residual": "0", "porcentaje_fiscal": "25"}
CUOTA = Decimal("1608.27")  # 77196.85 / 48
FISCAL = Decimal("1608.27")  # 77196.85 × 25 % / 12


@pytest.fixture
def flota(cliente):
    ciclo_completo(cliente)
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json=PARAMETROS).status_code == 201


@pytest.fixture
def gerente() -> TestClient:
    return TestClient(app, headers=_token(TestClient(app), "gerente.financiero@empresa.gt"))


def _calcular(cliente, anio: int, mes: int):
    return cliente.post(URL, json={"anio": anio, "mes": mes})


def _contabilizar(cliente, gerente, partida_id: int) -> None:
    assert cliente.post(f"{API}/contabilidad/partidas/{partida_id}/enviar-a-revision").status_code == 200
    assert gerente.post(f"{API}/contabilidad/partidas/{partida_id}/contabilizar").status_code == 200


def test_genera_la_partida_en_borrador_con_una_linea_por_unidad(cliente, flota):
    respuesta = _calcular(cliente, 2024, 2)
    assert respuesta.status_code == 201, respuesta.text
    calculo = respuesta.json()
    partida = calculo["partida"]
    assert (partida["estado"], partida["fecha"], partida["origen"]) == ("borrador", "2024-02-29", "manual")
    debe, haber = partida["lineas"]
    assert (debe["vin"], debe["linea_negocio"], Decimal(debe["debe"])) == (VIN, "alquiler", CUOTA)
    assert (haber["vin"], haber["linea_negocio"], Decimal(haber["haber"])) == (VIN, "alquiler", CUOTA)
    (linea,) = calculo["lineas"]
    assert (linea["vin"], Decimal(linea["financiera"]), Decimal(linea["fiscal"])) == (VIN, CUOTA, FISCAL)
    assert Decimal(calculo["total_financiera"]) == CUOTA
    assert cliente.get(URL).json()[0]["id"] == calculo["id"]


def test_guarda_la_diferencia_entre_la_fiscal_y_la_financiera(cliente):
    ciclo_completo(cliente)
    cuerpo = {**PARAMETROS, "vida_util_meses": 60, "porcentaje_fiscal": "20", "valor_residual": "7719.69"}
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json=cuerpo).status_code == 201
    (linea,) = _calcular(cliente, 2024, 2).json()["lineas"]
    # Financiera: (77196.85 − 7719.69) / 60 = 1157.95; fiscal: 77196.85 × 20 % / 12 = 1286.61.
    assert (linea["financiera"], linea["fiscal"], linea["diferencia"]) == (
        "1157.950000", "1286.610000", "128.660000",
    )  # fmt: skip


def test_recalcular_reemplaza_el_borrador_y_contabilizado_lo_impide(cliente, gerente, flota):
    primera = _calcular(cliente, 2024, 2).json()
    segunda = _calcular(cliente, 2024, 2).json()
    assert segunda["partida"]["id"] != primera["partida"]["id"]
    assert cliente.get(f"{API}/contabilidad/partidas/{primera['partida']['id']}").status_code == 404
    assert len(cliente.get(URL).json()) == 1

    _contabilizar(cliente, gerente, segunda["partida"]["id"])
    respuesta = _calcular(cliente, 2024, 2)
    assert respuesta.status_code == 409
    assert "ya está contabilizada" in respuesta.json()["detail"]


def test_la_partida_de_la_depreciacion_no_se_edita_a_mano(cliente, flota):
    partida = _calcular(cliente, 2024, 2).json()["partida"]
    cuerpo = {
        "fecha": partida["fecha"],
        "concepto": "Otra cosa",
        "lineas": [
            {"cuenta_id": linea["cuenta_id"], "lado": lado, "monto": "1", "vin": VIN}
            for linea, lado in zip(partida["lineas"], ("debe", "haber"), strict=True)
        ],
    }
    respuesta = cliente.put(f"{API}/contabilidad/partidas/{partida['id']}", json=cuerpo)
    assert respuesta.status_code == 409
    assert "vuelva a calcular" in respuesta.json()["detail"]


def test_los_meses_van_en_orden_y_un_mes_sin_calcular_se_recupera(cliente, gerente, flota):
    febrero = _calcular(cliente, 2024, 2).json()
    # Con febrero sin contabilizar no se calcula marzo.
    respuesta = _calcular(cliente, 2024, 3)
    assert respuesta.status_code == 409
    assert "Contabilice primero la depreciación de febrero de 2024" in respuesta.json()["detail"]
    _contabilizar(cliente, gerente, febrero["partida"]["id"])

    # Abril sin haber calculado marzo: trae las dos cuotas, y marzo ya no se calcula aparte.
    abril = _calcular(cliente, 2024, 4).json()
    (linea,) = abril["lineas"]
    with SessionLocal() as db:
        acumulada = unidades.valor_en_libros(db, VIN, date(2024, 4, 30))
    assert Decimal(linea["financiera"]) == acumulada["depreciacion_financiera"] - CUOTA
    assert Decimal(linea["fiscal"]) == acumulada["depreciacion_fiscal"] - FISCAL
    respuesta = _calcular(cliente, 2024, 3)
    assert respuesta.status_code == 409
    assert "mes posterior" in respuesta.json()["detail"]


def test_no_deprecia_mas_alla_del_residual_ni_unidades_fuera_de_la_flota(cliente, gerente):
    # Dos unidades con alta en enero de 2020; una pasa luego a venta y deja de depreciarse.
    for numero, vin in enumerate((VIN, OTRO_VIN), start=1):
        ciclo_completo(cliente, vin, numero=numero)
        cuerpo = {**PARAMETROS, "fecha": "2020-01-10"}
        assert cliente.post(f"{API}/unidades/{vin}/alta-flota", json=cuerpo).status_code == 201
    with SessionLocal() as db:
        db.execute(text("UPDATE unidad SET estado = 'en_venta' WHERE vin = :vin"), {"vin": OTRO_VIN})
        db.commit()

    # Al final de la vida útil (48 meses, enero de 2024) la partida lleva todo el costo y nada más.
    total = _calcular(cliente, 2024, 1).json()
    assert [linea["vin"] for linea in total["lineas"]] == [VIN]
    assert Decimal(total["total_financiera"]) == TOTAL
    _contabilizar(cliente, gerente, total["partida"]["id"])
    respuesta = _calcular(cliente, 2024, 2)
    assert respuesta.status_code == 400
    assert "No hay unidades" in respuesta.json()["detail"]


def test_el_mes_del_alta_no_se_deprecia_y_un_mes_futuro_se_rechaza(cliente, flota):
    assert _calcular(cliente, 2024, 1).status_code == 400
    respuesta = _calcular(cliente, date.today().year + 1, 1)
    assert respuesta.status_code == 400
    assert "futura" in respuesta.json()["detail"]
    assert _calcular(cliente, 2024, 13).status_code == 422


def test_sin_la_regla_de_contabilizacion_no_calcula(cliente, flota):
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE regla_contabilizacion SET cuenta_codigo = NULL "
                "WHERE documento_tipo = 'depreciacion' AND concepto = 'gasto'"
            )
        )
        db.commit()
    try:
        respuesta = _calcular(cliente, 2024, 2)
        assert respuesta.status_code == 409
        assert "depreciacion · gasto" in respuesta.json()["detail"]
    finally:
        with SessionLocal() as db:
            db.execute(
                text(
                    "UPDATE regla_contabilizacion SET cuenta_codigo = '6.4' "
                    "WHERE documento_tipo = 'depreciacion' AND concepto = 'gasto'"
                )
            )
            db.commit()


def test_permisos(flota):
    assert TestClient(app).post(URL, json={"anio": 2024, "mes": 2}).status_code == 401
    gerencia = TestClient(app, headers=_token(TestClient(app), "gerencia@empresa.gt"))
    assert gerencia.post(URL, json={"anio": 2024, "mes": 2}).status_code == 403
    assert gerencia.get(URL).status_code == 200
    auxiliar = TestClient(app, headers=_token(TestClient(app), "auxiliar@empresa.gt"))
    assert auxiliar.post(URL, json={"anio": 2024, "mes": 2}).status_code == 201
    assert len(auxiliar.get(URL).json()) == 1
