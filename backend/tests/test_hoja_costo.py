"""HU-4.08 (versión delgada): hoja de costo de una unidad y su cuadre con el mayor.

`ciclo_completo` deja una unidad en "lista" con compra en USD, gastos de importación en GTQ y USD
(con IVA de importación), una orden de taller cerrada y una línea de factura local para la unidad;
la reutilizan las pruebas del alta en flota (HU-3.01) y de los reportes.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.compras import service as compras
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada

API = "/api/v1"
URL = f"{API}/compras/hoja-costo"
VIN = "1HGCM82633A004352"
OTRO_VIN = "JHMCM56557C404453"
FECHA = "2026-10-20"
# Compra 9075.00 USD × 7.75 = 70331.25; gastos que suman 3500 + 933.10 + 1200; IVA de importación
# 5000 aparte; mano de obra 112.50; factura de pequeño contribuyente 1000 + 120 de IVA.
TOTAL = Decimal("77196.85")


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


@pytest.fixture(autouse=True)
def base_limpia(cliente):
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("TRUNCATE proveedor, unidad, partida, tarifa_mano_obra RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.execute(
            text("INSERT INTO tarifa_mano_obra (tarifa_hora, vigente_desde) VALUES (45, '2026-11-01')")
        )
        db.commit()
    assert (
        cliente.post(f"{API}/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": "7.75"}).status_code
        == 201
    )


def _proveedor(cliente, **datos) -> int:
    """El proveedor con ese nombre, o lo crea: varias unidades comparten los mismos proveedores."""
    existentes = cliente.get(f"{API}/compras/proveedores", params={"buscar": datos["nombre"]}).json()
    if existentes:
        return existentes[0]["id"]
    respuesta = cliente.post(f"{API}/compras/proveedores", json={"dias_credito": 0, **datos})
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()["id"]


def ciclo_completo(cliente, vin: str = VIN, numero: int = 1, tipo_vehiculo: str = "sedan") -> str:
    """Compra, importación, taller y factura local de la unidad; la deja en "lista".

    `numero` distingue el DTE de la factura local cuando se arman varias unidades."""
    subasta = _proveedor(
        cliente, tipo="exterior", nombre="Copart Inc.", identificacion_fiscal="94-2867490",
        pais="US", rubro="subasta", moneda_habitual="USD",
    )  # fmt: skip
    agente = _proveedor(
        cliente, tipo="local", nombre="Aduanas Express", nit="1669394-9",
        regimen="general", rubro="agente_aduanal", moneda_habitual="GTQ",
    )  # fmt: skip
    taller = _proveedor(
        cliente, tipo="local", nombre="Taller Don Chepe", nit="576937-K",
        regimen="pequeno_contribuyente", rubro="servicios", moneda_habitual="GTQ",
    )  # fmt: skip
    sufijo = vin[-4:]
    compra = cliente.post(
        f"{API}/compras/compras-unidades",
        json={
            "proveedor_id": subasta, "fecha": FECHA, "documento": f"LOT-{sufijo}", "vin": vin,
            "marca": "Honda", "linea": "Accord", "modelo": 2007, "color": "Gris",
            "tipo_vehiculo": tipo_vehiculo, "linea_negocio": "alquiler", "precio_usd": "8500.00",
            "comision_usd": "350.00", "documentacion_usd": "75.00", "arrastre_usd": "150.00",
        },
    )  # fmt: skip
    assert compra.status_code == 201, compra.text
    for concepto, moneda, monto in (
        ("flete", "GTQ", "3500.00"),
        ("seguro", "USD", "120.40"),
        ("dai", "GTQ", "1200.00"),
        ("iva_importacion", "GTQ", "5000.00"),
    ):
        gasto = cliente.post(
            f"{API}/compras/gastos-importacion",
            json={
                "vin": vin, "concepto": concepto, "proveedor_id": subasta if moneda == "USD" else agente,
                "fecha": FECHA, "documento": f"DOC-{concepto}", "moneda": moneda, "monto": monto,
            },
        )  # fmt: skip
        assert gasto.status_code == 201, gasto.text
    assert (
        cliente.post(
            f"{API}/unidades/{vin}/estado", json={"estado": "en_aduana", "documento": "BL"}
        ).status_code
        == 200
    )
    orden = cliente.post(
        f"{API}/taller/ordenes",
        json={
            "vin": vin, "tipo": "reacondicionamiento", "fecha_apertura": "2026-11-10", "kilometraje": 84500,
            "descripcion": "Frenos", "responsable": "Taller central",
        },
    )  # fmt: skip
    assert orden.status_code == 201, orden.text
    orden_id = orden.json()["id"]
    horas = cliente.post(
        f"{API}/taller/ordenes/{orden_id}/horas",
        json={"mecanico": "Luis", "fecha": "2026-11-12", "horas": "2.5", "tarea": "Frenos"},
    )
    assert horas.status_code == 201, horas.text
    factura = cliente.post(
        f"{API}/compras/facturas",
        json={
            "proveedor_id": taller, "serie": "A1", "numero": str(numero),
            "autorizacion": f"1A2B3C4D-1234-4ABC-9DEF-{numero:012d}", "fecha": "2026-11-11",
            "lineas": [{
                "descripcion": "Enderezado y pintura", "cuenta": "1.1.04.01", "linea_negocio": "alquiler",
                "vin": vin, "base": "1000.00", "iva": "120.00",
            }],
        },
    )  # fmt: skip
    assert factura.status_code == 201, factura.text
    assert cliente.post(f"{API}/taller/ordenes/{orden_id}/cerrar", json={}).status_code == 200
    return vin


def test_ciclo_completo_cuadra_al_centavo_con_el_mayor(cliente):
    ciclo_completo(cliente)

    respuesta = cliente.get(f"{URL}/{VIN}")
    assert respuesta.status_code == 200, respuesta.text
    hoja = respuesta.json()
    assert hoja["estado"] == "lista"
    assert hoja["compra"]["total_usd"] == "9075.000000"
    assert hoja["compra"]["tipo_cambio"] == "7.75000000"
    assert hoja["compra"]["total_gtq"] == "70331.250000"
    seguro = next(g for g in hoja["importacion"] if g["concepto"] == "seguro")
    assert (seguro["moneda"], seguro["monto"], seguro["tipo_cambio"], seguro["monto_gtq"]) == (
        "USD", "120.400000", "7.75000000", "933.100000",
    )  # fmt: skip
    # En el orden del catálogo de conceptos; el IVA de importación aparece pero no suma al costo.
    assert [g["concepto"] for g in hoja["importacion"]] == ["flete", "seguro", "dai", "iva_importacion"]
    assert hoja["importacion"][-1]["suma_al_costo"] is False
    assert hoja["importacion_gtq"] == "5633.100000"
    assert hoja["credito_fiscal_gtq"] == "5000.000000"
    assert [(m["numero"], m["costo_gtq"]) for m in hoja["mano_obra"]] == [("OT-00001", "112.500000")]
    # El IVA del pequeño contribuyente no da crédito fiscal: es parte del costo.
    assert [(r["descripcion"], r["monto_gtq"]) for r in hoja["repuestos"]] == [
        ("Enderezado y pintura", "1120.000000")
    ]
    assert hoja["reacondicionamiento_gtq"] == "1232.500000"
    assert Decimal(hoja["total_gtq"]) == TOTAL
    assert Decimal(hoja["saldo_mayor_gtq"]) == TOTAL
    assert (hoja["diferencia_gtq"], hoja["cuadra"], hoja["costo_alta_gtq"]) == ("0.000000", True, None)


def test_el_costo_acumulado_de_las_otras_pantallas_usa_la_misma_regla(cliente):
    ciclo_completo(cliente)
    with SessionLocal() as db:
        assert compras.costos_de_unidades(db, [VIN]) == {VIN: TOTAL}
        assert compras.resumen_gastos_unidad(db, VIN)["costo_total_gtq"] == TOTAL
    lista = cliente.get(f"{API}/unidades/etapas-importacion", params={"etapa": "lista"}).json()
    assert Decimal(lista["unidades"][0]["costo_total_gtq"]) == TOTAL


def test_un_movimiento_del_mayor_fuera_de_la_hoja_la_descuadra(cliente):
    ciclo_completo(cliente)
    with SessionLocal() as db:
        en_proceso = contabilidad.cuenta_regla(db, "compra_unidad", "unidad_en_transito")
        caja = contabilidad.cuenta_regla(db, "factura_compra", "por_pagar_gtq")
        contabilidad.registrar_automatica(
            db,
            fecha=date(2026, 11, 12),
            concepto="Cargo sin documento de la hoja",
            lineas=[
                LineaEntrada(cuenta_id=en_proceso, lado="debe", monto="50.00", vin=VIN),
                LineaEntrada(cuenta_id=caja, lado="haber", monto="50.00"),
            ],
            documento_tipo="prueba",
            documento_id=1,
        )
        db.commit()

    hoja = cliente.get(f"{URL}/{VIN}").json()
    assert hoja["cuadra"] is False
    assert hoja["diferencia_gtq"] == "-50.000000"
    assert Decimal(hoja["saldo_mayor_gtq"]) == TOTAL + 50


def test_unidad_sin_movimientos_y_vin_inexistente(cliente):
    unidad = {"vin": OTRO_VIN, "marca": "Honda", "linea": "Fit", "modelo": 2010, "color": "Azul"}
    assert cliente.post(f"{API}/unidades", json={**unidad, "tipo_vehiculo": "sedan"}).status_code == 201
    hoja = cliente.get(f"{URL}/{OTRO_VIN}").json()
    assert (hoja["compra"], hoja["total_gtq"], hoja["cuadra"]) == (None, "0.000000", True)
    assert cliente.get(f"{URL}/{VIN}").status_code == 404


def test_sin_sesion_responde_401():
    assert TestClient(app).get(f"{URL}/{VIN}").status_code == 401
