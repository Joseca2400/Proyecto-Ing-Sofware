"""Demo del Sprint 1 según el guion de Sprint1.md (sección 10): de la compra al alta en flota.

Requiere la API corriendo con una base vacía.
Uso:  python scripts/demo_ciclo.py [http://localhost:8000]
"""

import sys

import httpx

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000") + "/api/v1"
PASSWORD = "Demo2026!"
c = httpx.Client(base_url=BASE, timeout=10)


def login(usuario):
    r = c.post("/auth/login", json={"usuario": usuario, "password": PASSWORD})
    if r.is_error:
        sys.exit(f"No se pudo iniciar sesión como {usuario}: {r.json().get('detail')}")
    return {"Authorization": f"Bearer {r.json()['token']}"}


def call(metodo, ruta, quien, **kw):
    r = c.request(metodo, ruta, headers=quien, **kw)
    if r.is_error:
        sys.exit(f"\nError {r.status_code} en {metodo} {ruta}: {r.json().get('detail')}")
    return r.json() if r.content else None


def intento(metodo, ruta, quien, **kw):
    r = c.request(metodo, ruta, headers=quien, **kw)
    return r.status_code, (r.json().get("detail") if r.content else "")


def paso(n, titulo):
    print(f"\n{'═' * 72}\n {n}. {titulo}\n{'═' * 72}")


def q(v):
    return f"Q{v:,.2f}"


def main():
    paso(1, "Sesión y permisos")
    malo = c.post("/auth/login", json={"usuario": "aux", "password": "incorrecta"})
    print(f"Contraseña incorrecta → {malo.status_code}: {malo.json()['detail']}")
    AUX, CONTADOR, GERENTE, GERENCIA = (login(u) for u in ("aux", "contador", "gerente", "gerencia"))
    print("Sesiones iniciadas: aux (auxiliar), contador, gerente (gerente financiero) y gerencia")
    print(f"La auxiliar intenta cargar un tipo de cambio → {intento('POST', '/tipos-cambio', AUX, json={'fecha': '2026-10-01', 'valor': 7.7})[0]}")
    print(f"La gerencia intenta registrar una compra → {intento('POST', '/compras', GERENCIA, json={})[0]}")
    print(f"Sin sesión → {c.get('/cuentas').status_code}")

    paso(2, "Preparación: catálogo y tipos de cambio")
    arbol = call("GET", "/cuentas/arbol", AUX)
    detalle = sum(1 for _ in _hojas(arbol))
    print(f"Catálogo semilla: {len(arbol)} grupos principales, {detalle} cuentas de detalle")
    for fecha, valor in [("2026-10-01", 7.70), ("2026-10-05", 7.72), ("2026-10-12", 7.71)]:
        call("POST", "/tipos-cambio", CONTADOR, json={"fecha": fecha, "valor": valor})
    print("El contador registra los tipos de cambio: 01/10 7.70 · 05/10 7.72 · 12/10 7.71")
    print(f"Tipo de cambio negativo → {intento('POST', '/tipos-cambio', CONTADOR, json={'fecha': '2026-10-02', 'valor': -1})[0]}")

    paso(3, "Compra en EE. UU.")
    subasta = call("POST", "/proveedores", AUX, json={"nombre": "Copart Inc.", "tipo": "EXTERIOR", "rubro": "SUBASTA", "moneda": "USD"})
    naviera = call("POST", "/proveedores", AUX, json={"nombre": "Seaboard Marine", "tipo": "EXTERIOR", "rubro": "NAVIERA", "moneda": "USD"})
    sat = call("POST", "/proveedores", AUX, json={"nombre": "SAT", "tipo": "LOCAL", "nit": "1669394-9", "rubro": "SAT", "moneda": "GTQ"})
    datos = {"proveedor_id": subasta["id"], "fecha": "2026-10-01", "numero_lote": "LOT-58213",
             "vin": "1HGCM82633A004352", "marca": "Honda", "linea": "Accord", "modelo_anio": 2019,
             "color": "Gris", "tipo_vehiculo": "Sedán", "precio_usd": 8000, "cargos_usd": 500}
    compra = call("POST", "/compras", AUX, json=datos)
    u = compra["unidad"]
    print(f"VIN {u['vin']} → unidad {u['estado']}")
    print(f"Cuenta por pagar USD 8,500.00 a Copart; partida No. {compra['partida_numero']} por {q(8500 * 7.70)}")
    print(f"Mismo VIN otra vez → {intento('POST', '/compras', AUX, json=datos)[0]} (no se duplica)")

    paso(4, "Importación")
    call("POST", "/gastos-importacion", AUX, json={"unidad_id": u["id"], "proveedor_id": naviera["id"],
                                                   "concepto": "FLETE", "fecha": "2026-10-05", "moneda": "USD", "monto": 900})
    call("POST", f"/unidades/{u['id']}/estado", AUX, json={"estado": "EN_ADUANA", "documento": "Arribo a Puerto Quetzal"})
    call("POST", "/gastos-importacion", AUX, json={"unidad_id": u["id"], "proveedor_id": sat["id"],
                                                   "concepto": "DAI", "fecha": "2026-10-05", "moneda": "GTQ", "monto": 3000})
    iva = call("POST", "/gastos-importacion", AUX, json={"unidad_id": u["id"], "proveedor_id": sat["id"],
                                                         "concepto": "IVA_IMPORTACION", "fecha": "2026-10-05", "moneda": "GTQ", "monto": 8200})
    print("Flete USD 900 (TC 7.72) y DAI Q3,000 → costo de la unidad; la unidad pasa a EN_ADUANA")
    print(f"IVA de importación Q8,200 → crédito fiscal, no costo (capitalizable: {iva['capitalizable']})")

    paso(5, "Taller")
    orden = call("POST", "/ordenes", AUX, json={"unidad_id": u["id"], "tipo": "REACONDICIONAMIENTO",
                                                "descripcion": "Frenos, pintura de puerta y alineación",
                                                "responsable": "Jefe de taller", "fecha": "2026-10-12"})
    call("POST", f"/ordenes/{orden['id']}/mano-obra", AUX, json={"mecanico": "Pedro", "fecha": "2026-10-12", "horas": 10, "descripcion": "Frenos y alineación"})
    call("POST", f"/ordenes/{orden['id']}/mano-obra", AUX, json={"mecanico": "Julio", "fecha": "2026-10-12", "horas": 6, "descripcion": "Pintura"})
    print(f"La auxiliar intenta cerrar la orden → {intento('POST', f'/ordenes/{orden['id']}/cerrar', AUX, json={'fecha': '2026-10-12'})[0]}")
    cerrada = call("POST", f"/ordenes/{orden['id']}/cerrar", CONTADOR, json={"fecha": "2026-10-12"})
    print(f"El contador cierra la orden #{orden['id']}: 16 h × Q75 = {q(cerrada['costo_total'])} capitalizado")
    estado, _ = intento("POST", f"/ordenes/{orden['id']}/mano-obra", AUX,
                        json={"mecanico": "Pedro", "fecha": "2026-10-12", "horas": 1, "descripcion": "x"})
    print(f"Agregar horas a la orden cerrada → {estado}")

    paso(6, "Costo")
    hoja = call("GET", f"/unidades/{u['id']}/hoja-costo", CONTADOR)
    for comp in hoja["componentes"]:
        print(f"  {comp['grupo']:22} {q(comp['total_q']):>14}")
    print(f"  {'COSTO TOTAL':22} {q(hoja['costo_total']):>14}   cuadra con el mayor: {hoja['cuadra_con_mayor']}")

    paso(7, "Alta en flota")
    print(f"Alta antes de estar LISTA → {intento('POST', f'/unidades/{u['id']}/alta-flota', CONTADOR, json={'fecha': '2026-10-12'})[0]}")
    call("POST", f"/unidades/{u['id']}/estado", AUX, json={"estado": "LISTA", "documento": "Inspección final"})
    alta = call("POST", f"/unidades/{u['id']}/alta-flota", CONTADOR,
                json={"fecha": "2026-10-12", "vida_util_meses": 48, "valor_residual": 20000})
    print(f"Estado {alta['estado']}, costo de alta {q(alta['costo_alta'])}, vida útil 48 meses, residual Q20,000")
    proceso = call("GET", "/contabilidad/mayor/1.1.06", CONTADOR, params={"vin": u["vin"]})["saldo_final"]
    flota = call("GET", "/contabilidad/mayor/1.2.01", CONTADOR, params={"vin": u["vin"]})["saldo_final"]
    print(f"Unidades en proceso {q(proceso)} → Activo fijo flota {q(flota)}")

    paso(8, "Control: balance, mayor y bitácora por VIN")
    bal = call("GET", "/contabilidad/balance", CONTADOR)
    print(f"Balance: debe {q(bal['total_debe'])} = haber {q(bal['total_haber'])} → cuadra: {bal['cuadra']}")
    bit = call("GET", "/bitacora", CONTADOR, params={"vin": u["vin"], "entidad": "Unidad"})
    for r in reversed(bit):
        if r["accion"] == "MODIFICAR" and "estado" in (r["valores_nuevos"] or {}):
            print(f"  {r['usuario']:9} estado {r['valores_anteriores']['estado']:12} → {r['valores_nuevos']['estado']}")
    print(f"Registros de bitácora ligados al VIN: {len(call('GET', '/bitacora', CONTADOR, params={'vin': u['vin']}))}")

    paso(9, "Separación de funciones")
    p = call("POST", "/partidas", CONTADOR, json={"fecha": "2026-10-12", "concepto": "Aporte de capital", "lineas": [
        {"cuenta": "1.1.01", "lado": "DEBE", "monto": 50000}, {"cuenta": "3.1.01", "lado": "HABER", "monto": 50000}]})
    call("POST", f"/partidas/{p['id']}/enviar", CONTADOR)
    estado, detalle_ = intento("POST", f"/partidas/{p['id']}/contabilizar", CONTADOR)
    print(f"El contador intenta aprobar su propia partida → {estado}: {detalle_}")
    ok = call("POST", f"/partidas/{p['id']}/contabilizar", GERENTE)
    print(f"La gerente financiera la aprueba → partida No. {ok['numero']}")
    call("POST", "/auth/logout", AUX)
    print(f"La auxiliar cierra sesión; su token ya no sirve → {intento('GET', '/yo', AUX)[0]}")


def _hojas(nodos):
    for n in nodos:
        if n["es_detalle"]:
            yield n
        yield from _hojas(n["hijas"])


if __name__ == "__main__":
    main()
