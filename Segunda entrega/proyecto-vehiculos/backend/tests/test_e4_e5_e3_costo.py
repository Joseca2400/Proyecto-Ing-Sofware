"""Tarea 2 · Costo de la unidad: compra, importación, taller y alta en flota (E4, E5, E3)."""

from tests.conftest import API, AUX, CONTADOR, F2, F3, gasto, saldo


# ---------------------------------------------------------------- HU-4.01 Proveedores

def test_hu_4_01_proveedor_local_exige_nit_valido_y_unico(client, proveedores):
    base = {"nombre": "Repuestos GT", "tipo": "LOCAL", "rubro": "REPUESTOS", "moneda": "GTQ"}
    assert client.post(f"{API}/proveedores", json=base, headers=AUX).status_code == 422
    assert client.post(f"{API}/proveedores", json={**base, "nit": "1234567-1"}, headers=AUX).status_code == 422
    assert client.post(f"{API}/proveedores", json={**base, "nit": "12345679"}, headers=AUX).status_code == 409


# ---------------------------------------------------------------- HU-4.02 Compra en EE. UU.

def test_hu_4_02_compra_crea_unidad_cxp_en_usd_y_partida(client, comprar):
    u = comprar(precio=8000, cargos=500)
    assert u["estado"] == "EN_TRANSITO"
    cxp = client.get(f"{API}/cuentas-por-pagar", headers=AUX).json()
    assert (cxp[0]["moneda"], cxp[0]["monto"], cxp[0]["tipo_cambio"]) == ("USD", 8500, 7.7)
    assert saldo(client, "1.1.06", u["vin"]) == 65450  # 8,500 × 7.70
    p = client.get(f"{API}/partidas/{cxp[0]['partida_id']}", headers=AUX).json()
    assert p["automatica"] and p["estado"] == "CONTABILIZADA" and p["origen_tipo"] == "COMPRA_UNIDAD"


# ---------------------------------------------------------------- HU-4.04 Gastos de importación

def test_hu_4_04_iva_de_importacion_es_credito_fiscal_no_costo(client, comprar, proveedores):
    u = comprar()
    flete = gasto(client, u["id"], proveedores["naviera"]["id"], "FLETE", "USD", 900)
    iva = gasto(client, u["id"], proveedores["sat"]["id"], "IVA_IMPORTACION", "GTQ", 8000)
    assert flete["capitalizable"] and not iva["capitalizable"]
    assert saldo(client, "1.1.06", u["vin"]) == 65450 + 6948  # 900 × 7.72
    assert saldo(client, "1.1.05") == 8000
    assert saldo(client, "2.1.01") == 8000  # CxP local en quetzales


# ---------------------------------------------------------------- HU-4.07 Estados de importación

def test_hu_4_07_orden_de_las_etapas(client, comprar):
    u = comprar()
    url = f"{API}/unidades/{u['id']}/estado"
    assert client.post(url, json={"estado": "LISTA", "documento": "x"}, headers=AUX).status_code == 409
    r = client.post(url, json={"estado": "EN_ADUANA", "documento": "Arribo a Puerto Quetzal"}, headers=AUX)
    assert r.json()["estado"] == "EN_ADUANA"
    assert [h["estado_nuevo"] for h in r.json()["historial"]] == ["EN_TRANSITO", "EN_ADUANA"]


# ---------------------------------------------------------------- HU-5.01 / 5.03 / 5.07 Taller

def abrir(client, unidad_id, tipo="REACONDICIONAMIENTO"):
    return client.post(f"{API}/ordenes", headers=AUX, json={
        "unidad_id": unidad_id, "tipo": tipo, "descripcion": "Trabajo", "responsable": "Jefe", "fecha": F3})


def test_hu_5_01_tipo_de_orden_coherente_con_el_estado(client, comprar):
    u = comprar()
    assert abrir(client, u["id"]).status_code == 422  # aún en tránsito
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "x"}, headers=AUX)
    assert abrir(client, u["id"], "MANTENIMIENTO").status_code == 422  # no está en flota
    r = abrir(client, u["id"])
    assert r.status_code == 201 and r.json()["vin"] == u["vin"]
    assert client.get(f"{API}/unidades/{u['id']}", headers=AUX).json()["estado"] == "EN_TALLER"


def test_hu_5_03_mano_de_obra_con_tarifa_interna(client, comprar):
    u = comprar()
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "x"}, headers=AUX)
    orden = abrir(client, u["id"]).json()
    r = client.post(f"{API}/ordenes/{orden['id']}/mano-obra", headers=AUX,
                    json={"mecanico": "Pedro", "fecha": F3, "horas": 6.5, "descripcion": "Suspensión"})
    assert r.json()["costo_total"] == 487.5 and r.json()["mano_obra"][0]["tarifa"] == 75


def test_hu_5_07_reacondicionamiento_se_capitaliza(client, comprar):
    u = comprar()
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "x"}, headers=AUX)
    orden = abrir(client, u["id"]).json()
    client.post(f"{API}/ordenes/{orden['id']}/mano-obra", headers=AUX,
                json={"mecanico": "Pedro", "fecha": F3, "horas": 10, "descripcion": "Frenos"})
    url = f"{API}/ordenes/{orden['id']}/cerrar"
    assert client.post(url, json={"fecha": F3}, headers=AUX).status_code == 403  # cierra el contador
    r = client.post(url, json={"fecha": F3}, headers=CONTADOR)
    assert r.json()["estado"] == "CERRADA" and r.json()["partida_id"]
    assert saldo(client, "1.1.06", u["vin"]) == 65450 + 750
    assert saldo(client, "5.1.01") == 750  # mano de obra aplicada
    assert client.post(f"{API}/ordenes/{orden['id']}/mano-obra", headers=AUX, json={
        "mecanico": "Pedro", "fecha": F3, "horas": 1, "descripcion": "x"}).status_code == 409


def test_hu_5_07_orden_sin_costo_exige_justificacion(client, comprar):
    u = comprar()
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "x"}, headers=AUX)
    orden = abrir(client, u["id"]).json()
    url = f"{API}/ordenes/{orden['id']}/cerrar"
    assert client.post(url, json={"fecha": F3}, headers=CONTADOR).status_code == 422
    assert client.post(url, json={"fecha": F3, "justificacion": "Sólo inspección"}, headers=CONTADOR).status_code == 200


def test_hu_5_07_mantenimiento_es_gasto_de_la_unidad(client, unidad_en_flota):
    u = unidad_en_flota()
    orden = abrir(client, u["id"], "MANTENIMIENTO").json()
    assert client.get(f"{API}/unidades/{u['id']}", headers=AUX).json()["estado"] == "EN_TALLER"
    client.post(f"{API}/ordenes/{orden['id']}/mano-obra", headers=AUX,
                json={"mecanico": "Pedro", "fecha": F3, "horas": 2, "descripcion": "Cambio de aceite"})
    client.post(f"{API}/ordenes/{orden['id']}/cerrar", json={"fecha": F3}, headers=CONTADOR)
    assert saldo(client, "6.1.01", u["vin"]) == 150
    assert client.get(f"{API}/unidades/{u['id']}", headers=AUX).json()["estado"] == "EN_FLOTA"


# ---------------------------------------------------------------- HU-4.08 Hoja de costo

def test_hu_4_08_hoja_de_costo_desglosada_y_cuadrada(client, comprar, proveedores):
    u = comprar()
    gasto(client, u["id"], proveedores["naviera"]["id"], "FLETE", "USD", 900)
    gasto(client, u["id"], proveedores["sat"]["id"], "DAI", "GTQ", 3000)
    hoja = client.get(f"{API}/unidades/{u['id']}/hoja-costo", headers=AUX).json()
    grupos = {c["grupo"]: c["total_q"] for c in hoja["componentes"]}
    assert grupos == {"Compra": 65450, "Importación": 6948 + 3000}
    compra = hoja["componentes"][0]["detalle"][0]
    assert (compra["moneda"], compra["monto_original"], compra["tipo_cambio"]) == ("USD", 8500, 7.7)
    assert hoja["costo_total"] == 75398 and hoja["cuadra_con_mayor"]


# ---------------------------------------------------------------- HU-3.01 Alta en flota

def test_hu_3_01_alta_traslada_el_costo_al_activo_fijo(client, unidad_en_flota):
    u = unidad_en_flota()
    costo = 65450 + 6948 + 3000 + 750
    assert u["estado"] == "EN_FLOTA" and u["costo_alta"] == costo and u["vida_util_meses"] == 48
    assert saldo(client, "1.1.06", u["vin"]) == 0
    assert saldo(client, "1.2.01", u["vin"]) == costo
    hoja = client.get(f"{API}/unidades/{u['id']}/hoja-costo", headers=AUX).json()
    assert hoja["trasladado_a_flota"] == costo and hoja["cuadra_con_mayor"]


def test_hu_3_01_solo_unidades_listas_y_sin_ordenes_abiertas(client, comprar):
    u = comprar()
    alta = {"fecha": F3}
    assert client.post(f"{API}/unidades/{u['id']}/alta-flota", json=alta, headers=CONTADOR).status_code == 409
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "x"}, headers=AUX)
    abrir(client, u["id"])
    r = client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "LISTA", "documento": "x"}, headers=AUX)
    assert r.status_code == 409 and "órdenes" in r.json()["detail"]
    assert client.post(f"{API}/unidades/{u['id']}/alta-flota", json=alta, headers=AUX).status_code == 403
