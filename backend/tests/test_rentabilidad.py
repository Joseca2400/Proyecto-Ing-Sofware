"""HU-3.13: rentabilidad por unidad y por contrato, leída del mayor filtrado por VIN.

La unidad `VIN` se compra, se da de alta (10/01/2024), se deprecia febrero de 2024, recibe un
mantenimiento y se alquila tres días con 150 km excedentes; el contrato se cierra y se factura.
`OTRO_VIN` queda en "lista", sin alta: no es flota.
"""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion import service as configuracion
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from tests.test_depositos_garantia import PERFIL
from tests.test_depreciacion_mensual import CUOTA, PARAMETROS, gerente  # noqa: F401
from tests.test_hoja_costo import API, OTRO_VIN, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

URL_UNIDADES = f"{API}/reportes/rentabilidad/unidades"
URL_CONTRATOS = f"{API}/reportes/rentabilidad/contratos"
TARIFA = {
    "tipo_vehiculo": "sedan", "modalidad": "diaria", "moneda": "GTQ", "monto": "350.00",
    "km_incluido": 150, "precio_km_adicional": "2.50", "vigente_desde": "2026-01-01",
}  # fmt: skip
PERSONA = {
    "tipo": "individual", "nombre": "María López", "tipo_identificacion": "cui",
    "identificacion": "2547 12345 0101",
}  # fmt: skip
MANTENIMIENTO = Decimal("500.00")
# 3 días × 350 = 1050 y 150 km × 2.50 = 375, con IVA: bases 937.50 y 334.82.
ALQUILER = Decimal("937.50")
CARGOS = Decimal("334.82")
TODO = {"desde": "2024-01-01", "hasta": date.today().isoformat()}


def _mantenimiento(fecha: date) -> None:
    """Gasto de mantenimiento con el VIN, como lo dejará la orden de mantenimiento (Sprint 5)."""
    with SessionLocal() as db:
        gasto = configuracion.buscar_cuenta(db, "6.2").id
        banco = configuracion.buscar_cuenta(db, "1.1.01.02").id
        contabilidad.registrar_automatica(
            db,
            fecha=fecha,
            concepto="Cambio de aceite",
            lineas=[
                LineaEntrada(
                    cuenta_id=gasto, lado="debe", monto=f"{MANTENIMIENTO}", linea_negocio="alquiler", vin=VIN
                ),
                LineaEntrada(
                    cuenta_id=banco, lado="haber", monto=f"{MANTENIMIENTO}", linea_negocio="administracion"
                ),
            ],  # fmt: skip
            documento_tipo="prueba_mantenimiento",
            documento_id=1,
        )
        db.commit()


@pytest.fixture
def flota(cliente, gerente) -> int:  # noqa: F811
    """Deja la unidad depreciada, con mantenimiento y con su contrato cerrado y facturado."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE tarifa, cliente, perfil_fiscal RESTART IDENTITY CASCADE"))
        db.commit()
    ciclo_completo(cliente, VIN, numero=1)
    ciclo_completo(cliente, OTRO_VIN, numero=2)
    assert cliente.post(f"{API}/unidades/{VIN}/alta-flota", json=PARAMETROS).status_code == 201
    calculo = cliente.post(f"{API}/contabilidad/depreciaciones", json={"anio": 2024, "mes": 2}).json()
    partida = calculo["partida"]["id"]
    assert cliente.post(f"{API}/contabilidad/partidas/{partida}/enviar-a-revision").status_code == 200
    assert gerente.post(f"{API}/contabilidad/partidas/{partida}/contabilizar").status_code == 200
    _mantenimiento(date(2026, 11, 15))

    assert cliente.post(f"{API}/configuracion/perfil-fiscal", json=PERFIL).status_code == 201
    assert cliente.post(f"{API}/alquileres/tarifas", json=TARIFA).status_code == 201
    cliente_id = cliente.post(f"{API}/facturacion/clientes", json=PERSONA).json()["id"]
    contrato = cliente.post(
        f"{API}/alquileres/contratos",
        json={
            "cliente_id": cliente_id, "vin": VIN, "salida": "2026-11-10T09:00:00-06:00",
            "devolucion_prevista": "2026-11-13", "modalidad": "diaria", "moneda": "GTQ",
            "km_salida": 90000, "combustible_salida": 8, "deposito_esperado": "0",
        },
    )  # fmt: skip
    assert contrato.status_code == 201, contrato.text
    contrato_id = contrato.json()["id"]
    cierre = {"devolucion": "2026-11-13T09:00:00-06:00", "km_devolucion": 90600, "combustible_devolucion": 5}
    assert cliente.post(f"{API}/alquileres/contratos/{contrato_id}/cierre", json=cierre).status_code == 200
    factura = cliente.post(f"{API}/alquileres/contratos/{contrato_id}/factura")
    assert factura.status_code == 201, factura.text
    return contrato_id


@pytest.fixture
def regla_seguro():
    """Asigna la regla de seguro durante la prueba y la deja sin cuenta al terminar."""
    yield
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE regla_contabilizacion SET cuenta_codigo = NULL"
                " WHERE documento_tipo = 'rentabilidad' AND concepto = 'seguro'"
            )
        )
        db.commit()


def test_rentabilidad_por_unidad_del_mayor(cliente, flota):
    respuesta = cliente.get(URL_UNIDADES, params=TODO)
    assert respuesta.status_code == 200, respuesta.text
    reporte = respuesta.json()
    (unidad,) = reporte["unidades"]  # OTRO_VIN no tiene alta en la flota
    assert (unidad["vin"], unidad["fecha_alta"]) == (VIN, "2024-01-10")
    assert Decimal(unidad["ingreso_alquiler"]) == ALQUILER + CARGOS
    assert Decimal(unidad["depreciacion"]) == CUOTA
    assert Decimal(unidad["mantenimiento"]) == MANTENIMIENTO
    assert (unidad["seguro"], unidad["marchamo"]) == (None, None)
    assert Decimal(unidad["costos"]) == CUOTA + MANTENIMIENTO
    assert Decimal(unidad["resultado"]) == ALQUILER + CARGOS - CUOTA - MANTENIMIENTO
    assert reporte["totales"]["resultado"] == unidad["resultado"]
    assert reporte["totales"]["seguro"] is None
    assert len(reporte["pendientes"]) == 2
    assert "rentabilidad · seguro" in reporte["pendientes"][0]

    # Cuadra con el mayor: el ingreso es el saldo de la cuenta de ingreso de alquiler para el VIN.
    with SessionLocal() as db:
        ingreso = contabilidad.cuenta_regla(db, "rentabilidad", "ingreso_alquiler")
        assert contabilidad.saldo_cuenta(db, ingreso, vin=VIN) == Decimal(unidad["ingreso_alquiler"])


def test_el_periodo_filtra_por_la_fecha_de_la_partida(cliente, flota):
    reporte = cliente.get(URL_UNIDADES, params={"desde": "2026-01-01", "hasta": TODO["hasta"]}).json()
    (unidad,) = reporte["unidades"]
    assert Decimal(unidad["depreciacion"]) == 0  # la de febrero de 2024 queda fuera
    assert Decimal(unidad["mantenimiento"]) == MANTENIMIENTO

    solo_2024 = cliente.get(URL_UNIDADES, params={"desde": "2024-01-01", "hasta": "2024-12-31"}).json()
    (unidad,) = solo_2024["unidades"]
    assert (Decimal(unidad["ingreso_alquiler"]), Decimal(unidad["depreciacion"])) == (0, CUOTA)

    al_reves = cliente.get(URL_UNIDADES, params={"desde": "2026-02-01", "hasta": "2026-01-01"})
    assert al_reves.status_code == 400
    assert "posterior" in al_reves.json()["detail"]


def test_el_contador_asigna_la_cuenta_de_un_concepto_pendiente(cliente, flota, regla_seguro):
    regla = next(
        r for r in cliente.get(f"{API}/contabilidad/reglas").json()
        if (r["documento_tipo"], r["concepto"]) == ("rentabilidad", "seguro")
    )  # fmt: skip
    assert (
        cliente.put(f"{API}/contabilidad/reglas/{regla['id']}", json={"cuenta_codigo": "6.2"}).status_code
        == 200
    )
    reporte = cliente.get(URL_UNIDADES, params=TODO).json()
    assert Decimal(reporte["unidades"][0]["seguro"]) == MANTENIMIENTO  # misma cuenta en esta prueba
    assert len(reporte["pendientes"]) == 1


def test_filtra_por_vin(cliente, flota):
    assert cliente.get(URL_UNIDADES, params={**TODO, "vin": OTRO_VIN}).json()["unidades"] == []
    assert len(cliente.get(URL_UNIDADES, params={**TODO, "vin": VIN.lower()}).json()["unidades"]) == 1
    assert cliente.get(URL_CONTRATOS, params={**TODO, "vin": OTRO_VIN}).json()["contratos"] == []


def test_rentabilidad_por_contrato(cliente, flota):
    respuesta = cliente.get(URL_CONTRATOS, params=TODO)
    assert respuesta.status_code == 200, respuesta.text
    reporte = respuesta.json()
    (contrato,) = reporte["contratos"]
    assert (contrato["contrato_id"], contrato["numero"], contrato["vin"]) == (flota, 1, VIN)
    assert (contrato["cliente"], contrato["estado"], len(contrato["facturas"])) == (
        "María López",
        "cerrado",
        1,
    )
    assert Decimal(contrato["alquiler"]) == ALQUILER
    assert Decimal(contrato["cargos_adicionales"]) == CARGOS
    assert Decimal(contrato["ingresos"]) == ALQUILER + CARGOS
    assert Decimal(contrato["costos_directos"]) == 0
    assert Decimal(contrato["resultado"]) == ALQUILER + CARGOS
    assert reporte["totales"]["ingresos"] == contrato["ingresos"]
    assert any("Costos directos" in p for p in reporte["pendientes"])

    # La salida del contrato decide el período.
    fuera = cliente.get(URL_CONTRATOS, params={"desde": "2024-01-01", "hasta": "2026-11-09"}).json()
    assert fuera["contratos"] == []
    assert fuera["totales"]["ingresos"] == "0.000000"


def test_un_contrato_sin_factura_no_tiene_ingresos(cliente, flota):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE factura RESTART IDENTITY CASCADE"))
        db.commit()
    (contrato,) = cliente.get(URL_CONTRATOS, params=TODO).json()["contratos"]
    assert (contrato["ingresos"], contrato["facturas"]) == ("0.000000", [])


def test_exporta_a_csv(cliente, flota):
    respuesta = cliente.get(f"{URL_UNIDADES}/csv", params=TODO)
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/csv")
    assert "attachment" in respuesta.headers["content-disposition"]
    texto = respuesta.content.decode("utf-8")
    assert texto.startswith("﻿VIN,Marca,Línea")
    encabezado, fila, total = texto.lstrip("﻿").strip().split("\r\n")
    assert fila.startswith(f"{VIN},Honda,Accord,2007,en_flota,2024-01-10,1272.32,1608.27,500.00,pendiente")
    assert total.startswith("Total,")

    contratos = cliente.get(f"{URL_CONTRATOS}/csv", params=TODO).content.decode("utf-8").strip().split("\r\n")
    assert contratos[1].startswith(f"1,{VIN},María López,2026-11-10,2026-11-13,cerrado,")
    assert contratos[1].endswith("937.50,334.82,1272.32,0.00,1272.32")


@pytest.mark.parametrize("url", [URL_UNIDADES, URL_CONTRATOS, f"{URL_UNIDADES}/csv", f"{URL_CONTRATOS}/csv"])
def test_permisos(url):
    anonimo = TestClient(app)
    assert anonimo.get(url).status_code == 401
    assert anonimo.get(url, headers=_token(anonimo, "auxiliar@empresa.gt")).status_code == 403
    for correo in ("gerencia@empresa.gt", "gerente.financiero@empresa.gt"):
        assert anonimo.get(url, headers=_token(anonimo, correo)).status_code == 200
