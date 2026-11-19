"""HU-3.07: depósitos en garantía (pasivo con su partida, aplicación, devolución y saldo vigente)."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.modulos.alquileres import service
from app.modulos.configuracion import service as configuracion
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
URL_CONTRATOS = f"{API}/alquileres/contratos"
URL = f"{API}/alquileres/depositos"
VIN = "1HGCM82633A004352"
FECHA = "2026-11-10"

TARIFA = {
    "tipo_vehiculo": "sedan",
    "modalidad": "diaria",
    "moneda": "GTQ",
    "monto": "350.00",
    "km_incluido": 150,
    "precio_km_adicional": "2.50",
    "vigente_desde": "2026-01-01",
}
CIERRE = {"devolucion": "2026-11-13T09:00:00-06:00", "km_devolucion": 42600, "combustible_devolucion": 5}


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


@pytest.fixture(autouse=True)
def datos_base(cliente) -> dict[str, int]:
    """Unidad en flota, tarifas, cliente, tipo de cambio y una cuenta bancaria por moneda."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(
            text("TRUNCATE unidad, tarifa, cliente, partida, cuenta_bancaria RESTART IDENTITY CASCADE")
        )
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
        bancos = {
            moneda: configuracion.crear_cuenta_bancaria(
                db,
                "Banco Industrial",
                f"000-{moneda}",
                "monetaria",
                moneda,
                configuracion.buscar_cuenta(db, codigo).id,
            ).id
            for moneda, codigo in (("GTQ", "1.1.01.02"), ("USD", "1.1.01.03"))
        }
    unidad = {
        "vin": VIN,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "linea_negocio": "alquiler",
        "estado": "en_flota",
    }
    assert cliente.post(f"{API}/unidades", json=unidad).status_code == 201
    assert cliente.post(f"{API}/alquileres/tarifas", json=TARIFA).status_code == 201
    usd = {**TARIFA, "moneda": "USD", "monto": "50.00", "precio_km_adicional": "0.30"}
    assert cliente.post(f"{API}/alquileres/tarifas", json=usd).status_code == 201
    assert (
        cliente.post(f"{API}/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": "7.75"}).status_code
        == 201
    )
    persona = {
        "tipo": "individual",
        "nombre": "María López",
        "tipo_identificacion": "cui",
        "identificacion": "2547 12345 0101",
    }
    cliente_id = cliente.post(f"{API}/facturacion/clientes", json=persona).json()["id"]
    return {"cliente_id": cliente_id, **bancos}


def _contrato(cliente, datos_base, moneda: str = "GTQ") -> int:
    cuerpo = {
        "cliente_id": datos_base["cliente_id"],
        "vin": VIN,
        "salida": "2026-11-10T09:00:00-06:00",
        "devolucion_prevista": "2026-11-13",
        "modalidad": "diaria",
        "moneda": moneda,
        "km_salida": 42000,
        "combustible_salida": 8,
        "deposito_esperado": "2000.00",
    }
    respuesta = cliente.post(URL_CONTRATOS, json=cuerpo)
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


@pytest.fixture
def contrato_id(cliente, datos_base) -> int:
    return _contrato(cliente, datos_base)


def _depositar(cliente, contrato_id: int, banco: int | None, **cambios):
    cuerpo = {
        "tipo": "deposito",
        "fecha": FECHA,
        "moneda": "GTQ",
        "monto": "2000.00",
        "cuenta_bancaria_id": banco,
    }
    return cliente.post(f"{URL_CONTRATOS}/{contrato_id}/depositos", json={**cuerpo, **cambios})


def _cerrar(cliente, contrato_id: int):
    assert cliente.post(f"{URL_CONTRATOS}/{contrato_id}/cierre", json=CIERRE).status_code == 200


def _partida(documento_tipo: str, documento_id: int) -> list[tuple]:
    """Líneas de la partida: (cuenta, debe, haber, moneda, monto en USD, línea de negocio, VIN)."""
    with SessionLocal() as db:
        filas = db.execute(
            text(
                """
                SELECT c.codigo, l.debe, l.haber, l.moneda, l.monto_usd, l.linea_negocio, l.vin
                FROM linea_partida l
                JOIN partida p ON p.id = l.partida_id
                JOIN cuentas c ON c.id = l.cuenta_id
                WHERE p.documento_tipo = :tipo AND p.documento_id = :id AND p.estado = 'contabilizada'
                ORDER BY l.numero_linea
                """
            ),
            {"tipo": documento_tipo, "id": str(documento_id)},
        )
        return [tuple(fila) for fila in filas]


def _movimiento(deposito_id: int, tipo: str) -> int:
    with SessionLocal() as db:
        return db.scalar(
            text("SELECT id FROM movimiento_deposito WHERE deposito_id = :id AND tipo = :tipo"),
            {"id": deposito_id, "tipo": tipo},
        )


# ── Recepción (criterios 1 y 2) ───────────────────────────────────────────────


def test_el_deposito_en_quetzales_es_pasivo_con_su_partida(cliente, datos_base, contrato_id):
    respuesta = _depositar(cliente, contrato_id, datos_base["GTQ"])

    assert respuesta.status_code == 201
    deposito = respuesta.json()
    assert (deposito["saldo"], deposito["vin"], deposito["contrato_numero"]) == ("2000.000000", VIN, 1)
    assert _partida("deposito_garantia", deposito["id"]) == [
        ("1.1.01.02", Decimal("2000"), 0, "GTQ", None, "alquiler", None),
        ("2.1.03", 0, Decimal("2000"), "GTQ", None, "alquiler", VIN),
    ]


def test_el_deposito_en_dolares_va_en_dolares_en_los_dos_lados(cliente, datos_base, contrato_id):
    deposito = _depositar(cliente, contrato_id, datos_base["USD"], moneda="USD", monto="300").json()

    assert _partida("deposito_garantia", deposito["id"]) == [
        ("1.1.01.03", Decimal("2325"), 0, "USD", Decimal("300"), "alquiler", None),
        ("2.1.04", 0, Decimal("2325"), "USD", Decimal("300"), "alquiler", VIN),
    ]


def test_la_autorizacion_de_tarjeta_es_solo_referencia(cliente, contrato_id):
    respuesta = _depositar(cliente, contrato_id, None, tipo="autorizacion_tarjeta", referencia="AUT-778812")

    assert respuesta.status_code == 201
    autorizacion = respuesta.json()
    assert (autorizacion["saldo"], autorizacion["referencia"]) == ("0.000000", "AUT-778812")
    assert _partida("deposito_garantia", autorizacion["id"]) == []
    assert cliente.get(URL).json()["depositos"] == []
    assert len(cliente.get(f"{URL_CONTRATOS}/{contrato_id}/depositos").json()) == 1


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"cuenta_bancaria_id": None}, "Indique la cuenta bancaria"),
        ({"moneda": "USD"}, "es en GTQ, no en USD"),
        ({"tipo": "autorizacion_tarjeta"}, "lleva su referencia"),
        ({"monto": "0"}, "mayor que cero"),
        ({"fecha": "2099-01-01"}, "no puede ser futura"),
    ],
)
def test_rechaza_depositos_invalidos(cliente, datos_base, contrato_id, cambio, mensaje):
    respuesta = _depositar(cliente, contrato_id, datos_base["GTQ"], **cambio)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_sin_regla_de_contabilizacion_no_queda_el_deposito(cliente, datos_base, contrato_id):
    def regla(codigo: str | None) -> None:
        with SessionLocal() as db:
            db.execute(
                text(
                    "UPDATE regla_contabilizacion SET cuenta_codigo = :codigo"
                    " WHERE documento_tipo = 'deposito_garantia' AND concepto = 'pasivo_gtq'"
                ),
                {"codigo": codigo},
            )
            db.commit()

    regla(None)
    try:
        respuesta = _depositar(cliente, contrato_id, datos_base["GTQ"])
    finally:
        regla("2.1.03")

    assert respuesta.status_code == 409
    assert "deposito_garantia · pasivo_gtq" in respuesta.json()["detail"]
    assert cliente.get(f"{URL_CONTRATOS}/{contrato_id}/depositos").json() == []


def test_sin_tipo_de_cambio_no_queda_el_deposito_en_dolares(cliente, datos_base, contrato_id):
    respuesta = _depositar(
        cliente, contrato_id, datos_base["USD"], moneda="USD", monto="300", fecha="2026-11-09"
    )

    assert respuesta.status_code == 409
    assert cliente.get(f"{URL_CONTRATOS}/{contrato_id}/depositos").json() == []
    assert _partida("deposito_garantia", 1) == []


def test_no_se_recibe_deposito_con_el_contrato_cerrado(cliente, datos_base, contrato_id):
    _cerrar(cliente, contrato_id)

    respuesta = _depositar(cliente, contrato_id, datos_base["GTQ"])

    assert respuesta.status_code == 400
    assert "está cerrado" in respuesta.json()["detail"]


# ── Aplicación y devolución (criterios 3 y 4) ─────────────────────────────────


def _aplicar(cliente, deposito_id: int, monto: str):
    return cliente.post(f"{URL}/{deposito_id}/aplicacion", json={"fecha": FECHA, "monto": monto})


def _devolver(cliente, deposito_id: int, monto: str, banco: int):
    return cliente.post(
        f"{URL}/{deposito_id}/devolucion", json={"fecha": FECHA, "monto": monto, "cuenta_bancaria_id": banco}
    )


def test_aplica_a_los_cargos_y_devuelve_el_resto(cliente, datos_base, contrato_id):
    deposito_id = _depositar(cliente, contrato_id, datos_base["GTQ"]).json()["id"]
    _cerrar(cliente, contrato_id)  # monto final 1425.00

    aplicado = _aplicar(cliente, deposito_id, "1425.00")
    assert aplicado.status_code == 200
    assert aplicado.json()["saldo"] == "575.000000"
    assert _partida("aplicacion_deposito", _movimiento(deposito_id, "aplicacion")) == [
        ("2.1.03", Decimal("1425"), 0, "GTQ", None, "alquiler", VIN),
        ("1.1.02.01", 0, Decimal("1425"), "GTQ", None, "alquiler", None),
    ]

    devuelto = _devolver(cliente, deposito_id, "575.00", datos_base["GTQ"])
    assert devuelto.status_code == 200
    assert (devuelto.json()["saldo"], devuelto.json()["devuelto"]) == ("0.000000", True)
    assert _partida("devolucion_deposito", _movimiento(deposito_id, "devolucion")) == [
        ("2.1.03", Decimal("575"), 0, "GTQ", None, "alquiler", VIN),
        ("1.1.01.02", 0, Decimal("575"), "GTQ", None, "alquiler", None),
    ]
    assert cliente.get(URL).json()["depositos"] == []


def test_aplicacion_en_dolares_contra_clientes_en_dolares(cliente, datos_base):
    contrato_id = _contrato(cliente, datos_base, moneda="USD")
    deposito_id = _depositar(cliente, contrato_id, datos_base["USD"], moneda="USD", monto="300").json()["id"]
    _cerrar(cliente, contrato_id)  # 3 × 50 + 150 km × 0.30 = 195.00

    assert _aplicar(cliente, deposito_id, "195").status_code == 200
    assert _partida("aplicacion_deposito", _movimiento(deposito_id, "aplicacion")) == [
        ("2.1.04", Decimal("1511.25"), 0, "USD", Decimal("195"), "alquiler", VIN),
        ("1.1.02.02", 0, Decimal("1511.25"), "USD", Decimal("195"), "alquiler", None),
    ]


def test_un_deposito_no_se_devuelve_dos_veces(cliente, datos_base, contrato_id):
    deposito_id = _depositar(cliente, contrato_id, datos_base["GTQ"]).json()["id"]
    _cerrar(cliente, contrato_id)
    assert _devolver(cliente, deposito_id, "1000", datos_base["GTQ"]).status_code == 200

    respuesta = _devolver(cliente, deposito_id, "500", datos_base["GTQ"])

    assert respuesta.status_code == 409
    assert "no se puede devolver dos veces" in respuesta.json()["detail"]
    assert cliente.get(f"{URL_CONTRATOS}/{contrato_id}/depositos").json()[0]["saldo"] == "1000.000000"


@pytest.mark.parametrize(
    ("accion", "monto", "mensaje"),
    [
        ("aplicar", "1500", "monto final del contrato"),
        ("aplicar", "2000.01", "excede el saldo"),
        ("devolver", "2000.01", "excede el saldo"),
    ],
)
def test_nunca_mas_que_el_saldo_ni_que_el_monto_final(
    cliente, datos_base, contrato_id, accion, monto, mensaje
):
    deposito_id = _depositar(cliente, contrato_id, datos_base["GTQ"]).json()["id"]
    _cerrar(cliente, contrato_id)

    if accion == "aplicar":
        respuesta = _aplicar(cliente, deposito_id, monto)
    else:
        respuesta = _devolver(cliente, deposito_id, monto, datos_base["GTQ"])

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert _partida("aplicacion_deposito", 1) == []


def test_lo_aplicado_entre_depositos_no_excede_el_monto_final(cliente, datos_base, contrato_id):
    primero = _depositar(cliente, contrato_id, datos_base["GTQ"], monto="1000").json()["id"]
    segundo = _depositar(cliente, contrato_id, datos_base["GTQ"], monto="1000").json()["id"]
    _cerrar(cliente, contrato_id)

    assert _aplicar(cliente, primero, "1000").status_code == 200
    assert _aplicar(cliente, segundo, "500").json()["detail"].startswith("Lo aplicado excedería")
    assert _aplicar(cliente, segundo, "425").status_code == 200


def test_no_se_aplica_ni_devuelve_con_el_contrato_abierto(cliente, datos_base, contrato_id):
    deposito_id = _depositar(cliente, contrato_id, datos_base["GTQ"]).json()["id"]

    assert "al cerrar el contrato" in _aplicar(cliente, deposito_id, "100").json()["detail"]
    assert (
        "al cerrar el contrato" in _devolver(cliente, deposito_id, "100", datos_base["GTQ"]).json()["detail"]
    )


def test_no_aplica_un_deposito_en_otra_moneda(cliente, datos_base, contrato_id):
    deposito_id = _depositar(cliente, contrato_id, datos_base["USD"], moneda="USD", monto="300").json()["id"]
    _cerrar(cliente, contrato_id)

    assert "es en USD y el contrato en GTQ" in _aplicar(cliente, deposito_id, "100").json()["detail"]


# ── Vigentes y saldo total (criterio 5) ───────────────────────────────────────


def test_depositos_vigentes_y_total_por_moneda(cliente, datos_base, contrato_id):
    _depositar(cliente, contrato_id, datos_base["GTQ"])
    _depositar(cliente, contrato_id, datos_base["GTQ"], monto="500")
    dolares = _depositar(cliente, contrato_id, datos_base["USD"], moneda="USD", monto="300").json()["id"]
    _depositar(cliente, contrato_id, None, tipo="autorizacion_tarjeta", referencia="AUT-1", monto="999")
    _cerrar(cliente, contrato_id)
    _devolver(cliente, dolares, "100", datos_base["USD"])

    vigentes = cliente.get(URL).json()

    assert len(vigentes["depositos"]) == 3
    assert vigentes["totales"] == {"GTQ": "2500.000000", "USD": "200.000000"}
    # El saldo de los depósitos cuadra con el de sus cuentas de pasivo en el mayor (criterio 5).
    assert vigentes["mayor"] == vigentes["totales"]
    assert vigentes["cuadra"] is True
    with SessionLocal() as db:
        assert service.saldo_depositos(db) == {"GTQ": Decimal("2500"), "USD": Decimal("200")}


# ── Factura del contrato cerrado (HU-6.02) ─────────────────────────────────────

PERFIL = {
    "vigente_desde": "2026-01-01",
    "razon_social": "Kilómetro Cero, S. A.",
    "nombre_comercial": "Kilómetro Cero",
    "nit": "1234567-9",
    "direccion_fiscal": "Zona 10, Ciudad de Guatemala",
    "establecimiento": "1",
    "regimen_isr": "utilidades",
}


def test_el_contrato_cerrado_se_factura_una_sola_vez(cliente, datos_base, contrato_id):
    with SessionLocal() as db:
        db.execute(text("DELETE FROM perfil_fiscal"))
        db.commit()
    assert cliente.post(f"{API}/configuracion/perfil-fiscal", json=PERFIL).status_code == 201
    url = f"{URL_CONTRATOS}/{contrato_id}/factura"

    abierto = cliente.post(url)
    assert abierto.status_code == 409
    assert "no está cerrado" in abierto.json()["detail"]

    _cerrar(cliente, contrato_id)
    contrato = cliente.get(f"{URL_CONTRATOS}/{contrato_id}").json()
    respuesta = cliente.post(url)
    assert respuesta.status_code == 201, respuesta.text
    factura = respuesta.json()
    assert factura["estado"] == "certificada"
    assert (factura["origen_tipo"], factura["origen_id"]) == ("contrato", contrato_id)
    assert Decimal(factura["total"]) == Decimal(contrato["monto_final"])
    assert factura["partida_id"] is not None

    repetida = cliente.post(url)
    assert repetida.status_code == 409
    assert f"ya tiene su factura ({factura['serie']}-{factura['numero']})" in repetida.json()["detail"]


# ── Permisos ──────────────────────────────────────────────────────────────────


def test_sin_sesion_responde_401(cliente_contador):
    from fastapi.testclient import TestClient

    from app.main import app

    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(f"{URL_CONTRATOS}/1/depositos", json={}).status_code == 401
    assert anonimo.post(f"{URL}/1/devolucion", json={}).status_code == 401


def test_gerencia_consulta_pero_no_registra(cliente, datos_base, contrato_id):
    token = cliente.post(
        f"{API}/seguridad/login", json={"correo": "gerencia@empresa.gt", "clave": CLAVE_PRUEBAS}
    ).json()["token"]
    gerencia = {"Authorization": f"Bearer {token}"}
    deposito = {
        "tipo": "deposito",
        "fecha": FECHA,
        "moneda": "GTQ",
        "monto": "100",
        "cuenta_bancaria_id": datos_base["GTQ"],
    }

    assert (
        cliente.post(f"{URL_CONTRATOS}/{contrato_id}/depositos", json=deposito, headers=gerencia).status_code
        == 403
    )
    assert (
        cliente.post(f"{URL}/1/aplicacion", json={"fecha": FECHA, "monto": "1"}, headers=gerencia).status_code
        == 403
    )
    assert cliente.get(URL, headers=gerencia).status_code == 200
