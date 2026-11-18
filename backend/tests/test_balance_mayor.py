"""HU-2.16: balance de comprobación y mayor sobre partidas contabilizadas."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.modulos.configuracion.models import Cuenta
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service
from app.modulos.contabilidad.schemas import LineaEntrada, PartidaEntrada
from app.modulos.seguridad.semilla import CUENTAS, crear_cuentas_iniciales

CLAVE = "Prueba-2026!"
AUXILIAR, GERENCIA = CUENTAS[0][0], CUENTAS[3][0]
VIN = "1HGCM82633A004352"
URL = "/api/v1/contabilidad"


def _id(db, codigo: str) -> int:
    return db.query(Cuenta).filter_by(codigo=codigo).one().id


def _linea(db, codigo, lado, monto, moneda="GTQ", **extra) -> LineaEntrada:
    return LineaEntrada(cuenta_id=_id(db, codigo), lado=lado, monto=monto, moneda=moneda, **extra)


@pytest.fixture(autouse=True)
def libro():
    """Tres partidas contabilizadas (enero y febrero) y un borrador que no debe contar."""
    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE)
        crear_catalogo_inicial(db)
        # TRUNCATE no dispara los triggers que protegen las partidas: cada prueba empieza sin ellas.
        db.execute(text("TRUNCATE partida RESTART IDENTITY CASCADE"))
        db.execute(
            text(
                "INSERT INTO tipo_cambio (fecha, valor, origen) VALUES ('2026-02-05', 7.75, 'manual') "
                "ON CONFLICT (fecha) DO UPDATE SET valor = 7.75"
            )
        )
        for numero, (fecha, lineas) in enumerate(
            [
                (
                    date(2026, 1, 10),
                    [_linea(db, "1.1.01.01", "debe", "1000"), _linea(db, "1.1.01.02", "haber", "1000")],
                ),
                (
                    date(2026, 2, 5),
                    [
                        _linea(db, "1.1.01.03", "debe", "100", "USD"),
                        _linea(db, "2.1.01.01", "haber", "100", "USD", vin=VIN),
                    ],
                ),
                (
                    date(2026, 2, 20),
                    [_linea(db, "1.1.01.02", "debe", "300"), _linea(db, "1.1.01.01", "haber", "300")],
                ),
            ],
            start=1,
        ):
            service.registrar_automatica(db, fecha, f"Movimiento {numero}", lineas, "prueba", numero)
        db.commit()
        service.crear_borrador(
            db,
            PartidaEntrada(
                fecha=date(2026, 2, 21),
                concepto="Borrador",
                lineas=[_linea(db, "1.1.01.01", "debe", "999"), _linea(db, "1.1.01.02", "haber", "999")],
            ),
        )
    yield


def test_el_balance_da_saldos_por_naturaleza_y_totales_del_rango():
    with SessionLocal() as db:
        balance = service.balance_comprobacion(db, date(2026, 2, 1), date(2026, 2, 28))
    filas = {
        f["codigo"]: (f["saldo_inicial"], f["debe"], f["haber"], f["saldo_final"]) for f in balance["filas"]
    }
    assert filas == {
        "1.1.01.01": (1000, 0, 300, 700),
        "1.1.01.02": (-1000, 300, 0, -700),
        "1.1.01.03": (0, 775, 0, 775),
        "2.1.01.01": (0, 0, 775, 775),  # acreedora: saldo positivo en el haber
    }
    assert balance["total_debe"] == balance["total_haber"] == Decimal("1075")


def test_el_balance_filtra_por_vin_y_por_linea_de_negocio():
    with SessionLocal() as db:
        por_vin = service.balance_comprobacion(db, vin=VIN.lower())
        por_linea = service.balance_comprobacion(db, linea_negocio="venta")
    assert [f["codigo"] for f in por_vin["filas"]] == ["2.1.01.01"]
    assert por_linea["filas"] == [] and por_linea["total_debe"] == 0


def test_el_mayor_lleva_saldo_inicial_acumulado_y_original_en_usd():
    with SessionLocal() as db:
        caja = service.mayor(db, _id(db, "1.1.01.01"), desde=date(2026, 2, 1))
        dolares = service.mayor(db, _id(db, "1.1.01.03"))
    assert caja["saldo_inicial"] == 1000 and caja["saldo_final"] == 700
    (movimiento,) = caja["movimientos"]
    assert (movimiento["haber"], movimiento["saldo"], movimiento["documento_tipo"]) == (300, 700, "prueba")
    (usd,) = dolares["movimientos"]
    assert (usd["monto_usd"], usd["tipo_cambio"], usd["debe"]) == (100, Decimal("7.75"), 775)


def test_saldo_cuenta_para_conciliar_por_vin_y_fecha():
    with SessionLocal() as db:
        proveedores = _id(db, "2.1.01.01")
        assert service.saldo_cuenta(db, proveedores, vin=VIN) == Decimal("775")
        assert service.saldo_cuenta(db, proveedores, hasta=date(2026, 1, 31)) == 0
        assert service.saldo_cuenta(db, _id(db, "1.1.01.01")) == Decimal("700")  # sin el borrador


def _entrar(cliente, correo):
    token = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_la_api_exige_rol_de_consulta_y_envia_montos_como_texto(cliente):
    assert cliente.get(f"{URL}/balance").status_code == 401
    assert cliente.get(f"{URL}/balance", headers=_entrar(cliente, AUXILIAR)).status_code == 403
    gerencia = _entrar(cliente, GERENCIA)
    balance = cliente.get(f"{URL}/balance", params={"hasta": "2026-02-28"}, headers=gerencia).json()
    assert balance["total_debe"] == "2075.000000"
    with SessionLocal() as db:
        cuenta = _id(db, "1.1.01.03")
    mayor = cliente.get(f"{URL}/mayor/{cuenta}", headers=gerencia).json()
    assert mayor["movimientos"][0]["tipo_cambio"] == "7.75000000"
    assert mayor["saldo_final"] == "775.000000"
    assert cliente.get(f"{URL}/mayor/999999", headers=gerencia).status_code == 404
