"""Tarea 3 · Ingreso: contrato, factura, cobro y reportes (E3, E6, E2.09, E7)."""

from tests.conftest import API, AUX, CONTADOR, F3, F4, F5, GERENCIA, saldo


def contrato(client, cliente, unidad, moneda="GTQ", tarifa=350, salida="2026-10-13", prevista="2026-10-18"):
    return client.post(f"{API}/contratos", headers=AUX, json={
        "cliente_id": cliente["id"], "unidad_id": unidad["id"], "fecha_salida": salida,
        "fecha_prevista": prevista, "tarifa_diaria": tarifa, "moneda": moneda})


def cerrar(client, c, devolucion="2026-10-19", km=650):
    return client.post(f"{API}/contratos/{c['id']}/cerrar", headers=AUX,
                       json={"fecha_devolucion": devolucion, "km_entrada": km})


# ---------------------------------------------------------------- HU-6.01 Clientes

def test_hu_6_01_cliente_con_nit_valido_y_sin_duplicados(client, cliente):
    base = {"tipo": "INDIVIDUAL", "nombre": "Juan Pérez"}
    assert client.post(f"{API}/clientes", json=base, headers=AUX).status_code == 422
    assert client.post(f"{API}/clientes", json={**base, "nit": "1234567-1"}, headers=AUX).status_code == 422
    assert client.post(f"{API}/clientes", json={**base, "nit": "12345679"}, headers=AUX).status_code == 409
    r = client.post(f"{API}/clientes", json={**base, "pasaporte": "X1234567", "pais": "Estados Unidos"}, headers=AUX)
    assert r.status_code == 201


# ---------------------------------------------------------------- HU-3.06 / HU-3.08 Contratos

def test_hu_3_06_solo_unidades_en_flota_y_disponibles(client, cliente, comprar, unidad_en_flota):
    en_transito = comprar(9)
    assert contrato(client, cliente, en_transito).status_code == 409
    u = unidad_en_flota()
    r = contrato(client, cliente, u)
    assert r.status_code == 201 and r.json()["monto_estimado"] == 350 * 5
    otro = contrato(client, cliente, u)
    assert otro.status_code == 409 and "ya está alquilada" in otro.json()["detail"]


def test_hu_3_08_cierre_calcula_dias_y_kilometraje(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u).json()
    r = cerrar(client, c, devolucion="2026-10-19", km=650)
    assert r.json()["estado"] == "CERRADO"
    assert (r.json()["dias"], r.json()["km_recorridos"], r.json()["monto"]) == (6, 650, 2100)
    assert client.get(f"{API}/unidades/{u['id']}", headers=AUX).json()["kilometraje"] == 650
    assert contrato(client, cliente, u, salida="2026-10-20", prevista="2026-10-22").status_code == 201


# ---------------------------------------------------------------- HU-6.02 Factura FEL

def test_hu_6_02_factura_en_quetzales_separa_iva(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u).json()
    cerrar(client, c)
    r = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX)
    assert r.status_code == 201, r.text
    f = r.json()
    assert (f["total"], f["base"], f["iva"]) == (2100, 1875, 225)
    assert f["simulada"] and f["serie"] == "SIM-A" and len(f["autorizacion"]) == 36
    assert saldo(client, "4.1.01", u["vin"]) == 1875
    assert saldo(client, "2.1.03") == 225
    assert saldo(client, "1.1.03") == 2100
    # HU-3.10 criterio 5: no se factura dos veces el mismo contrato
    assert client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX).status_code == 409


def test_hu_6_02_consumidor_final_sobre_el_umbral(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u, tarifa=500).json()
    cerrar(client, c)  # 6 días × Q500 = Q3,000
    r = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4, "consumidor_final": True}, headers=AUX)
    assert r.status_code == 422 and "Consumidor Final" in r.json()["detail"]


def test_hu_6_02_factura_en_dolares_se_contabiliza_en_quetzales(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u, moneda="USD", tarifa=56).json()
    cerrar(client, c)  # 6 × USD 56 = USD 336
    f = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX).json()
    assert (f["moneda"], f["total"], f["tipo_cambio"], f["total_q"]) == ("USD", 336, 7.73, 2597.28)
    bal = client.get(f"{API}/contabilidad/balance", headers=CONTADOR).json()
    assert bal["cuadra"]
    assert next(x for x in bal["cuentas"] if x["codigo"] == "1.1.04")["saldo_usd"] == 336


# ---------------------------------------------------------------- HU-6.07 / HU-2.09 Cobros

def test_hu_6_07_cobro_parcial_y_saldo(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u).json()
    cerrar(client, c)
    f = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX).json()
    url = f"{API}/facturas/{f['id']}/cobros"
    assert client.post(url, json={"fecha": F5, "forma": "TRANSFERENCIA", "monto": 3000}, headers=AUX).status_code == 422
    client.post(url, json={"fecha": F5, "forma": "TRANSFERENCIA", "monto": 1000}, headers=AUX)
    facturas = client.get(f"{API}/facturas", params={"con_saldo": True}, headers=AUX).json()
    assert facturas[0]["saldo"] == 1100
    assert saldo(client, "1.1.01") == 1000


def test_hu_2_09_cobro_en_dolares_registra_diferencial_cambiario(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u, moneda="USD", tarifa=56).json()
    cerrar(client, c)
    f = client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX).json()  # TC 7.73
    r = client.post(f"{API}/facturas/{f['id']}/cobros", headers=AUX,
                    json={"fecha": F5, "forma": "TRANSFERENCIA", "monto": 336, "referencia": "TRF-881"})  # TC 7.75
    cobro = r.json()
    assert cobro["diferencial_q"] == 6.72  # 336 × (7.75 − 7.73), ganancia
    assert saldo(client, "1.1.04") == 0
    assert saldo(client, "7.1.01") == -6.72  # cuenta deudora con saldo acreedor = ganancia
    assert client.get(f"{API}/contabilidad/balance", headers=CONTADOR).json()["cuadra"]


# ---------------------------------------------------------------- E7 Reportes

def test_hu_7_04_unidades_por_etapa(client, comprar, unidad_en_flota):
    unidad_en_flota(1)
    comprar(2, precio=10000, cargos=0)
    r = client.get(f"{API}/reportes/unidades-por-etapa", headers=GERENCIA).json()
    etapas = {e["estado"]: (e["cantidad"], e["valor_q"]) for e in r["etapas"]}
    assert etapas["EN_FLOTA"] == (1, 76148) and etapas["EN_TRANSITO"] == (1, 77000)
    assert r["capital_invertido_q"] == 76148 + 77000


def test_hu_7_02_rentabilidad_por_unidad_sale_del_mayor(client, cliente, unidad_en_flota):
    u = unidad_en_flota()
    c = contrato(client, cliente, u).json()
    cerrar(client, c)
    client.post(f"{API}/contratos/{c['id']}/facturar", json={"fecha": F4}, headers=AUX)
    fila = client.get(f"{API}/reportes/rentabilidad-unidades", headers=GERENCIA).json()[0]
    assert fila["costo_adquisicion_q"] == 76148
    assert fila["ingresos_alquiler_q"] == 1875 and fila["resultado_q"] == 1875
    assert fila["dias_alquilada"] == 6 and fila["contratos"] == 1
