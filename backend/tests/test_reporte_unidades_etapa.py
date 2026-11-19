"""HU-7.04: unidades por etapa del ciclo con su valor, días promedio y las que superan el plazo."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.unidades import service as unidades
from tests.test_hoja_costo import API, OTRO_VIN, TOTAL, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

URL = f"{API}/reportes/unidades-por-etapa"
NUEVO_VIN = "JHMCM56557C404454"


def _hace_dias(vin: str, dias: int) -> None:
    """Mueve al pasado el último cambio de estado de la unidad."""
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE cambio_estado_unidad SET fecha = now() - make_interval(days => :dias)"
                " WHERE id = (SELECT max(c.id) FROM cambio_estado_unidad c"
                " JOIN unidad u ON u.id = c.unidad_id WHERE u.vin = :vin)"
            ),
            {"vin": vin, "dias": dias},
        )
        db.commit()


def _preparar(cliente) -> None:
    ciclo_completo(cliente, VIN, numero=1)
    ciclo_completo(cliente, OTRO_VIN, numero=2)
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json={"fecha": "2024-01-10"}).status_code == 201
    unidad = {"vin": NUEVO_VIN, "marca": "Honda", "linea": "Fit", "modelo": 2010, "color": "Azul"}
    assert cliente.post(f"{API}/unidades", json={**unidad, "tipo_vehiculo": "sedan"}).status_code == 201
    _hace_dias(OTRO_VIN, 40)
    _hace_dias(NUEVO_VIN, 10)


def test_cantidad_valor_y_dias_por_estado(cliente):
    _preparar(cliente)
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200, respuesta.text
    reporte = respuesta.json()
    estados = {e["estado"]: e for e in reporte["estados"]}
    with SessionLocal() as db:
        en_libros = unidades.valor_en_libros(db, VIN, date.today())["valor_libros_financiero"]

    assert reporte["limite_dias"] == 30
    assert (estados["en_flota"]["unidades"], Decimal(estados["en_flota"]["valor"])) == (1, en_libros)
    assert en_libros < TOTAL  # ya se depreció desde 2024
    assert (estados["lista"]["unidades"], Decimal(estados["lista"]["valor"])) == (1, TOTAL)
    assert (estados["lista"]["dias_promedio"], estados["lista"]["excedidas"]) == (40, 1)
    assert (estados["en_transito"]["unidades"], estados["en_transito"]["valor"]) == (1, "0.000000")
    assert (estados["en_transito"]["dias_promedio"], estados["en_transito"]["excedidas"]) == (10, 0)
    assert estados["vendida"] == {
        "estado": "vendida",
        "unidades": 0,
        "valor": "0.000000",
        "dias_promedio": 0,
        "excedidas": 0,
    }
    assert Decimal(reporte["valor_total"]) == en_libros + TOTAL

    por_vin = {u["vin"]: u for u in reporte["unidades"]}
    assert (por_vin[VIN]["valor_en_libros"], por_vin[OTRO_VIN]["valor_en_libros"]) == (True, False)
    assert (por_vin[OTRO_VIN]["excede"], por_vin[NUEVO_VIN]["excede"]) == (True, False)
    # Ordenadas por estado del ciclo.
    assert [u["estado"] for u in reporte["unidades"]] == ["en_transito", "lista", "en_flota"]


def test_el_plazo_es_configurable(cliente):
    _preparar(cliente)
    reporte = cliente.get(URL, params={"limite_dias": 5}).json()
    assert {u["vin"] for u in reporte["unidades"] if u["excede"]} == {OTRO_VIN, NUEVO_VIN}
    assert cliente.get(URL, params={"limite_dias": 0}).status_code == 422


def test_permisos(cliente):
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.get(URL, headers=_token(anonimo, "auxiliar@empresa.gt")).status_code == 403
    for correo in ("gerencia@empresa.gt", "gerente.financiero@empresa.gt"):
        assert anonimo.get(URL, headers=_token(anonimo, correo)).status_code == 200
