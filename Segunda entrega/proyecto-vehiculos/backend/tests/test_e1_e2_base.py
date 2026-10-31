"""Tarea 1 · Base contable, multimoneda y seguridad (E1 y E2)."""

from tests.conftest import API, AUX, CONTADOR, F1, GERENCIA, GERENTE, vin


def partida(client, lineas, headers=AUX, fecha="2026-10-02", concepto="Aporte de capital"):
    return client.post(f"{API}/partidas", headers=headers, json={"fecha": fecha, "concepto": concepto, "lineas": lineas})


APORTE = [
    {"cuenta": "1.1.01", "lado": "DEBE", "monto": 100000},
    {"cuenta": "3.1.01", "lado": "HABER", "monto": 100000},
]


# ---------------------------------------------------------------- HU-1.09 Usuarios y roles

def test_hu_1_09_sin_sesion_no_hay_acceso(client):
    assert client.get(f"{API}/cuentas").status_code == 401
    assert client.get(f"{API}/cuentas", headers={"Authorization": "Bearer inventado"}).status_code == 401
    assert client.get(f"{API}/cuentas", headers={"X-Usuario": "contador"}).status_code == 401  # ya no hay atajo


def test_hu_1_09_login_con_contrasena_y_cierre_de_sesion(client):
    malo = client.post(f"{API}/auth/login", json={"usuario": "aux", "password": "otra"})
    assert malo.status_code == 401 and malo.json()["detail"] == "Usuario o contraseña incorrectos"
    assert client.post(f"{API}/auth/login", json={"usuario": "nadie", "password": "x"}).json()["detail"] == \
        "Usuario o contraseña incorrectos"
    r = client.post(f"{API}/auth/login", json={"usuario": "contador", "password": "Demo2026!"})
    token = {"Authorization": f"Bearer {r.json()['token']}"}
    assert r.json()["usuario"]["rol"] == "CONTADOR" and "password_hash" not in r.json()["usuario"]
    assert client.get(f"{API}/yo", headers=token).status_code == 200
    assert client.post(f"{API}/auth/logout", headers=token).status_code == 204
    assert client.get(f"{API}/yo", headers=token).status_code == 401


def test_hu_1_09_gerencia_solo_consulta_reportes(client):
    assert client.post(f"{API}/partidas", headers=GERENCIA, json={
        "fecha": "2026-10-02", "concepto": "x", "lineas": APORTE}).status_code == 403
    assert client.get(f"{API}/partidas", headers=GERENCIA).status_code == 403
    assert client.post(f"{API}/compras", headers=GERENCIA, json={}).status_code == 403
    assert client.get(f"{API}/tipos-cambio", headers=GERENCIA).status_code == 200


def test_hu_1_09_solo_gerente_financiero_crea_usuarios(client):
    nuevo = {"usuario": "aux2", "nombre": "Rosa Díaz", "rol": "AUXILIAR", "password": "Clave2026"}
    assert client.post(f"{API}/usuarios", json=nuevo, headers=CONTADOR).status_code == 403
    debil = client.post(f"{API}/usuarios", json={**nuevo, "password": "corta"}, headers=GERENTE)
    assert debil.status_code == 422 and "8 caracteres" in debil.json()["detail"]
    r = client.post(f"{API}/usuarios", json=nuevo, headers=GERENTE)
    assert r.status_code == 201 and r.json()["rol"] == "AUXILIAR"
    token = client.post(f"{API}/auth/login", json={"usuario": "aux2", "password": "Clave2026"}).json()["token"]
    assert client.get(f"{API}/yo", headers={"Authorization": f"Bearer {token}"}).json()["nombre"] == "Rosa Díaz"


# ---------------------------------------------------------------- HU-2.01 / HU-2.02 / HU-1.10

def test_hu_2_01_partida_nace_en_borrador_y_no_afecta_el_mayor(client):
    r = partida(client, APORTE)
    assert r.status_code == 201
    p = r.json()
    assert p["estado"] == "BORRADOR" and p["numero"] is None
    assert client.get(f"{API}/contabilidad/balance", headers=CONTADOR).json()["cuentas"] == []


def test_hu_2_01_partida_descuadrada_no_pasa_a_revision(client):
    p = partida(client, [{"cuenta": "1.1.01", "lado": "DEBE", "monto": 1000},
                         {"cuenta": "3.1.01", "lado": "HABER", "monto": 900}]).json()
    r = client.post(f"{API}/partidas/{p['id']}/enviar", headers=AUX)
    assert r.status_code == 422 and "diferencia de Q100.00" in r.json()["detail"]


def test_hu_2_02_y_hu_1_10_quien_registra_no_contabiliza(client):
    p = partida(client, APORTE, headers=CONTADOR).json()
    client.post(f"{API}/partidas/{p['id']}/enviar", headers=CONTADOR)
    r = client.post(f"{API}/partidas/{p['id']}/contabilizar", headers=CONTADOR)
    assert r.status_code == 403 and "separación de funciones" in r.json()["detail"]

    r = client.post(f"{API}/partidas/{p['id']}/contabilizar", headers=GERENTE)
    assert r.status_code == 200
    assert r.json()["estado"] == "CONTABILIZADA" and r.json()["numero"] == 1
    assert r.json()["contabilizada_por"] == "gerente"


def test_hu_2_02_el_auxiliar_no_contabiliza_y_se_puede_devolver(client):
    p = partida(client, APORTE).json()
    client.post(f"{API}/partidas/{p['id']}/enviar", headers=AUX)
    assert client.post(f"{API}/partidas/{p['id']}/contabilizar", headers=AUX).status_code == 403
    r = client.post(f"{API}/partidas/{p['id']}/devolver", json={"comentario": "Falta soporte"}, headers=CONTADOR)
    assert r.json()["estado"] == "DEVUELTA" and r.json()["comentario_revision"] == "Falta soporte"
    corregida = {"fecha": "2026-10-02", "concepto": "Aporte de capital (con acta)", "lineas": APORTE}
    assert client.put(f"{API}/partidas/{p['id']}", json=corregida, headers=CONTADOR).status_code == 403  # no es suya
    r = client.put(f"{API}/partidas/{p['id']}", json=corregida, headers=AUX)
    assert r.json()["estado"] == "BORRADOR" and r.json()["concepto"] == "Aporte de capital (con acta)"
    assert client.post(f"{API}/partidas/{p['id']}/enviar", headers=AUX).json()["estado"] == "EN_REVISION"
    client.post(f"{API}/partidas/{p['id']}/contabilizar", headers=CONTADOR)
    assert client.put(f"{API}/partidas/{p['id']}", json=corregida, headers=AUX).status_code == 409  # ya contabilizada


# ---------------------------------------------------------------- HU-1.02 / HU-1.04 Catálogo y dimensiones

def test_hu_1_02_cuentas_de_agrupacion_no_reciben_movimientos(client):
    r = partida(client, [{"cuenta": "1.1", "lado": "DEBE", "monto": 10}, {"cuenta": "3.1.01", "lado": "HABER", "monto": 10}])
    assert r.status_code == 422 and "agrupación" in r.json()["detail"]


def test_hu_1_04_cuenta_que_exige_vin(client):
    r = partida(client, [{"cuenta": "6.1.01", "lado": "DEBE", "monto": 500, "linea_negocio": "ALQUILER"},
                         {"cuenta": "1.1.01", "lado": "HABER", "monto": 500}])
    assert r.status_code == 422 and "exige el VIN" in r.json()["detail"]


def test_hu_1_02_crear_cuenta(client):
    datos = {"codigo": "6.1.03", "nombre": "Seguros de flota", "tipo": "GASTO", "naturaleza": "DEUDORA",
             "exige_vin": "OBLIGATORIO", "linea_defecto": "ALQUILER"}
    assert client.post(f"{API}/cuentas", json=datos, headers=AUX).status_code == 403
    assert client.post(f"{API}/cuentas", json=datos, headers=CONTADOR).status_code == 201
    assert client.post(f"{API}/cuentas", json=datos, headers=CONTADOR).status_code == 409


# ---------------------------------------------------------------- HU-1.06 / HU-1.07 Multimoneda

def test_hu_1_06_sin_tipo_de_cambio_no_se_registra_en_usd(client):
    r = partida(client, [{"cuenta": "1.1.02", "lado": "DEBE", "monto": 1000, "moneda": "USD"},
                         {"cuenta": "3.1.01", "lado": "HABER", "monto": 7700}])
    assert r.status_code == 422 and "No hay tipo de cambio" in r.json()["detail"]


def test_hu_1_07_linea_usd_guarda_original_tipo_de_cambio_y_quetzales(client):
    client.post(f"{API}/tipos-cambio", json={"fecha": "2026-10-02", "valor": 7.7}, headers=CONTADOR)
    p = partida(client, [{"cuenta": "1.1.02", "lado": "DEBE", "monto": 1000, "moneda": "USD"},
                         {"cuenta": "3.1.01", "lado": "HABER", "monto": 7700}]).json()
    usd = p["lineas"][0]
    assert (usd["monto_original"], usd["tipo_cambio"], usd["debe"]) == (1000, 7.7, 7700)


def test_hu_1_07_tipo_de_cambio_distinto_requiere_justificacion(client):
    client.post(f"{API}/tipos-cambio", json={"fecha": "2026-10-02", "valor": 7.7}, headers=CONTADOR)
    lineas = [{"cuenta": "1.1.02", "lado": "DEBE", "monto": 1000, "moneda": "USD", "tipo_cambio": 7.8},
              {"cuenta": "3.1.01", "lado": "HABER", "monto": 7800}]
    assert partida(client, lineas).status_code == 422
    r = client.post(f"{API}/partidas", headers=AUX, json={"fecha": "2026-10-02", "concepto": "Compra de divisas",
                                                          "lineas": lineas, "justificacion_tipo_cambio": "TC del banco"})
    assert r.status_code == 201 and r.json()["lineas"][0]["debe"] == 7800


def test_hu_1_07_tipo_de_cambio_personalizado_debe_ser_positivo(client):
    client.post(f"{API}/tipos-cambio", json={"fecha": "2026-10-02", "valor": 7.7}, headers=CONTADOR)
    for tc in (0, -7.8):
        r = client.post(f"{API}/partidas", headers=AUX, json={
            "fecha": "2026-10-02", "concepto": "x", "justificacion_tipo_cambio": "TC del banco", "lineas": [
                {"cuenta": "1.1.02", "lado": "DEBE", "monto": 1000, "moneda": "USD", "tipo_cambio": tc},
                {"cuenta": "3.1.01", "lado": "HABER", "monto": 7800}]})
        assert r.status_code == 422
    assert client.post(f"{API}/tipos-cambio", json={"fecha": "2026-10-03", "valor": -1}, headers=CONTADOR).status_code == 422


def test_hu_1_02_catalogo_jerarquico(client):
    arbol = client.get(f"{API}/cuentas/arbol", headers=AUX).json()
    activo = next(n for n in arbol if n["codigo"] == "1")
    corriente = next(n for n in activo["hijas"] if n["codigo"] == "1.1")
    assert "1.1.06" in [h["codigo"] for h in corriente["hijas"]]


def test_hu_1_06_tipo_de_cambio_usado_no_se_modifica(client, comprar):
    comprar()
    r = client.post(f"{API}/tipos-cambio", json={"fecha": F1, "valor": 7.9}, headers=CONTADOR)
    assert r.status_code == 409 and "aprobación del gerente financiero" in r.json()["detail"]


# ---------------------------------------------------------------- HU-1.05 VIN

def test_hu_1_05_vin_validado(client, tc, proveedores):
    base = {"proveedor_id": proveedores["subasta"]["id"], "fecha": F1, "numero_lote": "L1",
            "marca": "Toyota", "linea": "Corolla", "modelo_anio": 2020, "precio_usd": 7000}
    corto = client.post(f"{API}/compras", headers=AUX, json={**base, "vin": "1HGCM8263"})
    assert corto.status_code == 422 and "17 caracteres" in corto.json()["detail"]
    malo = vin(1)[:8] + ("0" if vin(1)[8] != "0" else "1") + vin(1)[9:]
    r = client.post(f"{API}/compras", headers=AUX, json={**base, "vin": malo})
    assert r.status_code == 422 and "dígito verificador" in r.json()["detail"]
    assert client.post(f"{API}/compras", headers=AUX, json={**base, "vin": vin(1)}).status_code == 201
    assert client.post(f"{API}/compras", headers=AUX, json={**base, "vin": vin(1).lower()}).status_code == 409


def test_hu_1_05_ficha_con_historial_y_movimientos(client, comprar):
    u = comprar()
    ficha = client.get(f"{API}/unidades/vin/{u['vin']}", headers=AUX).json()
    assert ficha["estado"] == "EN_TRANSITO"
    assert ficha["historial"][0]["estado_nuevo"] == "EN_TRANSITO" and ficha["historial"][0]["usuario"] == "aux"
    movs = client.get(f"{API}/contabilidad/mayor/1.1.06", params={"vin": u["vin"]}, headers=AUX).json()["movimientos"]
    assert movs[0]["origen_tipo"] == "COMPRA_UNIDAD"


# ---------------------------------------------------------------- HU-1.11 Bitácora / HU-2.16 Balance

def test_hu_1_11_bitacora_registra_y_no_se_puede_borrar(client, comprar):
    u = comprar()
    registros = client.get(f"{API}/bitacora", params={"vin": u["vin"]}, headers=CONTADOR).json()
    assert any(r["accion"] == "COMPRA" and r["usuario"] == "aux" for r in registros)
    assert client.delete(f"{API}/bitacora", headers=GERENTE).status_code == 405
    assert client.get(f"{API}/bitacora", headers=AUX).status_code == 403


def test_hu_1_11_auditoria_automatica_con_valores_anteriores_y_nuevos(client, comprar):
    u = comprar()
    client.post(f"{API}/unidades/{u['id']}/estado", json={"estado": "EN_ADUANA", "documento": "Arribo"}, headers=AUX)
    registros = client.get(f"{API}/bitacora", params={"vin": u["vin"], "entidad": "Unidad"}, headers=CONTADOR).json()
    alta = next(r for r in registros if r["accion"] == "CREAR")
    assert alta["usuario"] == "aux" and alta["valores_nuevos"]["estado"] == "EN_TRANSITO"
    cambio = next(r for r in registros if r["accion"] == "MODIFICAR")
    assert cambio["valores_anteriores"] == {"estado": "EN_TRANSITO"}
    assert cambio["valores_nuevos"] == {"estado": "EN_ADUANA"}


def test_hu_1_11_la_bitacora_no_expone_secretos(client):
    client.post(f"{API}/usuarios", headers=GERENTE, json={"usuario": "aux3", "nombre": "Leo", "rol": "AUXILIAR",
                                                          "password": "Secreta2026"})
    texto = str(client.get(f"{API}/bitacora", params={"entidad": "Usuario"}, headers=GERENTE).json())
    assert "aux3" in texto and "password" not in texto and "Secreta2026" not in texto and "pbkdf2" not in texto


def test_hu_2_03_documento_y_partida_se_confirman_juntos(client, tc, proveedores, sesiones):
    """Si la partida falla (cuenta inactiva), no queda ni la unidad ni la cuenta por pagar."""
    from sqlalchemy import update
    from app.models import Cuenta
    with sesiones["fabrica"]() as db:
        db.execute(update(Cuenta).where(Cuenta.codigo == "2.1.02").values(activa=False))
        db.commit()
    r = client.post(f"{API}/compras", headers=AUX, json={
        "proveedor_id": proveedores["subasta"]["id"], "fecha": F1, "numero_lote": "L1", "vin": vin(5),
        "marca": "Honda", "linea": "Civic", "modelo_anio": 2018, "precio_usd": 6000})
    assert r.status_code == 422 and "inactiva" in r.json()["detail"]
    assert client.get(f"{API}/unidades", headers=AUX).json() == []
    assert client.get(f"{API}/cuentas-por-pagar", headers=AUX).json() == []


def test_hu_2_16_balance_cuadra_y_filtra_por_vin(client, comprar):
    u1, u2 = comprar(1), comprar(2, precio=10000, cargos=0)
    bal = client.get(f"{API}/contabilidad/balance", headers=CONTADOR).json()
    assert bal["cuadra"] and bal["total_debe"] == round((8500 + 10000) * 7.70, 2)
    prov = next(c for c in bal["cuentas"] if c["codigo"] == "2.1.02")
    assert prov["saldo_usd"] == 18500  # columna en moneda original

    solo_u2 = client.get(f"{API}/contabilidad/balance", params={"vin": u2["vin"]}, headers=CONTADOR).json()
    assert next(c for c in solo_u2["cuentas"] if c["codigo"] == "1.1.06")["saldo"] == 77000
    assert solo_u2["cuadra"] is None and solo_u2["filtrado"]  # un subconjunto por VIN no se exige cuadrado
