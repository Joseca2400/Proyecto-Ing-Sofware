"""HU-3.05: tarifario de alquiler (tarifas con vigencia por tipo o unidad, temporadas, conceptos
con su tratamiento fiscal) y la cotización con IVA incluido y conversión de moneda."""

import pytest
from sqlalchemy import func, select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal

BASE = "/api/v1/alquileres"
VIN = "1HGCM82633A004352"

SEDAN_DIARIA = {
    "tipo_vehiculo": "sedan",
    "modalidad": "diaria",
    "moneda": "GTQ",
    "monto": "300.00",
    "km_incluido": 200,
    "costo_km_adicional": "2.50",
    "vigente_desde": "2026-01-01",
}


@pytest.fixture(autouse=True)
def tarifario_vacio():
    """Deja solo los conceptos de la carga inicial y borra tipos de cambio de prueba."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE tarifa_alquiler, temporada_alquiler RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM concepto_alquiler WHERE id > 6"))
        db.execute(text("UPDATE concepto_alquiler SET precio_sugerido = NULL, moneda = NULL, activo = true"))
        db.execute(text("DELETE FROM tipo_cambio WHERE fecha = '2026-03-02'"))
        db.commit()


def _tarifa(cliente, **cambios):
    respuesta = cliente.post(f"{BASE}/tarifas", json={**SEDAN_DIARIA, **cambios})
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def _concepto(cliente, nombre):
    return next(c for c in cliente.get(f"{BASE}/conceptos").json() if c["nombre"] == nombre)


def _cotizar(cliente, **datos):
    cuerpo = {
        "tipo_vehiculo": "sedan",
        "modalidad": "diaria",
        "moneda": "GTQ",
        "fecha_salida": "2026-03-02",
        "fecha_devolucion": "2026-03-05",
        **datos,
    }
    return cliente.post(f"{BASE}/cotizaciones", json=cuerpo)


# ── Tarifas ────────────────────────────────────────────────────────────────────


def test_registra_tarifa_por_tipo_de_vehiculo(cliente):
    tarifa = _tarifa(cliente)

    assert tarifa["tipo_vehiculo"] == "sedan"
    assert tarifa["vin"] is None
    assert tarifa["monto"] == "300.000000"
    assert tarifa["costo_km_adicional"] == "2.500000"
    assert tarifa["temporada"] is None


def test_registra_tarifa_de_excepcion_por_unidad(cliente):
    tarifa = _tarifa(cliente, tipo_vehiculo=None, vin=VIN.lower(), monto="450.00")

    assert tarifa["vin"] == VIN
    assert tarifa["tipo_vehiculo"] is None


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"tipo_vehiculo": None}, "Indique el tipo de vehículo o"),
        ({"vin": VIN}, "Indique el tipo de vehículo o"),
        ({"tipo_vehiculo": "tractor"}, "Tipo de vehículo desconocido"),
        ({"tipo_vehiculo": None, "vin": "123"}, "17 caracteres"),
        ({"monto": "0"}, "mayor que cero"),
        ({"monto": "300.555"}, "2 decimales"),
        (
            {"modalidad": "kilometraje", "km_incluido": None, "costo_km_adicional": None},
            "kilometraje requiere",
        ),
        ({"km_incluido": None}, "requiere indicar los kilómetros"),
        ({"temporada_id": 99}, "No existe la temporada"),
    ],
)
def test_valida_la_tarifa(cliente, cambios, mensaje):
    respuesta = cliente.post(f"{BASE}/tarifas", json={**SEDAN_DIARIA, **cambios})

    assert respuesta.status_code in (400, 404)
    assert mensaje in respuesta.json()["detail"]


def test_el_monto_se_envia_como_texto(cliente):
    assert cliente.post(f"{BASE}/tarifas", json={**SEDAN_DIARIA, "monto": 300}).status_code == 422


def test_un_cambio_de_tarifa_es_una_version_nueva_y_no_reescribe_fechas(cliente):
    _tarifa(cliente)
    _tarifa(cliente, monto="350.00", vigente_desde="2026-06-01")

    repetida = cliente.post(f"{BASE}/tarifas", json={**SEDAN_DIARIA, "vigente_desde": "2026-05-31"})
    assert repetida.status_code == 400
    assert "posterior a la de la tarifa actual (01/06/2026)" in repetida.json()["detail"]

    marzo = _cotizar(cliente).json()
    junio = _cotizar(cliente, fecha_salida="2026-06-10", fecha_devolucion="2026-06-11").json()
    assert marzo["lineas"][0]["precio_unitario"] == "300.00"
    assert junio["lineas"][0]["precio_unitario"] == "350.00"
    assert len(cliente.get(f"{BASE}/tarifas", params={"tipo_vehiculo": "sedan"}).json()) == 2


# ── Temporadas ─────────────────────────────────────────────────────────────────


def test_la_temporada_reemplaza_a_la_tarifa_base_en_sus_fechas(cliente):
    _tarifa(cliente)
    temporada = cliente.post(
        f"{BASE}/temporadas",
        json={"nombre": "Semana Santa", "fecha_inicio": "2026-03-29", "fecha_fin": "2026-04-05"},
    ).json()
    _tarifa(cliente, temporada_id=temporada["id"], monto="420.00")

    fuera = _cotizar(cliente).json()
    dentro = _cotizar(cliente, fecha_salida="2026-03-30", fecha_devolucion="2026-04-02").json()
    assert fuera["lineas"][0]["precio_unitario"] == "300.00"
    assert dentro["lineas"][0]["precio_unitario"] == "420.00"
    assert "Semana Santa" in dentro["lineas"][0]["descripcion"]

    cliente.post(f"{BASE}/temporadas/{temporada['id']}/desactivar")
    desactivada = _cotizar(cliente, fecha_salida="2026-03-30", fecha_devolucion="2026-04-02").json()
    assert desactivada["lineas"][0]["precio_unitario"] == "300.00"


def test_dos_temporadas_activas_no_se_traslapan(cliente):
    datos = {"nombre": "Navidad", "fecha_inicio": "2026-12-20", "fecha_fin": "2027-01-02"}
    assert cliente.post(f"{BASE}/temporadas", json=datos).status_code == 201

    respuesta = cliente.post(
        f"{BASE}/temporadas", json={**datos, "nombre": "Fin de año", "fecha_inicio": "2026-12-30"}
    )

    assert respuesta.status_code == 400
    assert "se traslapan con la temporada «Navidad»" in respuesta.json()["detail"]


# ── Conceptos ──────────────────────────────────────────────────────────────────


def test_la_carga_inicial_trae_los_conceptos_con_su_tratamiento_fiscal(cliente):
    deposito = _concepto(cliente, "Depósito en garantía")
    multa = _concepto(cliente, "Reintegro de multa de tránsito")
    gps = _concepto(cliente, "GPS")

    assert (deposito["naturaleza"], deposito["aplica_iva"], deposito["es_ingreso_acumulable"]) == (
        "deposito",
        False,
        False,
    )
    assert (multa["naturaleza"], multa["es_ingreso_acumulable"]) == ("reintegro", False)
    assert (gps["aplica_iva"], gps["es_ingreso_acumulable"]) == (True, True)


@pytest.mark.parametrize(
    ("datos", "mensaje", "status"),
    [
        ({"nombre": "Depósito VIP", "naturaleza": "deposito", "aplica_iva": True}, "Solo un ingreso", 400),
        ({"nombre": "Lavado", "naturaleza": "ingreso", "precio_sugerido": "50.00"}, "van juntos", 400),
        ({"nombre": "gps", "naturaleza": "ingreso", "aplica_iva": True}, "Ya existe", 409),
    ],
)
def test_valida_el_concepto(cliente, datos, mensaje, status):
    respuesta = cliente.post(f"{BASE}/conceptos", json=datos)

    assert respuesta.status_code == status
    assert mensaje in respuesta.json()["detail"]


def test_cambia_el_precio_del_concepto_y_queda_en_la_bitacora(cliente):
    gps = _concepto(cliente, "GPS")
    with SessionLocal() as db:
        desde = db.scalar(select(func.coalesce(func.max(RegistroBitacora.id), 0)))

    respuesta = cliente.put(
        f"{BASE}/conceptos/{gps['id']}", json={"precio_sugerido": "25.00", "moneda": "GTQ"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["precio_sugerido"] == "25.000000"
    with SessionLocal() as db:
        registro = db.scalars(
            select(RegistroBitacora).where(
                RegistroBitacora.id > desde, RegistroBitacora.entidad == "concepto_alquiler"
            )
        ).one()
    assert registro.accion == "modificar"
    assert registro.anteriores["precio_sugerido"] is None


# ── Cotización ─────────────────────────────────────────────────────────────────


def test_cotiza_con_iva_incluido_y_separa_depositos_y_reintegros(cliente):
    _tarifa(cliente)
    gps = _concepto(cliente, "GPS")
    deposito = _concepto(cliente, "Depósito en garantía")
    multa = _concepto(cliente, "Reintegro de multa de tránsito")
    cliente.put(f"{BASE}/conceptos/{gps['id']}", json={"precio_sugerido": "25.00", "moneda": "GTQ"})
    cliente.put(f"{BASE}/conceptos/{deposito['id']}", json={"precio_sugerido": "3000.00", "moneda": "GTQ"})

    respuesta = _cotizar(
        cliente,
        km_estimados=700,
        cargos=[
            {"concepto_id": gps["id"], "cantidad": 3},
            {"concepto_id": deposito["id"]},
            {"concepto_id": multa["id"], "precio": "150.00"},
        ],
    )

    assert respuesta.status_code == 200, respuesta.json()
    cuerpo = respuesta.json()
    assert cuerpo["dias"] == 3
    assert cuerpo["periodos"] == 3
    assert cuerpo["tipo_cambio"] is None
    alquiler, km, gps_linea, deposito_linea, multa_linea = cuerpo["lineas"]
    # Q900 con IVA incluido: base 900 / 1.12 = 803.57 e IVA 96.43.
    assert (alquiler["total"], alquiler["base"], alquiler["iva"]) == ("900.00", "803.57", "96.43")
    # 3 días × 200 km incluidos = 600; 100 km adicionales × Q2.50.
    assert (km["cantidad"], km["total"]) == ("100", "250.00")
    assert gps_linea["total"] == "75.00"
    assert (deposito_linea["naturaleza"], deposito_linea["iva"]) == ("deposito", "0.00")
    assert (multa_linea["naturaleza"], multa_linea["total"]) == ("reintegro", "150.00")
    assert cuerpo["total_ingresos"] == "1225.00"
    # El IVA se redondea por línea, como en la factura FEL: 96.43 + 26.79 + 8.04.
    assert cuerpo["total_iva"] == "131.26"
    assert cuerpo["total_depositos"] == "3000.00"
    assert cuerpo["total_reintegros"] == "150.00"
    assert cuerpo["total_a_pagar"] == "4375.00"


def test_la_tarifa_de_la_unidad_tiene_prioridad_sobre_la_del_tipo(cliente):
    _tarifa(cliente)
    _tarifa(cliente, tipo_vehiculo=None, vin=VIN, monto="450.00")

    con_vin = _cotizar(cliente, vin=VIN).json()
    otra_unidad = _cotizar(cliente, vin="2HGCM82633A004352").json()

    assert con_vin["lineas"][0]["precio_unitario"] == "450.00"
    assert otra_unidad["lineas"][0]["precio_unitario"] == "300.00"


@pytest.mark.parametrize(("modalidad", "periodos"), [("semanal", 2), ("mensual", 1)])
def test_los_periodos_se_redondean_hacia_arriba(cliente, modalidad, periodos):
    _tarifa(cliente, modalidad=modalidad, monto="1500.00")

    cuerpo = _cotizar(cliente, modalidad=modalidad, fecha_devolucion="2026-03-12").json()

    assert cuerpo["dias"] == 10
    assert cuerpo["periodos"] == periodos


def test_cotiza_en_dolares_convirtiendo_con_el_tipo_de_cambio(cliente):
    _tarifa(cliente)
    with SessionLocal() as db:
        db.execute(
            text("INSERT INTO tipo_cambio (fecha, valor, origen) VALUES ('2026-03-02', 7.75, 'manual')")
        )
        db.commit()

    cuerpo = _cotizar(cliente, moneda="USD").json()

    assert cuerpo["moneda"] == "USD"
    assert cuerpo["tipo_cambio"] == "7.75000000"
    assert cuerpo["lineas"][0]["precio_unitario"] == "38.71"  # 300 / 7.75 = 38.709…


def test_prefiere_la_tarifa_en_la_moneda_pedida(cliente):
    _tarifa(cliente)
    _tarifa(cliente, moneda="USD", monto="40.00")

    cuerpo = _cotizar(cliente, moneda="USD").json()

    assert cuerpo["tipo_cambio"] is None
    assert cuerpo["lineas"][0]["precio_unitario"] == "40.00"


@pytest.mark.parametrize(
    ("datos", "mensaje", "status"),
    [
        ({"moneda": "USD"}, "No hay tipo de cambio del 02/03/2026", 409),
        ({"modalidad": "mensual"}, "No hay tarifa mensual vigente", 404),
        ({"fecha_devolucion": "2026-03-01"}, "no puede ser anterior", 400),
    ],
)
def test_rechaza_cotizaciones_imposibles(cliente, datos, mensaje, status):
    _tarifa(cliente)

    respuesta = _cotizar(cliente, **datos)

    assert respuesta.status_code == status
    assert mensaje in respuesta.json()["detail"]


def test_un_cargo_sin_precio_en_el_tarifario_pide_su_monto(cliente):
    _tarifa(cliente)
    multa = _concepto(cliente, "Reintegro de multa de tránsito")

    respuesta = _cotizar(cliente, cargos=[{"concepto_id": multa["id"]}])

    assert respuesta.status_code == 400
    assert "Indique el monto" in respuesta.json()["detail"]


def test_la_tarifa_por_kilometraje_cobra_el_exceso(cliente):
    _tarifa(cliente, modalidad="kilometraje", monto="500.00", km_incluido=300, costo_km_adicional="3.00")

    sin_km = _cotizar(cliente, modalidad="kilometraje")
    cuerpo = _cotizar(cliente, modalidad="kilometraje", km_estimados=350).json()

    assert sin_km.status_code == 400
    assert cuerpo["periodos"] == 1
    assert cuerpo["lineas"][1]["total"] == "150.00"
    assert cuerpo["total_ingresos"] == "650.00"
