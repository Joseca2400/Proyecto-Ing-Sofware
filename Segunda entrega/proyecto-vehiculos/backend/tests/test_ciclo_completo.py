"""Corte transversal: una unidad recorre su ciclo y la contabilidad cuadra al final."""

from tests.conftest import API, AUX, CONTADOR, F4, F5, GERENCIA, saldo


def test_ciclo_completo_de_una_unidad(client, unidad_en_flota, cliente):
    u = unidad_en_flota()  # compra USD + flete USD + DAI + taller + alta

    c = client.post(f"{API}/contratos", headers=AUX, json={
        "cliente_id": cliente["id"], "unidad_id": u["id"], "fecha_salida": "2026-10-13",
        "fecha_prevista": "2026-10-18", "tarifa_diaria": 56, "moneda": "USD"}).json()
    client.post(f"{API}/contratos/{c['id']}/cerrar", headers=AUX, json={"fecha_devolucion": "2026-10-19", "km_entrada": 820})
    f = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX).json()
    client.post(f"{API}/facturas/{f['id']}/cobros", headers=AUX,
                json={"fecha": F5, "forma": "TRANSFERENCIA", "monto": f["total"]})

    bal = client.get(f"{API}/contabilidad/balance", headers=CONTADOR).json()
    assert bal["cuadra"]
    saldos = {x["codigo"]: x["saldo"] for x in bal["cuentas"]}
    assert saldos["1.2.01"] == 76148                      # activo fijo de la unidad
    assert saldos["1.1.06"] == 0                          # nada queda en proceso
    assert saldos["1.1.02"] == round(336 * 7.75, 2)       # cobro en dólares
    assert saldos["2.1.02"] == round(8500 * 7.70 + 900 * 7.72, 2)  # se debe a subasta y naviera

    # Cada movimiento de la unidad está ligado a su VIN
    por_vin = client.get(f"{API}/contabilidad/balance", params={"vin": u["vin"]}, headers=CONTADOR).json()
    assert {x["codigo"] for x in por_vin["cuentas"]} >= {"1.1.06", "1.2.01", "4.1.01", "1.1.04"}

    rent = client.get(f"{API}/reportes/rentabilidad-unidades", headers=GERENCIA).json()[0]
    assert rent["ingresos_alquiler_q"] == saldo(client, "4.1.01", u["vin"]) > 0

    acciones = {b["accion"] for b in client.get(f"{API}/bitacora", params={"vin": u["vin"]}, headers=CONTADOR).json()}
    assert {"COMPRA", "GASTO_IMPORTACION", "ABRIR_ORDEN", "CERRAR_ORDEN", "CAMBIAR_ESTADO", "FACTURAR"} <= acciones
