"""HU-3.14: regla de fin de vida útil en flota y alerta de las unidades que la alcanzan."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.unidades import service as unidades
from tests.test_hoja_costo import API, OTRO_VIN, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

URL = f"{API}/unidades/fin-vida-util"


@pytest.fixture(autouse=True)
def sin_regla(base_limpia):  # noqa: F811
    with SessionLocal() as db:
        db.execute(text("DELETE FROM regla_fin_vida"))
        db.commit()


def _kilometraje(vin: str, km: int) -> None:
    with SessionLocal() as db:
        db.execute(text("UPDATE unidad SET kilometraje = :km WHERE vin = :vin"), {"km": km, "vin": vin})
        db.commit()


def _flota(cliente) -> None:
    """VIN en flota desde 2024 (más de 24 meses); OTRO_VIN dada de alta este mes."""
    ciclo_completo(cliente, VIN, numero=1)
    ciclo_completo(cliente, OTRO_VIN, numero=2)
    for vin, fecha in ((VIN, "2024-01-10"), (OTRO_VIN, str(date.today()))):
        assert cliente.post(f"{API}/unidades/{vin}/alta-flota", json={"fecha": fecha}).status_code == 201


@pytest.mark.parametrize(
    ("alta", "fecha", "meses"),
    [
        (date(2025, 1, 15), date(2025, 2, 14), 0),
        (date(2025, 1, 15), date(2025, 2, 15), 1),
        (date(2025, 1, 31), date(2026, 1, 31), 12),
        (date(2025, 1, 15), date(2024, 12, 1), 0),
    ],
)
def test_meses_en_flota(alta, fecha, meses):
    assert unidades.meses_en_flota(alta, fecha) == meses


def test_sin_regla_no_hay_alertas(cliente):
    _flota(cliente)
    assert cliente.get(URL).json() == {"regla": None, "unidades": []}


def test_umbrales_alcanzado_y_por_alcanzar(cliente):
    _flota(cliente)
    regla = cliente.put(f"{URL}/regla", json={"kilometraje_limite": 100000, "meses_limite": 24})
    assert regla.status_code == 200, regla.text
    assert regla.json()["porcentaje_aviso"] == "90.00"

    _kilometraje(OTRO_VIN, 89999)  # bajo el 90 % del límite: no aparece
    (alerta,) = cliente.get(URL).json()["unidades"]
    assert (alerta["vin"], alerta["situacion"]) == (VIN, "alcanzado")  # más de 24 meses en flota
    with SessionLocal() as db:
        libros = unidades.valor_en_libros(db, VIN, date.today())
    assert alerta["valor_libros_financiero"] == f"{libros['valor_libros_financiero']:.6f}"

    _kilometraje(OTRO_VIN, 90000)  # justo el 90 %: por alcanzar
    alertas = cliente.get(URL).json()["unidades"]
    assert [(a["vin"], a["situacion"]) for a in alertas] == [(VIN, "alcanzado"), (OTRO_VIN, "por_alcanzar")]
    _kilometraje(OTRO_VIN, 100000)
    assert {a["situacion"] for a in cliente.get(URL).json()["unidades"]} == {"alcanzado"}

    # La alerta no cambia la unidad.
    assert cliente.get(f"{API}/unidades/{VIN}").json()["estado"] == "en_flota"


def test_regla_solo_por_kilometraje_y_aviso_configurable(cliente):
    _flota(cliente)
    regla = {"kilometraje_limite": 100000, "porcentaje_aviso": "50"}
    assert cliente.put(f"{URL}/regla", json=regla).status_code == 200
    _kilometraje(OTRO_VIN, 50000)
    # VIN no tiene kilometraje: sin límite por meses no aparece aunque lleve años en flota.
    assert [(a["vin"], a["situacion"]) for a in cliente.get(URL).json()["unidades"]] == [
        (OTRO_VIN, "por_alcanzar")
    ]


def test_valida_la_regla_y_la_audita(cliente):
    for cuerpo, mensaje in (
        ({}, "Indique el límite"),
        ({"meses_limite": 0}, "mayores que cero"),
        ({"meses_limite": 60, "porcentaje_aviso": "120"}, "porcentaje de aviso"),
    ):
        respuesta = cliente.put(f"{URL}/regla", json=cuerpo)
        assert respuesta.status_code == 400
        assert mensaje in respuesta.json()["detail"]
    assert cliente.put(f"{URL}/regla", json={"meses_limite": 60}).status_code == 200
    assert (
        cliente.put(f"{URL}/regla", json={"meses_limite": 48, "kilometraje_limite": 150000}).status_code
        == 200
    )
    with SessionLocal() as db:
        cambio = db.execute(
            text(
                "SELECT accion, anteriores, nuevos FROM bitacora"
                " WHERE entidad = 'regla_fin_vida' ORDER BY id DESC"
            )
        ).first()
    assert cambio.accion == "modificar"
    assert (cambio.anteriores["meses_limite"], cambio.nuevos["meses_limite"]) == (60, 48)
    assert cliente.get(URL).json()["regla"]["kilometraje_limite"] == 150000


def test_permisos(cliente):
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.get(URL, headers=_token(anonimo, "auxiliar@empresa.gt")).status_code == 403
    assert anonimo.get(URL, headers=_token(anonimo, "gerencia@empresa.gt")).status_code == 200
    regla = {"meses_limite": 60}
    gerencia = _token(anonimo, "gerencia@empresa.gt")
    assert anonimo.put(f"{URL}/regla", json=regla, headers=gerencia).status_code == 403
    financiero = _token(anonimo, "gerente.financiero@empresa.gt")
    assert anonimo.put(f"{URL}/regla", json=regla, headers=financiero).status_code == 200
