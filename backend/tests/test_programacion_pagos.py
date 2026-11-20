"""HU-4.13: programar pagos a proveedores y aprobarlos, rechazarlos o modificarlos uno por uno."""

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
from app.modulos.contabilidad.schemas import LineaEntrada
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/compras/programaciones-pago"
URL_PENDIENTES = f"{API}/compras/cuentas-por-pagar"
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
    """Una unidad, un gasto en quetzales y otro en dólares por pagar, una cuenta bancaria por moneda
    (la de quetzales con Q 5,000.00 en libros) y el tipo de cambio de la fecha y de hoy."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(
            text(
                "TRUNCATE programacion_pago, pago_programado, proveedor, unidad, partida, cuenta_bancaria "
                "RESTART IDENTITY CASCADE"
            )
        )
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
        bancos = {
            moneda: configuracion.crear_cuenta_bancaria(
                db, "Banco Industrial", f"000-{moneda}", "monetaria", moneda,
                configuracion.buscar_cuenta(db, codigo).id,
            ).id
            for moneda, codigo in (("GTQ", "1.1.01.02"), ("USD", "1.1.01.03"))
        }  # fmt: skip
        contabilidad.registrar_automatica(
            db,
            fecha=date(2026, 11, 1),
            concepto="Aporte de capital",
            lineas=[
                LineaEntrada(
                    cuenta_id=configuracion.buscar_cuenta(db, "1.1.01.02").id, lado="debe", monto="5000"
                ),
                LineaEntrada(cuenta_id=configuracion.buscar_cuenta(db, "3.1").id, lado="haber", monto="5000"),
            ],
            documento_tipo="prueba_programacion",
            documento_id=1,
        )
        db.commit()
    c = cliente_contador
    for fecha in {FECHA, HOY}:
        assert (
            c.post(f"{API}/configuracion/tipos-cambio", json={"fecha": fecha, "valor": "7.75"}).status_code
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
    gasto = {"vin": VIN, "fecha": FECHA, "concepto": "flete"}
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


def _proponer(cliente: TestClient, *pagos: tuple[int, int, str], fecha: str = HOY):
    cuerpo = {
        "fecha": fecha,
        "descripcion": "Pagos de la semana",
        "pagos": [{"cuenta_por_pagar_id": c, "cuenta_bancaria_id": b, "monto": m} for c, b, m in pagos],
    }
    return cliente.post(URL, json=cuerpo)


def _decidir(cliente: TestClient, programacion: dict, indice: int, **cuerpo):
    pago_id = programacion["pagos"][indice]["id"]
    return cliente.post(f"{URL}/{programacion['id']}/pagos/{pago_id}/decision", json=cuerpo)


def test_lista_las_cuentas_por_pagar_vencidas_o_por_vencer(auxiliar, datos):
    respuesta = auxiliar.get(URL_PENDIENTES)
    assert respuesta.status_code == 200
    por_id = {c["id"]: c for c in respuesta.json()}
    gtq, usd = por_id[datos["cxp_gtq"]], por_id[datos["cxp_usd"]]
    assert gtq["origen"] == "gasto_importacion"
    assert gtq["proveedor"] == "Agencia Aduanal del Pacífico"
    assert gtq["vin"] == VIN
    assert gtq["fecha_vencimiento"] == FECHA  # sin días de crédito
    assert gtq["dias_vencida"] == (date.today() - date(2026, 11, 10)).days
    assert gtq["saldo"] == "3500.000000" and gtq["programado"] == "0.000000"
    assert usd["moneda"] == "USD" and usd["fecha_vencimiento"] == "2026-11-25"

    solo_usd = auxiliar.get(URL_PENDIENTES, params={"moneda": "USD"}).json()
    assert [c["id"] for c in solo_usd] == [datos["cxp_usd"]]
    vencidas = auxiliar.get(URL_PENDIENTES, params={"vence_hasta": "2026-11-15"}).json()
    assert [c["id"] for c in vencidas] == [datos["cxp_gtq"]]


def test_la_propuesta_muestra_totales_y_saldo_disponible_por_banco(auxiliar, datos):
    respuesta = _proponer(
        auxiliar,
        (datos["cxp_gtq"], datos["banco_gtq"], "2000.00"),  # parcial
        (datos["cxp_usd"], datos["banco_usd"], "1000.00"),
    )
    assert respuesta.status_code == 201, respuesta.text
    programacion = respuesta.json()
    assert programacion["estado"] == "pendiente"
    assert [p["estado"] for p in programacion["pagos"]] == ["propuesto", "propuesto"]
    assert programacion["totales"] == {"GTQ": "2000.000000", "USD": "1000.000000"}
    bancos = {b["moneda"]: b for b in programacion["bancos"]}
    assert bancos["GTQ"]["saldo_libros"] == "5000.000000"
    assert bancos["GTQ"]["disponible"] == "5000.000000"
    assert bancos["GTQ"]["programado"] == "2000.000000"
    assert bancos["GTQ"]["alcanza"] is True
    assert bancos["USD"]["saldo_libros"] == "0.000000"
    assert bancos["USD"]["alcanza"] is False

    pendientes = {c["id"]: c for c in auxiliar.get(URL_PENDIENTES).json()}
    assert pendientes[datos["cxp_gtq"]]["programado"] == "2000.000000"


def test_un_documento_en_dolares_se_puede_programar_desde_un_banco_en_quetzales(auxiliar, datos):
    respuesta = _proponer(auxiliar, (datos["cxp_usd"], datos["banco_gtq"], "400.00"))
    assert respuesta.status_code == 201
    programacion = respuesta.json()
    [pago] = programacion["pagos"]
    assert pago["moneda"] == "USD" and pago["moneda_banco"] == "GTQ"
    assert pago["monto_banco"] == "3100.000000"  # estimado: 400 × 7.75
    assert programacion["tipo_cambio_estimado"] == "7.75000000"
    assert programacion["totales"] == {"GTQ": "3100.000000", "USD": "0.000000"}


@pytest.mark.parametrize(
    ("monto", "mensaje"),
    [("3500.01", "excede el saldo"), ("0", "mayor que cero"), ("abc", "no es un número válido")],
)
def test_el_monto_propuesto_es_positivo_y_no_excede_el_saldo(auxiliar, datos, monto, mensaje):
    respuesta = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], monto))
    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_una_cuenta_por_pagar_no_se_programa_dos_veces(auxiliar, datos):
    repetida = _proponer(
        auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "100"), (datos["cxp_gtq"], datos["banco_gtq"], "100")
    )
    assert repetida.status_code == 400
    assert _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "100")).status_code == 201
    otra = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "100"))
    assert otra.status_code == 409
    assert "ya está en otra programación" in otra.json()["detail"]


def test_no_se_programa_con_fecha_pasada_ni_sin_pagos_ni_con_un_banco_inactivo(auxiliar, datos):
    ayer = (date.today() - timedelta(days=1)).isoformat()
    assert _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "1"), fecha=ayer).status_code == 400
    assert _proponer(auxiliar).status_code == 400
    with SessionLocal() as db:
        configuracion.cambiar_estado_cuenta_bancaria(db, datos["banco_gtq"], False)
    inactiva = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "1"))
    assert inactiva.status_code == 400
    assert "inactiva" in inactiva.json()["detail"]


def test_el_gerente_aprueba_modifica_o_rechaza_cada_pago(auxiliar, gerente, datos):
    programacion = _proponer(
        auxiliar,
        (datos["cxp_gtq"], datos["banco_gtq"], "3500.00"),
        (datos["cxp_usd"], datos["banco_usd"], "1000.00"),
    ).json()

    sin_motivo = _decidir(gerente, programacion, 1, accion="rechazar")
    assert sin_motivo.status_code == 400
    modificado = _decidir(
        gerente, programacion, 0, accion="aprobar", monto="1500.00", comentario="El resto el mes próximo"
    )
    assert modificado.status_code == 200, modificado.text
    pago = modificado.json()["pagos"][0]
    assert pago["estado"] == "aprobado"
    assert pago["monto_propuesto"] == "3500.000000" and pago["monto"] == "1500.000000"
    assert pago["decidido_por"] is not None and pago["comentario"] == "El resto el mes próximo"
    assert modificado.json()["estado"] == "pendiente"

    rechazado = _decidir(gerente, programacion, 1, accion="rechazar", comentario="Falta el BL original")
    assert rechazado.status_code == 200
    revisada = rechazado.json()
    assert revisada["estado"] == "revisada"
    assert revisada["pagos"][1]["estado"] == "rechazado"
    assert revisada["totales"] == {"GTQ": "1500.000000", "USD": "0.000000"}  # sin los rechazados

    # Un pago ya decidido no se vuelve a decidir; la cuenta del rechazado se puede volver a programar.
    assert _decidir(gerente, programacion, 0, accion="rechazar", comentario="x").status_code == 409
    assert _proponer(auxiliar, (datos["cxp_usd"], datos["banco_usd"], "1000.00")).status_code == 201


def test_el_gerente_puede_cambiar_la_cuenta_bancaria_al_aprobar(auxiliar, gerente, datos):
    programacion = _proponer(auxiliar, (datos["cxp_usd"], datos["banco_usd"], "400.00")).json()
    respuesta = _decidir(gerente, programacion, 0, accion="aprobar", cuenta_bancaria_id=datos["banco_gtq"])
    assert respuesta.status_code == 200
    pago = respuesta.json()["pagos"][0]
    assert pago["cuenta_bancaria_id"] == datos["banco_gtq"] and pago["monto_banco"] == "3100.000000"
    excede = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "10.00")).json()
    assert _decidir(gerente, excede, 0, accion="aprobar", monto="3500.01").status_code == 400


def test_quien_propone_no_puede_aprobar(gerente, datos):
    programacion = _proponer(gerente, (datos["cxp_gtq"], datos["banco_gtq"], "100.00"))
    assert programacion.status_code == 201
    respuesta = _decidir(gerente, programacion.json(), 0, accion="aprobar")
    assert respuesta.status_code == 403
    assert "propusiste tú" in respuesta.json()["detail"]


def test_solo_el_gerente_financiero_aprueba(auxiliar, cliente_contador, datos):
    programacion = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "100.00")).json()
    assert _decidir(auxiliar, programacion, 0, accion="aprobar").status_code == 403
    assert _decidir(cliente_contador, programacion, 0, accion="aprobar").status_code == 403
    gerencia = _sesion("gerencia@empresa.gt")
    assert _proponer(gerencia, (datos["cxp_usd"], datos["banco_usd"], "1.00")).status_code == 403


def test_lo_aprobado_en_otra_programacion_compromete_el_saldo_del_banco(auxiliar, gerente, datos):
    primera = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "3500.00")).json()
    assert _decidir(gerente, primera, 0, accion="aprobar").status_code == 200
    segunda = _proponer(auxiliar, (datos["cxp_usd"], datos["banco_gtq"], "400.00")).json()
    [banco] = segunda["bancos"]
    assert banco["comprometido"] == "3500.000000"
    assert banco["disponible"] == "1500.000000"
    assert banco["programado"] == "3100.000000"
    assert banco["alcanza"] is False

    listado = auxiliar.get(URL).json()
    assert [p["id"] for p in listado] == [segunda["id"], primera["id"]]
    assert auxiliar.get(f"{URL}/{primera['id']}").json()["estado"] == "revisada"
    assert auxiliar.get(f"{URL}/999").status_code == 404


def test_la_programacion_y_sus_pagos_quedan_en_la_bitacora(auxiliar, gerente, datos):
    with SessionLocal() as db:  # la bitácora no se vacía: solo cuenta lo de esta prueba
        desde = db.scalar(select(func.coalesce(func.max(RegistroBitacora.id), 0)))
    programacion = _proponer(auxiliar, (datos["cxp_gtq"], datos["banco_gtq"], "100.00")).json()
    _decidir(gerente, programacion, 0, accion="aprobar")
    pago_id = str(programacion["pagos"][0]["id"])
    with SessionLocal() as db:
        alta = db.scalar(
            select(RegistroBitacora).where(
                RegistroBitacora.id > desde,
                RegistroBitacora.entidad == "programacion_pago",
                RegistroBitacora.registro_id == str(programacion["id"]),
            )
        )
        cambios = list(
            db.scalars(
                select(RegistroBitacora)
                .where(
                    RegistroBitacora.id > desde,
                    RegistroBitacora.entidad == "pago_programado",
                    RegistroBitacora.registro_id == pago_id,
                )
                .order_by(RegistroBitacora.id)
            )
        )
    assert alta.usuario_id == programacion["propuesta_por"]
    assert [c.accion for c in cambios] == ["crear", "modificar"]
    assert cambios[1].nuevos["estado"] == "aprobado"
    assert cambios[1].usuario_id == cambios[1].nuevos["decidido_por"]
    assert Decimal(str(cambios[0].nuevos["monto"])) == Decimal("100")
