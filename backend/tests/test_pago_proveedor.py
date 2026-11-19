"""HU-4.14: registrar el pago aprobado a un proveedor, en su moneda o en otra, y anularlo."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion import service as configuracion
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service as contabilidad
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/compras/pagos"
VIN = "1HGCM82633A004352"
FECHA = "2026-11-10"
HOY = date.today().isoformat()

NAVIERA = {
    "tipo": "exterior",
    "nombre": "Seaboard Marine Ltd.",
    "identificacion_fiscal": "59-1182372",
    "pais": "US",
    "rubro": "naviera",
    "moneda_habitual": "USD",
    "dias_credito": 15,
}
AGENTE = {
    "tipo": "local",
    "nombre": "Agencia Aduanal del Pacífico",
    "nit": "1669394-9",
    "regimen": "general",
    "rubro": "agente_aduanal",
    "moneda_habitual": "GTQ",
    "dias_credito": 0,
}


def _sesion(correo: str) -> TestClient:
    respuesta = TestClient(app).post(
        f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}
    )
    return TestClient(app, headers={"Authorization": f"Bearer {respuesta.json()['token']}"})


@pytest.fixture(scope="module")
def auxiliar(sesion_contador) -> TestClient:  # `sesion_contador` crea las cuentas iniciales
    return _sesion("auxiliar@empresa.gt")


@pytest.fixture(scope="module")
def gerente(sesion_contador) -> TestClient:
    return _sesion("gerente.financiero@empresa.gt")


@pytest.fixture(autouse=True)
def datos(cliente_contador) -> dict[str, int]:
    """Un gasto de Q 3,500.00 al agente aduanal y otro de US$ 1,000.00 a la naviera (tipo de cambio
    7.75 en su fecha), una cuenta bancaria por moneda y el tipo de cambio de hoy, 7.80."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(
            text(
                "TRUNCATE aplicacion_pago, pago_proveedor, programacion_pago, pago_programado, proveedor, "
                "unidad, partida, cuenta_bancaria RESTART IDENTITY CASCADE"
            )
        )
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
        bancos = {
            moneda: configuracion.crear_cuenta_bancaria(
                db, "Banco Industrial", f"000-{moneda}", "monetaria", moneda,
                configuracion.buscar_cuenta(db, codigo).id, siguiente_cheque=101,
            ).id
            for moneda, codigo in (("GTQ", "1.1.01.02"), ("USD", "1.1.01.03"))
        }  # fmt: skip
    c = cliente_contador
    assert (
        c.post(f"{API}/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": "7.75"}).status_code == 201
    )
    if HOY != FECHA:
        assert (
            c.post(f"{API}/configuracion/tipos-cambio", json={"fecha": HOY, "valor": "7.80"}).status_code
            == 201
        )
    unidad = {
        "vin": VIN,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
    }
    assert c.post(f"{API}/unidades", json=unidad).status_code == 201
    naviera = c.post(f"{API}/compras/proveedores", json=NAVIERA).json()["id"]
    agente = c.post(f"{API}/compras/proveedores", json=AGENTE).json()["id"]
    gasto = {"vin": VIN, "fecha": FECHA}
    gtq = c.post(
        f"{API}/compras/gastos-importacion",
        json={
            **gasto,
            "concepto": "agente_aduanal",
            "proveedor_id": agente,
            "documento": "F-1",
            "moneda": "GTQ",
            "monto": "3500.00",
        },
    )
    usd = c.post(
        f"{API}/compras/gastos-importacion",
        json={
            **gasto,
            "concepto": "flete",
            "proveedor_id": naviera,
            "documento": "BL-778812",
            "moneda": "USD",
            "monto": "1000.00",
        },
    )
    assert gtq.status_code == 201 and usd.status_code == 201
    return {
        "banco_gtq": bancos["GTQ"],
        "banco_usd": bancos["USD"],
        "cxp_gtq": gtq.json()["cuenta_por_pagar"]["id"],
        "cxp_usd": usd.json()["cuenta_por_pagar"]["id"],
    }


def _programar(auxiliar, gerente, *pagos: tuple[int, int, str], aprobar: bool = True) -> list[int]:
    cuerpo = {
        "fecha": HOY,
        "pagos": [{"cuenta_por_pagar_id": c, "cuenta_bancaria_id": b, "monto": m} for c, b, m in pagos],
    }
    programacion = auxiliar.post(f"{API}/compras/programaciones-pago", json=cuerpo)
    assert programacion.status_code == 201, programacion.text
    ids = [p["id"] for p in programacion.json()["pagos"]]
    if aprobar:
        for pago_id in ids:
            url = f"{API}/compras/programaciones-pago/{programacion.json()['id']}/pagos/{pago_id}/decision"
            assert gerente.post(url, json={"accion": "aprobar"}).status_code == 200
    return ids


def _pagar(cliente, banco: int, programados: list[int], **cambios):
    cuerpo = {
        "cuenta_bancaria_id": banco,
        "forma_pago": "cheque",
        "referencia": "101",
        "fecha": HOY,
        "pagos_programados": programados,
        **cambios,
    }
    return cliente.post(URL, json=cuerpo)


def _saldo(cliente, cuenta_id: int) -> str:
    cuentas = cliente.get(f"{API}/compras/cuentas-por-pagar").json()
    return next((c["saldo"] for c in cuentas if c["id"] == cuenta_id), "0")


def _lineas_partida(pago_id: int) -> list[tuple[str, Decimal, Decimal, str | None, Decimal | None]]:
    """(código, debe, haber, moneda si USD, monto en USD) de cada línea de la partida del pago."""
    with SessionLocal() as db:
        partida = contabilidad.partida_de_documento(db, "pago_proveedor", pago_id)
        codigos = {c.id: c.codigo for c in configuracion.listar_cuentas(db)}
        return [
            (codigos[linea.cuenta_id], linea.debe, linea.haber, linea.moneda, linea.monto_usd)
            for linea in partida.lineas
        ]


def _cuadra(lineas) -> bool:
    return sum(linea[1] for linea in lineas) == sum(linea[2] for linea in lineas)


def test_pago_en_quetzales_por_cheque_cancela_el_documento(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_gtq"], "3500.00"))
    assert auxiliar.get(f"{API}/compras/pagos-por-ejecutar").json()[0]["id"] == programados[0]

    respuesta = _pagar(auxiliar, datos["banco_gtq"], programados)
    assert respuesta.status_code == 201, respuesta.text
    pago = respuesta.json()
    assert pago["estado"] == "registrado"
    assert pago["forma_pago"] == "cheque" and pago["referencia"] == "101"
    assert pago["moneda"] == "GTQ" and pago["monto"] == "3500.000000"
    assert pago["tipo_cambio"] is None and pago["diferencial"] == "0.000000"
    assert pago["partida_numero"] is not None and pago["reversion_numero"] is None
    [aplicacion] = pago["aplicaciones"]
    assert aplicacion["documento"] == "Agente aduanal F-1"
    assert aplicacion["saldo_documento"] == "0.000000"
    assert _saldo(auxiliar, datos["cxp_gtq"]) == "0"  # ya no está pendiente

    lineas = _lineas_partida(pago["id"])
    assert [(c, d, h) for c, d, h, *_ in lineas] == [
        ("2.1.01.02", Decimal("3500"), Decimal("0")),
        ("1.1.01.02", Decimal("0"), Decimal("3500")),
    ]
    assert auxiliar.get(f"{API}/compras/pagos-por-ejecutar").json() == []
    programacion = auxiliar.get(f"{API}/compras/programaciones-pago").json()[0]
    assert programacion["pagos"][0]["estado"] == "ejecutado"


def test_pago_parcial_deja_el_saldo_restante(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_gtq"], "1500.00"))
    respuesta = _pagar(
        auxiliar, datos["banco_gtq"], programados, forma_pago="transferencia", referencia="TRF-88"
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["aplicaciones"][0]["saldo_documento"] == "2000.000000"
    assert _saldo(auxiliar, datos["cxp_gtq"]) == "2000.000000"


def test_documento_en_dolares_pagado_en_dolares_registra_el_diferencial(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_usd"], datos["banco_usd"], "1000.00"))
    respuesta = _pagar(
        auxiliar, datos["banco_usd"], programados, forma_pago="transferencia", referencia="SWIFT-1"
    )
    assert respuesta.status_code == 201, respuesta.text
    pago = respuesta.json()
    assert pago["moneda"] == "USD" and pago["monto"] == "1000.000000"
    assert pago["tipo_cambio"] == "7.80000000"
    # US$ 1,000 en libros a 7.75 (Q 7,750) salen del banco a 7.80 (Q 7,800): pérdida de Q 50.
    assert pago["diferencial"] == "-50.000000"
    assert pago["aplicaciones"][0]["tipo_cambio_libros"] == "7.75000000"
    lineas = _lineas_partida(pago["id"])
    assert lineas == [
        ("2.1.01.01", Decimal("7750"), Decimal("0"), "USD", Decimal("1000")),
        ("6.3", Decimal("50"), Decimal("0"), "GTQ", None),
        ("1.1.01.03", Decimal("0"), Decimal("7800"), "USD", Decimal("1000")),
    ]


def test_documento_en_dolares_pagado_desde_un_banco_en_quetzales(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_usd"], datos["banco_gtq"], "400.00"))
    respuesta = _pagar(auxiliar, datos["banco_gtq"], programados)
    assert respuesta.status_code == 201, respuesta.text
    pago = respuesta.json()
    assert pago["moneda"] == "GTQ" and pago["monto"] == "3120.000000"  # 400 × 7.80
    assert pago["diferencial"] == "-20.000000"  # 400 × (7.80 − 7.75)
    assert pago["aplicaciones"][0]["saldo_documento"] == "600.000000"  # sigue en dólares
    lineas = _lineas_partida(pago["id"])
    assert _cuadra(lineas)
    assert lineas[-1][:3] == ("1.1.01.02", Decimal("0"), Decimal("3120"))


def test_documento_en_quetzales_pagado_desde_un_banco_en_dolares(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_usd"], "3500.00"))
    respuesta = _pagar(auxiliar, datos["banco_usd"], programados)
    assert respuesta.status_code == 201, respuesta.text
    pago = respuesta.json()
    assert pago["moneda"] == "USD" and pago["monto"] == "448.717949"  # 3500 / 7.80
    # El redondeo a 6 decimales deja fracciones de centavo; van al diferencial para que cuadre.
    assert abs(Decimal(pago["diferencial"])) < Decimal("0.0001")
    lineas = _lineas_partida(pago["id"])
    assert _cuadra(lineas)
    assert lineas[0][:3] == ("2.1.01.02", Decimal("3500"), Decimal("0"))
    assert _saldo(auxiliar, datos["cxp_gtq"]) == "0"


def test_un_pago_cancela_varios_documentos_del_mismo_proveedor_y_banco(
    auxiliar, gerente, cliente_contador, datos
):
    otro = cliente_contador.post(
        f"{API}/compras/gastos-importacion",
        json={
            "vin": VIN, "fecha": FECHA, "concepto": "almacenaje", "proveedor_id": 2, "documento": "F-2",
            "moneda": "GTQ", "monto": "500.00",
        },
    )  # fmt: skip
    assert otro.status_code == 201
    programados = _programar(
        auxiliar,
        gerente,
        (datos["cxp_gtq"], datos["banco_gtq"], "3500.00"),
        (otro.json()["cuenta_por_pagar"]["id"], datos["banco_gtq"], "500.00"),
    )
    respuesta = _pagar(auxiliar, datos["banco_gtq"], programados)
    assert respuesta.status_code == 201
    assert respuesta.json()["monto"] == "4000.000000"
    assert len(respuesta.json()["aplicaciones"]) == 2


def test_solo_se_ejecuta_un_pago_aprobado(auxiliar, gerente, datos):
    propuesto = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_gtq"], "100.00"), aprobar=False)
    respuesta = _pagar(auxiliar, datos["banco_gtq"], propuesto)
    assert respuesta.status_code == 409
    assert "solo se ejecuta un pago aprobado" in respuesta.json()["detail"]

    aprobado = _programar(auxiliar, gerente, (datos["cxp_usd"], datos["banco_usd"], "100.00"))
    assert _pagar(auxiliar, datos["banco_usd"], aprobado).status_code == 201
    otra_vez = _pagar(auxiliar, datos["banco_usd"], aprobado, referencia="102")
    assert otra_vez.status_code == 409
    assert "está ejecutado" in otra_vez.json()["detail"]
    assert _pagar(auxiliar, datos["banco_usd"], [999]).status_code == 404


def test_valida_banco_proveedor_referencia_fecha_y_tipo_de_cambio(auxiliar, gerente, datos):
    programados = _programar(
        auxiliar,
        gerente,
        (datos["cxp_gtq"], datos["banco_gtq"], "100.00"),
        (datos["cxp_usd"], datos["banco_gtq"], "100.00"),
    )
    otro_banco = _pagar(auxiliar, datos["banco_usd"], programados[:1])
    assert otro_banco.status_code == 400 and "otra cuenta bancaria" in otro_banco.json()["detail"]
    dos_proveedores = _pagar(auxiliar, datos["banco_gtq"], programados)
    assert dos_proveedores.status_code == 400 and "un solo proveedor" in dos_proveedores.json()["detail"]
    sin_cheque = _pagar(auxiliar, datos["banco_gtq"], programados[:1], referencia="  ")
    assert sin_cheque.status_code == 400 and "número de cheque" in sin_cheque.json()["detail"]
    manana = (date.today() + timedelta(days=1)).isoformat()
    assert _pagar(auxiliar, datos["banco_gtq"], programados[:1], fecha=manana).status_code == 400
    sin_tipo = _pagar(auxiliar, datos["banco_gtq"], programados[1:], fecha="2026-11-11")
    assert sin_tipo.status_code == 409 and "tipo de cambio" in sin_tipo.json()["detail"]
    assert _saldo(auxiliar, datos["cxp_usd"]) == "1000.000000"  # nada quedó a medias


def test_un_cheque_no_se_repite_en_la_misma_cuenta(auxiliar, gerente, cliente_contador, datos):
    programados = _programar(
        auxiliar,
        gerente,
        (datos["cxp_gtq"], datos["banco_gtq"], "100.00"),
        (datos["cxp_usd"], datos["banco_gtq"], "100.00"),
    )
    primero = _pagar(auxiliar, datos["banco_gtq"], programados[:1])
    assert primero.status_code == 201
    repetido = _pagar(auxiliar, datos["banco_gtq"], programados[1:])
    assert repetido.status_code == 409
    assert "cheque 101" in repetido.json()["detail"]
    anulado = cliente_contador.post(
        f"{URL}/{primero.json()['id']}/anulacion", json={"fecha": HOY, "motivo": "Cheque dañado"}
    )
    assert anulado.status_code == 200
    assert _pagar(auxiliar, datos["banco_gtq"], programados[1:]).status_code == 201


def test_anular_reabre_los_documentos_y_revierte_la_partida(auxiliar, gerente, cliente_contador, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_usd"], datos["banco_usd"], "1000.00"))
    pago = _pagar(auxiliar, datos["banco_usd"], programados).json()
    with SessionLocal() as db:
        banco = configuracion.buscar_cuenta(db, "1.1.01.03").id
        assert contabilidad.saldo_cuenta_usd(db, banco) == Decimal("-1000")

    assert (
        auxiliar.post(f"{URL}/{pago['id']}/anulacion", json={"fecha": HOY, "motivo": "x"}).status_code == 403
    )
    sin_motivo = cliente_contador.post(f"{URL}/{pago['id']}/anulacion", json={"fecha": HOY, "motivo": " "})
    assert sin_motivo.status_code == 400
    antes = cliente_contador.post(
        f"{URL}/{pago['id']}/anulacion", json={"fecha": "2026-11-01", "motivo": "x"}
    )
    assert antes.status_code == 400  # anterior al pago

    respuesta = cliente_contador.post(
        f"{URL}/{pago['id']}/anulacion", json={"fecha": HOY, "motivo": "Transferencia rechazada por el banco"}
    )
    assert respuesta.status_code == 200, respuesta.text
    anulado = respuesta.json()
    assert anulado["estado"] == "anulado"
    assert anulado["motivo_anulacion"] == "Transferencia rechazada por el banco"
    assert anulado["anulado_por"] is not None and anulado["fecha_anulacion"] == HOY
    assert anulado["reversion_numero"] is not None
    assert anulado["aplicaciones"][0]["saldo_documento"] == "1000.000000"
    assert _saldo(auxiliar, datos["cxp_usd"]) == "1000.000000"
    with SessionLocal() as db:
        assert contabilidad.saldo_cuenta_usd(db, banco) == Decimal("0")
        perdida = configuracion.buscar_cuenta(db, "6.3").id
        assert contabilidad.saldo_cuenta(db, perdida) == Decimal("0")

    programacion = auxiliar.get(f"{API}/compras/programaciones-pago").json()[0]
    assert programacion["pagos"][0]["estado"] == "anulado"
    # El documento reabierto se vuelve a programar y aprobar antes de pagarlo otra vez.
    assert _pagar(auxiliar, datos["banco_usd"], programados, referencia="SWIFT-2").status_code == 409
    nuevos = _programar(auxiliar, gerente, (datos["cxp_usd"], datos["banco_usd"], "1000.00"))
    assert _pagar(auxiliar, datos["banco_usd"], nuevos, referencia="SWIFT-2").status_code == 201
    otra_vez = cliente_contador.post(f"{URL}/{pago['id']}/anulacion", json={"fecha": HOY, "motivo": "x"})
    assert otra_vez.status_code == 409


def test_se_consultan_los_pagos(auxiliar, gerente, datos):
    programados = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_gtq"], "100.00"))
    pago = _pagar(auxiliar, datos["banco_gtq"], programados).json()
    assert [p["id"] for p in auxiliar.get(URL).json()] == [pago["id"]]
    assert auxiliar.get(URL, params={"proveedor_id": pago["proveedor_id"] + 99}).json() == []
    assert auxiliar.get(f"{URL}/{pago['id']}").json()["proveedor"] == "Agencia Aduanal del Pacífico"
    assert auxiliar.get(f"{URL}/999").status_code == 404
    assert _sesion("gerencia@empresa.gt").post(URL, json={}).status_code == 403


def test_el_pago_y_sus_aplicaciones_quedan_en_la_bitacora(auxiliar, gerente, datos):
    with SessionLocal() as db:  # la bitácora no se vacía: solo cuenta lo de esta prueba
        desde = db.scalar(select(func.coalesce(func.max(RegistroBitacora.id), 0)))
    programados = _programar(auxiliar, gerente, (datos["cxp_gtq"], datos["banco_gtq"], "100.00"))
    pago = _pagar(auxiliar, datos["banco_gtq"], programados).json()
    with SessionLocal() as db:
        registros = list(
            db.scalars(
                select(RegistroBitacora).where(
                    RegistroBitacora.id > desde,
                    RegistroBitacora.entidad.in_(("pago_proveedor", "aplicacion_pago", "pago_programado")),
                )
            )
        )
    alta = next(r for r in registros if r.entidad == "pago_proveedor")
    assert alta.registro_id == str(pago["id"]) and alta.usuario_id == pago["usuario_id"]
    assert alta.nuevos["referencia"] == "101"
    assert any(r.entidad == "aplicacion_pago" for r in registros)
    ejecutado = [r for r in registros if r.entidad == "pago_programado" and r.nuevos["estado"] == "ejecutado"]
    assert ejecutado[0].nuevos["pago_id"] == pago["id"]
