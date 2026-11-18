"""HU-3.02: parámetros de depreciación por unidad, valores por defecto y valor en libros."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.unidades import service as unidades
from tests.test_hoja_costo import API, TOTAL, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

ALTA = date(2025, 1, 15)


def _version(desde: date, vida: int, residual: str, fiscal: str = "20"):
    return SimpleNamespace(
        vigente_desde=desde,
        vida_util_meses=vida,
        valor_residual=Decimal(residual),
        porcentaje_fiscal=Decimal(fiscal),
    )


def _calculo(fecha: date, *versiones, costo: str = "60000"):
    versiones = versiones or (_version(ALTA, 60, "6000"),)
    return unidades.calcular_depreciacion(Decimal(costo), ALTA, list(versiones), fecha)


# ── Cálculo (criterio 4) ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("fecha", "meses"),
    [
        (date(2025, 1, 31), 0),  # el mes del alta no se deprecia
        (date(2025, 2, 27), 0),
        (date(2025, 2, 28), 1),  # primera cuota al cierre del mes siguiente
        (date(2025, 3, 1), 1),
        (date(2025, 12, 31), 11),
        (date(2024, 12, 31), 0),  # antes del alta
    ],
)
def test_convencion_de_meses(fecha, meses):
    assert unidades.meses_depreciados(ALTA, fecha) == meses


def test_linea_recta_financiera_y_fiscal_a_varias_fechas():
    # 60000 − 6000 de residual en 60 meses = 900 al mes; fiscal 20 % anual = 1000 al mes, sin residual.
    al_cierre = _calculo(date(2025, 12, 31))
    assert (al_cierre["depreciacion_financiera"], al_cierre["valor_libros_financiero"]) == (
        Decimal("9900.00"), Decimal("50100.00"),
    )  # fmt: skip
    assert (al_cierre["depreciacion_fiscal"], al_cierre["valor_libros_fiscal"]) == (
        Decimal("11000.00"), Decimal("49000.00"),
    )  # fmt: skip
    fin_de_vida = _calculo(date(2030, 1, 31))
    assert fin_de_vida["meses_depreciados"] == 60
    assert fin_de_vida["valor_libros_financiero"] == Decimal("6000.00")
    assert fin_de_vida["valor_libros_fiscal"] == Decimal("0.00")
    # Después de la vida útil no baja del residual ni el fiscal de cero.
    despues = _calculo(date(2032, 6, 30))
    assert (despues["valor_libros_financiero"], despues["valor_libros_fiscal"]) == (Decimal("6000.00"), 0)


def test_los_centavos_se_absorben_en_la_ultima_cuota():
    calculo = [
        _calculo(fecha, _version(ALTA, 3, "0"), costo="10000")["depreciacion_financiera"]
        for fecha in (date(2025, 2, 28), date(2025, 3, 31), date(2025, 4, 30), date(2025, 9, 30))
    ]
    # 3333.33, 3333.34 (6666.67 / 2 redondeado mitad hacia arriba) y 3333.33: llega exacto al costo.
    assert calculo == [Decimal("3333.33"), Decimal("6666.67"), Decimal("10000.00"), Decimal("10000.00")]


def test_un_cambio_aplica_hacia_adelante_sin_recalcular_lo_devengado():
    original = _version(ALTA, 60, "6000")
    cambio = _version(date(2026, 1, 1), 36, "0")
    assert _calculo(date(2025, 12, 31), original, cambio)["depreciacion_financiera"] == Decimal("9900.00")
    # Mes 12: (60000 − 9900 − 0) / (36 − 11 meses ya depreciados) = 2004.
    enero = _calculo(date(2026, 1, 31), original, cambio)
    assert (enero["depreciacion_financiera"], enero["vida_util_meses"]) == (Decimal("11904.00"), 36)
    assert _calculo(date(2028, 1, 31), original, cambio)["valor_libros_financiero"] == Decimal("0.00")
    # Un residual mayor que el valor en libros detiene la depreciación, sin revertir lo devengado.
    alto = _version(date(2026, 1, 1), 60, "55000")
    assert _calculo(date(2026, 6, 30), original, alto)["valor_libros_financiero"] == Decimal("50100.00")


def test_cambio_del_porcentaje_fiscal():
    cambio = _version(date(2026, 1, 1), 60, "6000", fiscal="10")
    calculo = _calculo(date(2026, 2, 28), _version(ALTA, 60, "6000"), cambio)
    assert calculo["depreciacion_fiscal"] == Decimal("11000") + 2 * Decimal("500.00")


# ── Alta, parámetros y valores por defecto ─────────────────────────────────────


def test_el_alta_guarda_los_parametros_propuestos_del_tipo(cliente):
    ciclo_completo(cliente)
    (candidata,) = cliente.get(f"{API}/unidades/alta-flota/candidatas").json()
    assert (candidata["vida_util_meses"], candidata["valor_residual"], candidata["porcentaje_fiscal"]) == (
        60, "7719.690000", "20.00",
    )  # fmt: skip
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json={"fecha": "2026-11-15"}).status_code == 201
    (version,) = cliente.get(f"{API}/unidades/{VIN}/parametros-depreciacion").json()
    assert (version["vigente_desde"], version["vida_util_meses"], version["valor_residual"]) == (
        "2026-11-15", 60, "7719.690000",
    )  # fmt: skip


def test_alta_con_parametros_del_contador_y_valor_en_libros(cliente):
    ciclo_completo(cliente)
    cuerpo = {"fecha": "2024-01-10", "vida_util_meses": 48, "valor_residual": "0", "porcentaje_fiscal": "25"}
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json=cuerpo).status_code == 201

    valor = cliente.get(f"{API}/unidades/{VIN}/valor-libros", params={"fecha": "2024-12-31"}).json()
    assert (valor["meses_depreciados"], Decimal(valor["costo"])) == (11, TOTAL)
    esperado = unidades.calcular_depreciacion(
        TOTAL, date(2024, 1, 10), [_version(date(2024, 1, 10), 48, "0", "25")], date(2024, 12, 31)
    )
    assert Decimal(valor["valor_libros_financiero"]) == esperado["valor_libros_financiero"]
    assert Decimal(valor["depreciacion_fiscal"]) == esperado["depreciacion_fiscal"]
    with SessionLocal() as db:
        assert unidades.valor_en_libros(db, VIN, date(2024, 12, 31))["porcentaje_fiscal"] == Decimal("25.00")


def test_rechaza_parametros_invalidos_al_alta(cliente):
    ciclo_completo(cliente)
    for cambio, mensaje in (
        ({"valor_residual": "99999999"}, "menor que el costo"),
        ({"vida_util_meses": 0}, "vida útil"),
        ({"porcentaje_fiscal": "120"}, "porcentaje fiscal"),
        ({"valor_residual": "abc"}, "no es un número"),
    ):
        respuesta = cliente.post(f"{API}/unidades/{VIN}/alta-flota", json={"fecha": "2026-11-15", **cambio})
        assert respuesta.status_code == 400, cambio
        assert mensaje in respuesta.json()["detail"]
    assert cliente.get(f"{API}/unidades/{VIN}").json()["estado"] == "lista"


def test_cambio_de_parametros_prospectivo_y_auditado(cliente):
    ciclo_completo(cliente)
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json={"fecha": "2024-01-10"}).status_code == 201
    inicio_mes = date.today().replace(day=1)
    url = f"{API}/unidades/{VIN}/parametros-depreciacion"
    cuerpo = {"vida_util_meses": 72, "valor_residual": "5000", "porcentaje_fiscal": "20"}

    pasado = cliente.post(url, json={**cuerpo, "vigente_desde": "2024-06-01"})
    assert pasado.status_code == 400
    assert "prospectivo" in pasado.json()["detail"]
    devengados = unidades.meses_depreciados(date(2024, 1, 10), date.fromordinal(inicio_mes.toordinal() - 1))
    corta = cliente.post(
        url, json={**cuerpo, "vigente_desde": str(inicio_mes), "vida_util_meses": devengados}
    )
    assert corta.status_code == 400
    assert "ya depreciados" in corta.json()["detail"]

    antes = cliente.get(f"{API}/unidades/{VIN}/valor-libros", params={"fecha": "2025-12-31"}).json()
    nueva = cliente.post(url, json={**cuerpo, "vigente_desde": str(inicio_mes)})
    assert nueva.status_code == 201, nueva.text
    assert cliente.post(url, json={**cuerpo, "vigente_desde": str(inicio_mes)}).status_code == 400
    versiones = cliente.get(url).json()
    assert [v["vida_util_meses"] for v in versiones] == [60, 72]
    # Lo devengado antes del cambio no se recalcula.
    despues = cliente.get(f"{API}/unidades/{VIN}/valor-libros", params={"fecha": "2025-12-31"}).json()
    assert despues == antes
    with SessionLocal() as db:
        registro = db.execute(
            text(
                "SELECT accion, vin FROM bitacora WHERE entidad = 'parametro_depreciacion'"
                " ORDER BY id DESC LIMIT 1"
            )
        ).one()
    assert (registro.accion, registro.vin) == ("crear", VIN)


def test_valores_por_defecto_por_tipo(cliente):
    tipos = cliente.get(f"{API}/unidades/depreciacion/tipos").json()
    assert len(tipos) == 8
    assert {t["tipo_vehiculo"]: t["porcentaje_fiscal"] for t in tipos}["pickup"] == "20.00"
    url = f"{API}/unidades/depreciacion/tipos/pickup"
    try:
        respuesta = cliente.put(
            url, json={"vida_util_meses": 48, "porcentaje_residual": "15", "porcentaje_fiscal": "20"}
        )
        assert respuesta.status_code == 200
        assert (respuesta.json()["vida_util_meses"], respuesta.json()["porcentaje_residual"]) == (48, "15.00")
        assert (
            cliente.put(
                url, json={"vida_util_meses": 48, "porcentaje_residual": "100", "porcentaje_fiscal": "20"}
            ).status_code
            == 400
        )
        assert (
            cliente.put(
                f"{API}/unidades/depreciacion/tipos/avion",
                json={"vida_util_meses": 1, "porcentaje_residual": "0", "porcentaje_fiscal": "20"},
            ).status_code
            == 404
        )
        with SessionLocal() as db:
            assert unidades.propuesta_depreciacion(db, "pickup", Decimal("100000"))[
                "valor_residual"
            ] == Decimal("15000.00")
    finally:
        cliente.put(url, json={"vida_util_meses": 60, "porcentaje_residual": "10", "porcentaje_fiscal": "20"})


def test_permisos(cliente):
    anonimo = TestClient(app)
    assert anonimo.get(f"{API}/unidades/depreciacion/tipos").status_code == 401
    assert anonimo.get(f"{API}/unidades/{VIN}/valor-libros").status_code == 401
    auxiliar = _token(anonimo, "auxiliar@empresa.gt")
    cuerpo = {"vida_util_meses": 48, "porcentaje_residual": "15", "porcentaje_fiscal": "20"}
    assert (
        anonimo.put(f"{API}/unidades/depreciacion/tipos/pickup", json=cuerpo, headers=auxiliar).status_code
        == 403
    )
    version = {
        "vigente_desde": "2030-01-01",
        "vida_util_meses": 48,
        "valor_residual": "0",
        "porcentaje_fiscal": "20",
    }
    assert (
        anonimo.post(
            f"{API}/unidades/{VIN}/parametros-depreciacion", json=version, headers=auxiliar
        ).status_code
        == 403
    )


def test_valor_en_libros_sin_alta(cliente):
    ciclo_completo(cliente)
    assert cliente.get(f"{API}/unidades/{VIN}/valor-libros").status_code == 404
