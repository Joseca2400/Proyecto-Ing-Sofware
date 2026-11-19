"""HU-7.02 (hasta la flota): rentabilidad de cada unidad en su ciclo, con filtros y orden.

Reutiliza la flota de HU-3.13: `VIN` comprada, dada de alta, depreciada, con mantenimiento y un
contrato de tres días facturado; `OTRO_VIN` comprada y en "lista". Se agrega `TOYOTA`, registrada
sin compra.
"""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from tests.test_depreciacion_mensual import CUOTA, gerente  # noqa: F401
from tests.test_hoja_costo import API, OTRO_VIN, TOTAL, VIN, base_limpia  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_rentabilidad import ALQUILER, CARGOS, MANTENIMIENTO, flota  # noqa: F401
from tests.test_taller_ordenes import _token

URL = f"{API}/reportes/rentabilidad/ciclo"
TOYOTA = "JHMCM56557C404454"
ALTA = date(2024, 1, 10)
RESULTADO = ALQUILER + CARGOS - MANTENIMIENTO - CUOTA


@pytest.fixture
def unidades(cliente, flota):  # noqa: F811
    unidad = {"vin": TOYOTA, "marca": "Toyota", "linea": "Yaris", "modelo": 2015, "color": "Rojo"}
    assert cliente.post(f"{API}/unidades", json={**unidad, "tipo_vehiculo": "sedan"}).status_code == 201


def _por_vin(reporte: dict) -> dict:
    return {u["vin"]: u for u in reporte["unidades"]}


def test_costo_ingresos_costos_y_resultado_por_vin(cliente, unidades):
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200, respuesta.text
    reporte = respuesta.json()
    unidad = _por_vin(reporte)[VIN]

    # Costo de la hoja de costo (HU-4.08).
    assert Decimal(unidad["compra"]) == Decimal("70331.25")
    assert Decimal(unidad["importacion"]) == Decimal("5633.10")
    assert Decimal(unidad["reacondicionamiento"]) == Decimal("1232.50")
    assert Decimal(unidad["costo_total"]) == TOTAL
    assert (unidad["proveedor"], unidad["fecha_compra"], unidad["fecha_alta"]) == (
        "Copart Inc.",
        "2026-10-20",
        "2024-01-10",
    )
    # Del mayor, toda la historia de la unidad.
    assert Decimal(unidad["ingreso_alquiler"]) == ALQUILER + CARGOS
    assert Decimal(unidad["mantenimiento"]) == MANTENIMIENTO
    assert Decimal(unidad["depreciacion"]) == CUOTA
    assert (unidad["seguro"], unidad["marchamo"]) == (None, None)
    assert Decimal(unidad["resultado"]) == RESULTADO
    rentabilidad = (RESULTADO * 100 / TOTAL).quantize(Decimal("0.01"), ROUND_HALF_UP)
    assert unidad["rentabilidad"] == f"{rentabilidad}" == "-1.08"

    dias = (date.today() - ALTA).days
    assert (unidad["dias_en_flota"], unidad["dias_alquilados"]) == (dias, 3)
    ocupacion = (Decimal(300) / dias).quantize(Decimal("0.01"), ROUND_HALF_UP)
    assert unidad["ocupacion"] == f"{ocupacion}"

    sin_alta = _por_vin(reporte)[OTRO_VIN]
    assert (sin_alta["dias_en_flota"], sin_alta["ocupacion"], sin_alta["rentabilidad"]) == (
        None,
        None,
        "0.00",
    )
    sin_compra = _por_vin(reporte)[TOYOTA]
    assert (sin_compra["costo_total"], sin_compra["rentabilidad"], sin_compra["proveedor"]) == (
        "0.000000",
        None,
        None,
    )

    totales = reporte["totales"]
    assert Decimal(totales["costo_total"]) == 2 * TOTAL
    assert Decimal(totales["resultado"]) == RESULTADO
    assert totales["rentabilidad"] == f"{(RESULTADO * 50 / TOTAL).quantize(Decimal('0.01'), ROUND_HALF_UP)}"
    assert totales["seguro"] is None
    assert len(reporte["pendientes"]) == 2


def test_ordena_por_resultado_o_por_rentabilidad(cliente, unidades):
    por_resultado = cliente.get(URL).json()
    assert [u["vin"] for u in por_resultado["unidades"]] == sorted([OTRO_VIN, TOYOTA]) + [VIN]

    por_rentabilidad = cliente.get(URL, params={"orden": "rentabilidad"}).json()
    assert por_rentabilidad["orden"] == "rentabilidad"
    # Sin costo no hay rentabilidad: va al final.
    assert [u["vin"] for u in por_rentabilidad["unidades"]] == [OTRO_VIN, VIN, TOYOTA]

    assert cliente.get(URL, params={"orden": "otro"}).status_code == 422


@pytest.mark.parametrize(
    ("filtro", "vins"),
    [
        ({"estado": "en_flota"}, {VIN}),
        ({"estado": "vendida"}, set()),
        ({"marca": "toyota"}, {TOYOTA}),
        ({"linea": "Accord"}, {VIN, OTRO_VIN}),
        ({"anio_compra": 2026}, {VIN, OTRO_VIN}),
        ({"anio_compra": 2025}, set()),
    ],
)
def test_filtros(cliente, unidades, filtro, vins):
    assert set(_por_vin(cliente.get(URL, params=filtro).json())) == vins


def test_filtra_por_proveedor_de_origen(cliente, unidades):
    filtros = cliente.get(URL).json()["filtros"]
    assert filtros["marcas"] == ["Honda", "Toyota"]
    assert filtros["anios_compra"] == [2026]
    (proveedor,) = filtros["proveedores"]
    assert proveedor["nombre"] == "Copart Inc."
    reporte = cliente.get(URL, params={"proveedor_id": proveedor["id"]}).json()
    assert set(_por_vin(reporte)) == {VIN, OTRO_VIN}
    assert cliente.get(URL, params={"proveedor_id": proveedor["id"] + 99}).json()["unidades"] == []


def test_los_dias_en_flota_terminan_al_salir_de_la_flota(cliente, unidades):
    assert (
        cliente.post(
            f"{API}/unidades/{VIN}/estado", json={"estado": "en_venta", "documento": "Memo"}
        ).status_code
        == 200
    )
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE cambio_estado_unidad SET fecha = '2025-01-10T12:00:00Z'"
                " WHERE id = (SELECT max(c.id) FROM cambio_estado_unidad c"
                " JOIN unidad u ON u.id = c.unidad_id WHERE u.vin = :vin)"
            ),
            {"vin": VIN},
        )
        db.commit()
    unidad = _por_vin(cliente.get(URL).json())[VIN]
    assert (unidad["estado"], unidad["dias_en_flota"]) == ("en_venta", 366)  # 2024 es bisiesto


def test_permisos():
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.get(URL, headers=_token(anonimo, "auxiliar@empresa.gt")).status_code == 403
    for correo in ("gerencia@empresa.gt", "gerente.financiero@empresa.gt"):
        assert anonimo.get(URL, headers=_token(anonimo, correo)).status_code == 200
