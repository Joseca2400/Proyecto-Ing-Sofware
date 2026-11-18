"""HU-3.06: contrato de alquiler (disponibilidad, estado "alquilada", tarifa copiada, monto estimado)."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.alquileres import service
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL = f"{API}/alquileres/contratos"
URL_TARIFAS = f"{API}/alquileres/tarifas"
VIN = "1HGCM82633A004352"
OTRO_VIN = "JHMCM56557C404453"

TARIFA = {
    "tipo_vehiculo": "sedan",
    "modalidad": "diaria",
    "moneda": "GTQ",
    "monto": "350.00",
    "km_incluido": 150,
    "precio_km_adicional": "2.50",
    "vigente_desde": "2026-01-01",
}
CLIENTE = {
    "tipo": "individual",
    "nombre": "María López",
    "tipo_identificacion": "cui",
    "identificacion": "2547 12345 0101",
}


def _unidad(vin: str, estado: str = "en_flota") -> dict:
    return {
        "vin": vin,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "linea_negocio": "alquiler",
        "estado": estado,
    }


def _contrato(cliente_id: int, **cambios) -> dict:
    return {
        "cliente_id": cliente_id,
        "vin": VIN,
        "salida": "2026-11-10T09:00:00-06:00",
        "devolucion_prevista": "2026-11-13",
        "modalidad": "diaria",
        "moneda": "GTQ",
        "km_salida": 42000,
        "combustible_salida": 8,
        "deposito_esperado": "2000.00",
        **cambios,
    }


@pytest.fixture(autouse=True)
def datos_base(cliente_contador):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE unidad, tarifa, cliente RESTART IDENTITY CASCADE"))
        db.commit()
    for vin in (VIN, OTRO_VIN):
        assert cliente_contador.post(f"{API}/unidades", json=_unidad(vin)).status_code == 201
    assert cliente_contador.post(URL_TARIFAS, json=TARIFA).status_code == 201


@pytest.fixture
def cliente_id(cliente_contador) -> int:
    return cliente_contador.post(f"{API}/facturacion/clientes", json=CLIENTE).json()["id"]


def _estado(cliente, vin: str = VIN) -> str:
    return cliente.get(f"{API}/unidades/{vin}").json()["estado"]


def _cambiar(cliente, estado: str, vin: str = VIN):
    return cliente.post(f"{API}/unidades/{vin}/estado", json={"estado": estado, "documento": "Memo"})


def test_registra_el_contrato_y_la_unidad_pasa_a_alquilada(cliente_contador, cliente_id):
    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id))

    assert respuesta.status_code == 201
    contrato = respuesta.json()
    assert contrato["numero"] == 1
    assert contrato["estado"] == "abierto"
    assert (contrato["modalidad"], contrato["moneda"], contrato["tarifa_monto"]) == (
        "diaria",
        "GTQ",
        "350.000000",
    )
    assert (contrato["km_incluido"], contrato["precio_km_adicional"]) == (150, "2.500000")
    assert contrato["dias_previstos"] == 3
    assert contrato["monto_estimado"] == "1050.000000"
    assert contrato["deposito_esperado"] == "2000.000000"
    assert _estado(cliente_contador) == "alquilada"
    historial = cliente_contador.get(f"{API}/unidades/{VIN}/historial").json()
    assert (historial[-1]["estado_anterior"], historial[-1]["estado_nuevo"]) == ("en_flota", "alquilada")
    assert historial[-1]["documento"] == "Contrato de alquiler 1"
    assert cliente_contador.get(f"{URL}/{contrato['id']}").json()["numero"] == 1


def test_el_numero_es_correlativo(cliente_contador, cliente_id):
    cliente_contador.post(URL, json=_contrato(cliente_id))
    segundo = cliente_contador.post(URL, json=_contrato(cliente_id, vin=OTRO_VIN)).json()

    assert segundo["numero"] == 2
    assert [c["numero"] for c in cliente_contador.get(URL).json()] == [2, 1]
    assert len(cliente_contador.get(URL, params={"vin": OTRO_VIN}).json()) == 1


def test_una_unidad_alquilada_no_se_vuelve_a_alquilar(cliente_contador, cliente_id):
    cliente_contador.post(URL, json=_contrato(cliente_id))

    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id))

    assert respuesta.status_code == 409
    assert "no está disponible: su estado es alquilada" in respuesta.json()["detail"]


@pytest.mark.parametrize("estado", ["en_taller", "en_venta"])
def test_una_unidad_fuera_de_flota_no_se_alquila(cliente_contador, cliente_id, estado):
    assert _cambiar(cliente_contador, estado).status_code == 200

    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id))

    assert respuesta.status_code == 409
    assert f"su estado es {estado}" in respuesta.json()["detail"]


def test_una_unidad_en_importacion_no_se_alquila(cliente_contador, cliente_id):
    cliente_contador.post(f"{API}/unidades", json=_unidad("1M8GDM9AXKP042788", estado="en_transito"))

    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id, vin="1M8GDM9AXKP042788"))

    assert respuesta.status_code == 409


def test_no_se_alquila_si_tiene_otro_contrato_abierto(cliente_contador, cliente_id):
    cliente_contador.post(URL, json=_contrato(cliente_id))
    assert _cambiar(cliente_contador, "en_flota").status_code == 200  # cambio manual: sigue el contrato

    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id, salida="2026-11-12T09:00:00-06:00"))

    assert respuesta.status_code == 409
    assert "ya tiene abierto el contrato 1" in respuesta.json()["detail"]


def test_la_tarifa_se_copia_y_no_cambia_con_el_tarifario(cliente_contador, cliente_id):
    contrato = cliente_contador.post(URL, json=_contrato(cliente_id)).json()

    nueva = {**TARIFA, "monto": "400.00", "km_incluido": 100, "vigente_desde": "2026-11-15"}
    assert cliente_contador.post(URL_TARIFAS, json=nueva).status_code == 201

    guardado = cliente_contador.get(f"{URL}/{contrato['id']}").json()
    assert (guardado["tarifa_monto"], guardado["km_incluido"]) == ("350.000000", 150)
    assert guardado["monto_estimado"] == "1050.000000"
    posterior = cliente_contador.post(
        URL,
        json=_contrato(
            cliente_id, vin=OTRO_VIN, salida="2026-11-16T08:00:00-06:00", devolucion_prevista="2026-11-17"
        ),
    ).json()
    assert (posterior["tarifa_monto"], posterior["monto_estimado"]) == ("400.000000", "400.000000")


def test_monto_estimado_semanal(cliente_contador, cliente_id):
    cliente_contador.post(URL_TARIFAS, json={**TARIFA, "modalidad": "semanal", "monto": "2000"})

    contrato = cliente_contador.post(
        URL, json=_contrato(cliente_id, modalidad="semanal", devolucion_prevista="2026-11-20")
    ).json()

    assert contrato["dias_previstos"] == 10
    assert contrato["monto_estimado"] == "4000.000000"  # dos semanas iniciadas


@pytest.mark.parametrize(
    ("modalidad", "dias", "periodos"),
    [
        ("diaria", 1, 1),
        ("diaria", 5, 5),
        ("semanal", 7, 1),
        ("semanal", 8, 2),
        ("mensual", 30, 1),
        ("mensual", 31, 2),
        ("por_kilometraje", 45, 1),
    ],
)
def test_periodos_por_modalidad(modalidad, dias, periodos):
    assert service._periodos(modalidad, dias) == periodos


def test_devolucion_el_mismo_dia_cuenta_un_dia(cliente_contador, cliente_id):
    contrato = cliente_contador.post(URL, json=_contrato(cliente_id, devolucion_prevista="2026-11-10")).json()

    assert (contrato["dias_previstos"], contrato["monto_estimado"]) == (1, "350.000000")


@pytest.mark.parametrize(
    ("cambio", "estado", "mensaje"),
    [
        ({"devolucion_prevista": "2026-11-09"}, 400, "antes de la salida"),
        ({"salida": "2099-01-01T09:00:00-06:00", "devolucion_prevista": "2099-01-05"}, 400, "día futuro"),
        ({"moneda": "USD"}, 404, "No hay tarifa diaria en USD"),
        ({"cliente_id": 999}, 404, "El cliente no existe"),
        ({"vin": "1M8GDM9AXKP042788"}, 404, "No existe la unidad"),
        ({"deposito_esperado": "-5"}, 400, "no puede ser negativo"),
    ],
)
def test_rechaza_datos_invalidos(cliente_contador, cliente_id, cambio, estado, mensaje):
    respuesta = cliente_contador.post(URL, json={**_contrato(cliente_id), **cambio})

    assert respuesta.status_code == estado
    assert mensaje in respuesta.json()["detail"]
    assert _estado(cliente_contador) == "en_flota"


def test_combustible_en_octavos(cliente_contador, cliente_id):
    assert cliente_contador.post(URL, json=_contrato(cliente_id, combustible_salida=9)).status_code == 422


def test_si_falla_el_cambio_de_estado_no_queda_el_contrato(cliente_contador, cliente_id, monkeypatch):
    def falla(*_args, **_kwargs):
        raise ErrorNegocio("Fallo simulado")

    monkeypatch.setattr(service.unidades, "cambiar_estado", falla)

    assert cliente_contador.post(URL, json=_contrato(cliente_id)).status_code == 400
    assert cliente_contador.get(URL).json() == []


# ── Transiciones del estado "alquilada" (módulo unidades) ──────────────────────


def test_transiciones_del_estado_alquilada(cliente_contador, cliente_id):
    assert _cambiar(cliente_contador, "en_venta", OTRO_VIN).status_code == 200
    rechazo = _cambiar(cliente_contador, "alquilada", OTRO_VIN)
    assert "Solo una unidad en flota puede alquilarse" in rechazo.json()["detail"]

    cliente_contador.post(URL, json=_contrato(cliente_id))
    rechazo = _cambiar(cliente_contador, "en_venta")
    assert "solo puede volver a la flota o pasar al taller" in rechazo.json()["detail"]
    assert _cambiar(cliente_contador, "en_taller").status_code == 200

    alta = cliente_contador.post(f"{API}/unidades", json=_unidad("1M8GDM9AXKP042788", estado="alquilada"))
    assert alta.status_code == 400


# ── HU-3.08: cierre ───────────────────────────────────────────────────────────

CIERRE = {
    "devolucion": "2026-11-13T09:00:00-06:00",
    "km_devolucion": 42600,
    "combustible_devolucion": 5,
    "observaciones_danos": "Rayón en la puerta trasera izquierda",
}


@pytest.fixture
def contrato_id(cliente_contador, cliente_id) -> int:
    return cliente_contador.post(URL, json=_contrato(cliente_id)).json()["id"]


def _cerrar(cliente, contrato_id: int, **cambios):
    return cliente.post(f"{URL}/{contrato_id}/cierre", json={**CIERRE, **cambios})


def test_cierra_el_contrato_con_su_calculo(cliente_contador, contrato_id):
    respuesta = _cerrar(cliente_contador, contrato_id)

    assert respuesta.status_code == 200
    cierre = respuesta.json()
    assert cierre["estado"] == "cerrado"
    assert cierre["dias_efectivos"] == 3
    assert cierre["km_recorridos"] == 600
    assert cierre["km_excedentes"] == 150  # 600 − 150 km × 3 días
    assert cierre["combustible_faltante"] == 3
    assert cierre["monto_final"] == "1425.000000"  # 3 × 350 + 150 × 2.50
    assert cierre["observaciones_danos"] == "Rayón en la puerta trasera izquierda"


def test_al_cerrar_la_unidad_vuelve_a_la_flota_con_su_kilometraje(cliente_contador, contrato_id):
    _cerrar(cliente_contador, contrato_id)

    unidad = cliente_contador.get(f"{API}/unidades/{VIN}").json()
    assert (unidad["estado"], unidad["kilometraje"]) == ("en_flota", 42600)
    historial = cliente_contador.get(f"{API}/unidades/{VIN}/historial").json()
    assert (historial[-1]["estado_anterior"], historial[-1]["estado_nuevo"]) == ("alquilada", "en_flota")


@pytest.mark.parametrize(
    ("devolucion", "dias"),
    [
        ("2026-11-10T10:00:00-06:00", 1),  # el mismo día cuenta uno
        ("2026-11-13T08:30:00-06:00", 3),
        ("2026-11-13T10:00:00-06:00", 4),  # un periodo de 24 horas iniciado cuenta completo
    ],
)
def test_dias_efectivos(cliente_contador, contrato_id, devolucion, dias):
    cierre = _cerrar(cliente_contador, contrato_id, devolucion=devolucion, km_devolucion=42000).json()

    assert cierre["dias_efectivos"] == dias
    assert cierre["km_excedentes"] == 0
    assert cierre["monto_final"] == f"{350 * dias}.000000"


def test_combustible_de_mas_no_es_faltante(cliente_contador, contrato_id):
    assert (
        _cerrar(cliente_contador, contrato_id, combustible_devolucion=8).json()["combustible_faltante"] == 0
    )


def test_un_contrato_cerrado_no_se_vuelve_a_cerrar(cliente_contador, contrato_id):
    _cerrar(cliente_contador, contrato_id)

    respuesta = _cerrar(cliente_contador, contrato_id, km_devolucion=50000)

    assert respuesta.status_code == 409
    assert "ya está cerrado" in respuesta.json()["detail"]
    assert cliente_contador.get(f"{URL}/{contrato_id}").json()["km_devolucion"] == 42600


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"km_devolucion": 41999}, "menor que el de salida"),
        ({"devolucion": "2026-11-10T08:00:00-06:00"}, "antes de la salida"),
        ({"devolucion": "2099-01-01T08:00:00-06:00"}, "en el futuro"),
    ],
)
def test_rechaza_cierres_invalidos(cliente_contador, contrato_id, cambio, mensaje):
    respuesta = _cerrar(cliente_contador, contrato_id, **cambio)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert _estado(cliente_contador) == "alquilada"


def test_la_devolucion_exige_zona_horaria(cliente_contador, contrato_id):
    assert _cerrar(cliente_contador, contrato_id, devolucion="2026-11-13T09:00:00").status_code == 422


def test_el_kilometraje_de_la_unidad_no_retrocede(cliente_contador, cliente_id, contrato_id):
    _cerrar(cliente_contador, contrato_id)

    respuesta = cliente_contador.post(URL, json=_contrato(cliente_id, km_salida=42000))

    assert respuesta.status_code == 400
    assert "menor que el de la unidad (42600 km)" in respuesta.json()["detail"]


def test_si_falla_la_unidad_el_contrato_sigue_abierto(cliente_contador, contrato_id, monkeypatch):
    def falla(*_args, **_kwargs):
        raise ErrorNegocio("Fallo simulado")

    monkeypatch.setattr(service.unidades, "fijar_kilometraje", falla)

    assert _cerrar(cliente_contador, contrato_id).status_code == 400
    assert cliente_contador.get(f"{URL}/{contrato_id}").json()["estado"] == "abierto"
    assert _estado(cliente_contador) == "alquilada"


def test_una_unidad_enviada_al_taller_se_queda_en_taller(cliente_contador, contrato_id):
    _cambiar(cliente_contador, "en_taller")

    assert _cerrar(cliente_contador, contrato_id).status_code == 200
    assert _estado(cliente_contador) == "en_taller"


def test_resumen_para_facturar(cliente_contador, cliente_id, contrato_id):
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="no está cerrado"):
        service.resumen_para_facturar(db, contrato_id)
    _cerrar(cliente_contador, contrato_id)

    with SessionLocal() as db:
        resumen = service.resumen_para_facturar(db, contrato_id)

    assert {k: resumen[k] for k in ("cliente_id", "moneda", "vin", "linea_negocio")} == {
        "cliente_id": cliente_id,
        "moneda": "GTQ",
        "vin": VIN,
        "linea_negocio": "alquiler",
    }
    assert [(linea["cantidad"], linea["precio_unitario"]) for linea in resumen["lineas"]] == [
        (Decimal(3), Decimal("350")),
        (Decimal(150), Decimal("2.5")),
    ]
    assert "contrato 1" in resumen["lineas"][0]["descripcion"]


# ── Permisos ──────────────────────────────────────────────────────────────────


def test_sin_sesion_responde_401(cliente):
    assert cliente.get(URL).status_code == 401
    assert cliente.post(URL, json=_contrato(1)).status_code == 401
    assert cliente.post(f"{URL}/1/cierre", json=CIERRE).status_code == 401


def test_gerencia_no_cierra(cliente, contrato_id):
    token = cliente.post(
        f"{API}/seguridad/login", json={"correo": "gerencia@empresa.gt", "clave": CLAVE_PRUEBAS}
    ).json()["token"]

    respuesta = cliente.post(
        f"{URL}/{contrato_id}/cierre", json=CIERRE, headers={"Authorization": f"Bearer {token}"}
    )

    assert respuesta.status_code == 403


def test_auxiliar_registra_y_gerencia_solo_consulta(cliente, cliente_id):
    def sesion(correo):
        token = cliente.post(
            f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}
        ).json()["token"]
        return {"Authorization": f"Bearer {token}"}

    gerencia = sesion("gerencia@empresa.gt")
    assert cliente.post(URL, json=_contrato(cliente_id), headers=gerencia).status_code == 403
    assert (
        cliente.post(URL, json=_contrato(cliente_id), headers=sesion("auxiliar@empresa.gt")).status_code
        == 201
    )
    assert cliente.get(URL, headers=gerencia).status_code == 200
