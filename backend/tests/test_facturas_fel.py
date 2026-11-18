"""HU-6.02 (parte 1): emitir una factura FEL contra el certificador simulado, con su cuenta por cobrar
y su partida; rechazo sin efecto contable; USD en quetzales; umbral de Consumidor Final."""

from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.main import app
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.facturacion import service
from tests.conftest import CLAVE_PRUEBAS

URL = "/api/v1/facturacion/facturas"
VIN = "1HGCM82633A004352"
FECHA = "2026-10-20"
FECHA_USD = "2026-10-21"
TIPO_CAMBIO = "7.77777777"

PERFIL = {
    "vigente_desde": "2026-01-01",
    "razon_social": "Kilómetro Cero, S. A.",
    "nombre_comercial": "Kilómetro Cero",
    "nit": "1234567-9",
    "direccion_fiscal": "Zona 10, Ciudad de Guatemala",
    "establecimiento": "1",
    "regimen_isr": "utilidades",
}
EMPRESA = {
    "tipo": "empresa",
    "nombre": "Transportes del Norte, S.A.",
    "tipo_identificacion": "nit",
    "identificacion": "576937-K",
}
ALQUILER = {"descripcion": "Alquiler semanal", "cantidad": "1", "precio_unitario": "1120.00",
            "linea_negocio": "alquiler", "vin": VIN}  # fmt: skip
TALLER = {"descripcion": "Servicio de frenos", "cantidad": "3", "precio_unitario": "33.33",
          "linea_negocio": "taller"}  # fmt: skip


@pytest.fixture
def cliente(cliente_contador):
    return cliente_contador


@pytest.fixture(autouse=True)
def datos_base(cliente):
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("TRUNCATE unidad, partida, cliente, factura RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM perfil_fiscal"))
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
    assert cliente.post("/api/v1/configuracion/perfil-fiscal", json=PERFIL).status_code == 201
    unidad = {"vin": VIN, "marca": "Honda", "linea": "Accord", "modelo": 2007, "color": "Gris",
              "tipo_vehiculo": "sedan"}  # fmt: skip
    assert cliente.post("/api/v1/unidades", json=unidad).status_code == 201
    tipo = {"fecha": FECHA_USD, "valor": TIPO_CAMBIO}
    assert cliente.post("/api/v1/configuracion/tipos-cambio", json=tipo).status_code == 201


@pytest.fixture
def empresa(cliente) -> int:
    return cliente.post("/api/v1/facturacion/clientes", json=EMPRESA).json()["id"]


def _factura(cliente_id: int | None, *lineas: dict, **cambios) -> dict:
    return {"cliente_id": cliente_id, "fecha": FECHA, "moneda": "GTQ", "lineas": list(lineas), **cambios}


def _partida(factura_id: int) -> list[tuple]:
    """(cuenta, debe, haber, moneda, monto USD, línea de negocio, VIN) de la partida de la factura."""
    with SessionLocal() as db:
        filas = db.execute(
            text(
                """
                SELECT c.codigo, l.debe, l.haber, l.moneda, l.monto_usd, l.linea_negocio, l.vin
                FROM linea_partida l
                JOIN partida p ON p.id = l.partida_id
                JOIN cuentas c ON c.id = l.cuenta_id
                WHERE p.documento_tipo = 'factura' AND p.documento_id = :id AND p.estado = 'contabilizada'
                ORDER BY l.numero_linea
                """
            ),
            {"id": str(factura_id)},
        )
        return [tuple(fila) for fila in filas]


def _cuantas(tabla: str) -> int:
    with SessionLocal() as db:
        return db.scalar(text(f"SELECT count(*) FROM {tabla}"))  # noqa: S608 (nombre fijo de la prueba)


def _sin_efecto_contable() -> bool:
    with SessionLocal() as db:
        partidas = db.scalar(text("SELECT count(*) FROM partida WHERE documento_tipo = 'factura'"))
    return partidas == 0 and _cuantas("cuenta_por_cobrar") == 0


def con_rol(correo: str) -> TestClient:
    otro = TestClient(app)
    token = otro.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}).json()[
        "token"
    ]
    otro.headers["Authorization"] = f"Bearer {token}"
    return otro


# ── Totales, certificación y partida en quetzales (criterios 1, 2 y 5) ────────


def test_calcula_totales_con_iva_incluido_y_redondeo_mitad_hacia_arriba(cliente, empresa):
    respuesta = cliente.post(URL, json=_factura(empresa, TALLER, ALQUILER))

    assert respuesta.status_code == 201
    factura = respuesta.json()
    # 3 × 33.33 = 99.99 → base 99.99 / 1.12 = 89.2767… → 89.28; IVA 10.71.
    assert [(x["total"], x["base"], x["iva"]) for x in factura["lineas"]] == [
        ("99.990000", "89.280000", "10.710000"),
        ("1120.000000", "1000.000000", "120.000000"),
    ]
    assert (factura["base"], factura["iva"], factura["total"]) == ("1089.280000", "130.710000", "1219.990000")
    assert factura["total_gtq"] == "1219.990000"
    assert factura["receptor_id"] == "576937K"
    assert (factura["emisor_nit"], factura["emisor_nombre"]) == ("12345679", "Kilómetro Cero, S. A.")


def test_certificada_guarda_los_datos_fel_y_genera_partida_y_cuenta_por_cobrar(cliente, empresa):
    factura = cliente.post(
        URL, json=_factura(empresa, TALLER, ALQUILER, dias_credito=30, origen_tipo="contrato", origen_id=7)
    ).json()

    assert factura["estado"] == "certificada"
    assert factura["serie"] and factura["numero"] and len(factura["autorizacion"]) == 36
    assert factura["autorizacion"] in factura["xml"] and factura["motivo_rechazo"] is None
    assert _partida(factura["id"]) == [
        ("1.1.02.01", Decimal("99.990000"), Decimal(0), "GTQ", None, "taller", None),
        ("1.1.02.01", Decimal("1120.000000"), Decimal(0), "GTQ", None, "alquiler", None),
        ("4.3", Decimal(0), Decimal("89.280000"), "GTQ", None, "taller", None),
        ("4.1", Decimal(0), Decimal("1000.000000"), "GTQ", None, "alquiler", VIN),
        ("2.1.02.01", Decimal(0), Decimal("130.710000"), "GTQ", None, None, None),
    ]
    assert factura["partida_id"] is not None
    assert factura["cuenta_por_cobrar"] == {
        "id": factura["cuenta_por_cobrar"]["id"],
        "fecha": FECHA,
        "fecha_vencimiento": "2026-11-19",
        "moneda": "GTQ",
        "monto": "1219.990000",
        "saldo": "1219.990000",
    }
    assert cliente.get(f"{URL}/{factura['id']}").json()["autorizacion"] == factura["autorizacion"]
    assert [f["id"] for f in cliente.get(URL).json()] == [factura["id"]]
    with SessionLocal() as db:
        assert [f.id for f in service.facturas_de_origen(db, "contrato", 7)] == [factura["id"]]
        assert service.facturas_de_origen(db, "contrato", 8) == []


def test_factura_en_dolares_guarda_el_tipo_de_cambio_y_se_contabiliza_en_quetzales(cliente, empresa):
    linea = {**ALQUILER, "cantidad": "2", "precio_unitario": "560.00"}
    factura = cliente.post(URL, json=_factura(empresa, linea, moneda="USD", fecha=FECHA_USD)).json()

    assert factura["estado"] == "certificada"
    assert factura["tipo_cambio"] == "7.77777777"
    # 1120 × 7.77777777 = 8711.1111024 → 8711.111102; ingreso 1000 × tc = 7777.77777; el IVA cuadra.
    assert factura["total_gtq"] == "8711.111102"
    assert _partida(factura["id"]) == [
        ("1.1.02.02", Decimal("8711.111102"), Decimal(0), "USD", Decimal("1120.000000"), "alquiler", None),
        ("4.1", Decimal(0), Decimal("7777.777770"), "GTQ", None, "alquiler", VIN),
        ("2.1.02.01", Decimal(0), Decimal("933.333332"), "GTQ", None, None, None),
    ]
    cuenta = factura["cuenta_por_cobrar"]
    assert (cuenta["moneda"], cuenta["monto"], cuenta["saldo"]) == ("USD", "1120.000000", "1120.000000")
    assert cuenta["fecha_vencimiento"] == FECHA_USD


# ── Rechazo y casos sin efecto contable (criterio 3) ──────────────────────────


def test_rechazada_muestra_el_motivo_y_no_tiene_efecto_contable(cliente, empresa):
    linea = {**TALLER, "descripcion": "RECHAZAR: receptor inactivo en la SAT"}
    respuesta = cliente.post(URL, json=_factura(empresa, linea))

    assert respuesta.status_code == 201
    factura = respuesta.json()
    assert (factura["estado"], factura["motivo_rechazo"]) == ("rechazada", "receptor inactivo en la SAT")
    assert factura["autorizacion"] is None and factura["partida_id"] is None
    assert factura["cuenta_por_cobrar"] is None
    assert _sin_efecto_contable()
    assert _cuantas("factura") == 1  # el intento queda para trazabilidad


def test_sin_regla_de_la_linea_de_negocio_no_guarda_nada(cliente, empresa):
    linea = {**TALLER, "linea_negocio": "financiamiento"}
    respuesta = cliente.post(URL, json=_factura(empresa, linea))

    assert respuesta.status_code == 409
    assert (
        "Falta la regla de contabilización «factura · ingreso_financiamiento»" in respuesta.json()["detail"]
    )
    assert _cuantas("factura") == 0 and _sin_efecto_contable()


def test_sin_tipo_de_cambio_de_la_fecha_no_guarda_nada(cliente, empresa):
    respuesta = cliente.post(URL, json=_factura(empresa, TALLER, moneda="USD", fecha=FECHA))

    assert respuesta.status_code == 409
    assert "No existe tipo de cambio para el 20/10/2026" in respuesta.json()["detail"]
    assert _cuantas("factura") == 0 and _sin_efecto_contable()


def test_linea_de_alquiler_sin_vin_se_rechaza_antes_de_certificar(cliente, empresa):
    linea = {**ALQUILER, "vin": None}
    respuesta = cliente.post(URL, json=_factura(empresa, linea))

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "Línea 1: La cuenta 4.1 exige el VIN de la unidad"
    assert _cuantas("factura") == 0


def test_si_la_partida_falla_despues_de_certificar_no_se_pierde_la_certificacion(
    cliente, empresa, monkeypatch
):
    def falla(*_args, **_kwargs):
        raise ErrorNegocio("falla simulada del motor", 409)

    monkeypatch.setattr(service.contabilidad, "registrar_automatica", falla)
    respuesta = cliente.post(URL, json=_factura(empresa, TALLER))

    assert respuesta.status_code == 409
    assert (
        "quedó certificada, pero no se pudo contabilizar: falla simulada del motor"
        in respuesta.json()["detail"]
    )
    factura = cliente.get(URL).json()[0]
    assert factura["estado"] == "certificada" and factura["autorizacion"] and factura["xml"]
    assert factura["partida_id"] is None and factura["cuenta_por_cobrar"] is None


# ── Emisor y Consumidor Final (criterio 6) ─────────────────────────────────────


def test_sin_perfil_fiscal_vigente_no_se_factura(cliente, empresa):
    with SessionLocal() as db:
        db.execute(text("DELETE FROM perfil_fiscal"))
        db.commit()
    respuesta = cliente.post(URL, json=_factura(empresa, TALLER))

    assert respuesta.status_code == 409
    assert "No hay perfil fiscal de la empresa vigente al 20/10/2026" in respuesta.json()["detail"]
    assert _cuantas("factura") == 0


def test_consumidor_final_hasta_el_umbral(cliente):
    linea = {**TALLER, "cantidad": "1", "precio_unitario": "2500.00"}
    factura = cliente.post(URL, json=_factura(None, linea)).json()

    assert factura["estado"] == "certificada"
    assert (factura["receptor_id"], factura["receptor_nombre"]) == ("CF", "Consumidor Final")
    assert factura["cuenta_por_cobrar"]["monto"] == "2500.000000"


@pytest.mark.parametrize(
    "cambios",
    [
        {"lineas": [{**TALLER, "cantidad": "1", "precio_unitario": "2500.01"}]},
        # 400 USD × 7.77777777 ≈ Q3,111.11: el umbral se compara en quetzales.
        {"lineas": [{**TALLER, "cantidad": "1", "precio_unitario": "400.00"}],
         "moneda": "USD", "fecha": FECHA_USD},
    ],
)  # fmt: skip
def test_consumidor_final_por_encima_del_umbral_se_rechaza(cliente, cambios):
    respuesta = cliente.post(URL, json=_factura(None, **cambios))

    assert respuesta.status_code == 400
    assert "Q2,500.00 no puede emitirse a Consumidor Final" in respuesta.json()["detail"]
    assert _cuantas("factura") == 0


def test_validaciones_de_la_entrada(cliente, empresa):
    futura = _factura(empresa, TALLER, fecha=date.today().replace(year=date.today().year + 1).isoformat())
    assert cliente.post(URL, json=futura).json()["detail"] == "La fecha de la factura no puede ser futura"
    sin_lineas = cliente.post(URL, json=_factura(empresa))
    assert sin_lineas.json()["detail"] == "La factura necesita al menos una línea"
    solo_tipo = cliente.post(URL, json=_factura(empresa, TALLER, origen_tipo="contrato"))
    assert solo_tipo.status_code == 400
    cantidad = cliente.post(URL, json=_factura(empresa, {**TALLER, "cantidad": "0"}))
    assert cantidad.json()["detail"] == "Línea 1: la cantidad debe ser mayor que cero"


# ── Permisos (HU-1.09) ─────────────────────────────────────────────────────────


def test_sin_sesion_responde_401():
    anonimo = TestClient(app)
    assert anonimo.get(URL).status_code == 401
    assert anonimo.post(URL, json=_factura(None, TALLER)).status_code == 401


def test_gerencia_lee_pero_no_emite(empresa):
    gerencia = con_rol("gerencia@empresa.gt")
    assert gerencia.post(URL, json=_factura(empresa, TALLER)).status_code == 403
    assert gerencia.get(URL).status_code == 200


def test_el_auxiliar_contable_emite(empresa):
    assert con_rol("auxiliar@empresa.gt").post(URL, json=_factura(empresa, TALLER)).status_code == 201
