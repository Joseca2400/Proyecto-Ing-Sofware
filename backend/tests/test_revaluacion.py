"""HU-2.08: revaluación de los saldos en dólares al cierre del mes."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service
from tests.test_balance_mayor import VIN, _id, _linea
from tests.test_taller_ordenes import _token

URL = "/api/v1/contabilidad/revaluaciones"
BANCO, PROVEEDOR = "1.1.01.03", "2.1.01.01"


def _tipo_cambio(db, fecha: str, valor: str) -> None:
    db.execute(
        text(
            "INSERT INTO tipo_cambio (fecha, valor, origen) VALUES (:fecha, :valor, 'manual') "
            "ON CONFLICT (fecha) DO UPDATE SET valor = :valor"
        ),
        {"fecha": fecha, "valor": valor},
    )


@pytest.fixture(autouse=True)
def libro(sesion_contador):
    """El 05/02/2026, a 7.75: 100 USD en el banco contra 100 USD por pagar al proveedor (con VIN)."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        # TRUNCATE no dispara los triggers que protegen las partidas; arrastra las revaluaciones.
        db.execute(text("TRUNCATE partida RESTART IDENTITY CASCADE"))
        for fecha, valor in (("2026-02-05", "7.75"), ("2026-02-28", "7.80"), ("2026-03-31", "7.70")):
            _tipo_cambio(db, fecha, valor)
        lineas = [
            _linea(db, BANCO, "debe", "100", "USD"),
            _linea(db, PROVEEDOR, "haber", "100", "USD", vin=VIN),
        ]
        service.registrar_automatica(db, date(2026, 2, 5), "Saldo en dólares", lineas, "prueba", 1)
        db.commit()


def _revaluar(cliente, mes: int, politica: str = "mantener"):
    return cliente.post(URL, json={"anio": 2026, "mes": mes, "politica": politica})


def _saldos(hasta: date) -> tuple[Decimal, Decimal]:
    with SessionLocal() as db:
        return (
            service.saldo_cuenta(db, _id(db, BANCO), hasta),
            service.saldo_cuenta(db, _id(db, PROVEEDOR), hasta),
        )


def test_revalua_cada_cuenta_con_el_tipo_de_cambio_de_cierre(cliente_contador):
    respuesta = _revaluar(cliente_contador, 2)
    assert respuesta.status_code == 201, respuesta.text
    revaluacion = respuesta.json()
    assert (revaluacion["fecha"], revaluacion["tipo_cambio"]) == ("2026-02-28", "7.80000000")
    # Reporte: saldo en USD (signo normal de la cuenta), tipo de cambio anterior y diferencial.
    banco, proveedor = revaluacion["lineas"]
    assert (banco["saldo_usd"], banco["tipo_cambio_anterior"], banco["diferencial"]) == (
        "100.000000", "7.75000000", "5.000000",
    )  # fmt: skip
    assert (proveedor["saldo_usd"], proveedor["vin"], proveedor["diferencial"]) == (
        "100.000000", VIN, "-5.000000",
    )  # fmt: skip
    assert revaluacion["total_diferencial"] == "0.000000"

    # La partida sube el banco con ganancia y la deuda con pérdida, y queda ligada al mes.
    partida = cliente_contador.get("/api/v1/contabilidad/documentos/revaluacion/2026-02/partida").json()
    assert (partida["id"], partida["estado"], partida["fecha"]) == (
        revaluacion["partida_id"], "contabilizada", "2026-02-28",
    )  # fmt: skip
    assert partida["total_debe"] == partida["total_haber"] == "10.000000"
    assert all(linea["moneda"] == "GTQ" for linea in partida["lineas"])
    assert _saldos(date(2026, 2, 28)) == (Decimal("780"), Decimal("780"))
    with SessionLocal() as db:
        assert service.saldo_cuenta_usd(db, _id(db, BANCO)) == Decimal("100")
        assert service.saldo_cuenta(db, _id(db, PROVEEDOR), vin=VIN) == Decimal("780")


def test_politica_revertir_deshace_la_revaluacion_el_primer_dia_del_mes_siguiente(cliente_contador):
    revaluacion = _revaluar(cliente_contador, 2, "revertir").json()
    reversion = cliente_contador.get(f"/api/v1/contabilidad/partidas/{revaluacion['reversion_id']}").json()
    assert (reversion["fecha"], reversion["revierte_a"]) == ("2026-03-01", revaluacion["partida_id"])
    assert _saldos(date(2026, 2, 28)) == (Decimal("780"), Decimal("780"))
    assert _saldos(date(2026, 3, 1)) == (Decimal("775"), Decimal("775"))
    with SessionLocal() as db:
        # Revertida, el saldo sigue en libros al tipo de cambio del documento.
        assert service.tipo_cambio_en_libros(
            db, date(2026, 2, 5), Decimal("7.75"), date(2026, 3, 15)
        ) == Decimal("7.75")


def test_politica_mantener_deja_el_saldo_revaluado_como_base_del_mes_siguiente(cliente_contador):
    assert _revaluar(cliente_contador, 2).json()["reversion_id"] is None
    marzo = _revaluar(cliente_contador, 3).json()
    banco, proveedor = marzo["lineas"]
    # De 7.80 a 7.70: el banco pierde 10 y la deuda gana 10.
    assert (banco["tipo_cambio_anterior"], banco["diferencial"]) == ("7.80000000", "-10.000000")
    assert proveedor["diferencial"] == "10.000000"
    assert _saldos(date(2026, 3, 31)) == (Decimal("770"), Decimal("770"))
    with SessionLocal() as db:
        libros = service.tipo_cambio_en_libros
        assert libros(db, date(2026, 2, 5), Decimal("7.75"), date(2026, 3, 15)) == Decimal("7.80")
        assert libros(db, date(2026, 2, 5), Decimal("7.75"), date(2026, 4, 2)) == Decimal("7.70")
        # Un documento posterior a la revaluación conserva su propio tipo de cambio.
        assert libros(db, date(2026, 4, 1), Decimal("7.72"), date(2026, 4, 2)) == Decimal("7.72")


def test_rechazos(cliente_contador):
    hoy = date.today()
    abierto = cliente_contador.post(URL, json={"anio": hoy.year, "mes": hoy.month, "politica": "mantener"})
    assert abierto.status_code == 400 and "haber terminado" in abierto.json()["detail"]
    sin_tipo = _revaluar(cliente_contador, 4)
    assert sin_tipo.status_code == 409 and "30/04/2026" in sin_tipo.json()["detail"]
    assert _revaluar(cliente_contador, 2, "a veces").status_code == 422

    assert _revaluar(cliente_contador, 3).status_code == 201
    repetida = _revaluar(cliente_contador, 3)
    assert repetida.status_code == 409 and "Ya se revaluó marzo de 2026" in repetida.json()["detail"]
    anterior = _revaluar(cliente_contador, 2)
    assert anterior.status_code == 409 and "mes posterior" in anterior.json()["detail"]
    assert len(cliente_contador.get(URL).json()) == 1


def test_sin_saldos_en_dolares_no_hay_revaluacion(cliente_contador):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE partida RESTART IDENTITY CASCADE"))
        db.commit()
    respuesta = _revaluar(cliente_contador, 2)
    assert respuesta.status_code == 400 and "No hay saldos" in respuesta.json()["detail"]


def test_permisos():
    cuerpo = {"anio": 2026, "mes": 2, "politica": "mantener"}
    assert TestClient(app).post(URL, json=cuerpo).status_code == 401
    auxiliar = TestClient(app, headers=_token(TestClient(app), "auxiliar@empresa.gt"))
    assert auxiliar.post(URL, json=cuerpo).status_code == 403
    assert auxiliar.get(URL).status_code == 200
