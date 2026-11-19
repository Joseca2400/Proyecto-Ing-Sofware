"""HU-4.04 (versión delgada): gastos de importación por VIN con IVA separado y cuenta por pagar."""

from datetime import date, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal

URL = "/api/v1/compras/gastos-importacion"
URL_PROVEEDORES = "/api/v1/compras/proveedores"
URL_UNIDADES = "/api/v1/unidades"
VIN = "1HGCM82633A004352"
OTRO_VIN = "JHMCM56557C404453"  # fabricado en Japón: sin dígito verificador obligatorio
FECHA = "2026-10-20"
TIPO_CAMBIO = "7.75"

NAVIERA = {
    "tipo": "exterior",
    "nombre": "Seaboard Marine Ltd.",
    "identificacion_fiscal": "59-1182372",
    "pais": "US",
    "rubro": "naviera",
    "moneda_habitual": "USD",
    "dias_credito": 15,
}
SAT = {
    "tipo": "local",
    "nombre": "Superintendencia de Administración Tributaria",
    "nit": "1669394-9",
    "regimen": "general",
    "rubro": "otros",
    "moneda_habitual": "GTQ",
    "dias_credito": 0,
}


def _unidad(vin: str) -> dict:
    return {
        "vin": vin,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
    }


def _gasto(proveedor_id: int, **cambios) -> dict:
    return {
        "vin": VIN,
        "concepto": "flete",
        "proveedor_id": proveedor_id,
        "fecha": FECHA,
        "documento": "BL-778812",
        "moneda": "GTQ",
        "monto": "3500.00",
        **cambios,
    }


@pytest.fixture(autouse=True)
def datos_base(cliente):
    """Sin gastos ni unidades previas; dos unidades registradas y el tipo de cambio de la fecha."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE proveedor, unidad RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
    for vin in (VIN, OTRO_VIN):
        assert cliente.post(URL_UNIDADES, json=_unidad(vin)).status_code == 201
    tipo = cliente.post("/api/v1/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": TIPO_CAMBIO})
    assert tipo.status_code == 201


@pytest.fixture
def naviera(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=NAVIERA).json()["id"]


@pytest.fixture
def sat(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=SAT).json()["id"]


def _cuantos_gastos() -> int:
    with SessionLocal() as db:
        return db.scalar(text("SELECT count(*) FROM gasto_importacion"))


def _cuantas_cuentas_por_pagar() -> int:
    with SessionLocal() as db:
        return db.scalar(text("SELECT count(*) FROM cuenta_por_pagar"))


# ── Catálogo de conceptos (criterio 1) ─────────────────────────────────────────


def test_catalogo_de_conceptos_con_su_cuenta_y_su_tratamiento(cliente):
    respuesta = cliente.get(f"{URL}/conceptos")

    assert respuesta.status_code == 200
    conceptos = {c["codigo"]: c for c in respuesta.json()}
    assert list(conceptos) == [
        "flete", "seguro", "agente_aduanal", "almacenaje", "dai", "iva_importacion", "iprima",
        "placas", "otros",
    ]  # fmt: skip
    assert conceptos["seguro"]["nombre"] == "Seguro de transporte"
    iva = conceptos["iva_importacion"]
    assert iva["tratamiento"] == "credito_fiscal"
    assert iva["cuenta"] == "1.1.03.02"
    assert iva["suma_al_costo"] is False
    for codigo, concepto in conceptos.items():
        if codigo != "iva_importacion":
            assert concepto["tratamiento"] == "costo"
            assert concepto["cuenta"] == "1.1.04.01"
            assert concepto["suma_al_costo"] is True


# ── Registro (criterios 3 y 4) ─────────────────────────────────────────────────


def test_registra_gasto_en_quetzales_con_su_cuenta_por_pagar(cliente, sat):
    respuesta = cliente.post(
        URL, json=_gasto(sat, vin=" 1hgcm82633a004352 ", concepto="dai", descripcion="  DAI 10 %  ")
    )

    assert respuesta.status_code == 201
    gasto = respuesta.json()
    assert gasto["vin"] == VIN
    assert gasto["concepto"] == "dai"
    assert gasto["concepto_nombre"] == "DAI"
    assert gasto["proveedor"] == {"id": sat, "nombre": SAT["nombre"], "tipo": "local"}
    assert gasto["descripcion"] == "DAI 10 %"
    assert gasto["moneda"] == "GTQ"
    assert gasto["monto"] == "3500.000000"
    assert gasto["tipo_cambio"] is None
    assert gasto["monto_gtq"] == "3500.000000"
    assert gasto["cuenta"] == "1.1.04.01"
    assert gasto["tratamiento"] == "costo"
    assert gasto["suma_al_costo"] is True

    cxp = gasto["cuenta_por_pagar"]
    assert cxp["moneda"] == "GTQ"
    assert cxp["monto"] == cxp["saldo"] == "3500.000000"
    assert cxp["fecha"] == cxp["fecha_vencimiento"] == FECHA  # la SAT: sin días de crédito


def test_gasto_en_dolares_usa_el_tipo_de_cambio_y_debe_en_dolares(cliente, naviera):
    respuesta = cliente.post(URL, json=_gasto(naviera, moneda="USD", monto="1250.50"))

    assert respuesta.status_code == 201
    gasto = respuesta.json()
    assert gasto["moneda"] == "USD"
    assert gasto["monto"] == "1250.500000"
    assert gasto["tipo_cambio"] == "7.75000000"
    assert gasto["monto_gtq"] == "9691.375000"  # 1250.50 × 7.75, sin pasar por float

    cxp = gasto["cuenta_por_pagar"]
    assert cxp["moneda"] == "USD"
    assert cxp["monto"] == cxp["saldo"] == "1250.500000"
    assert cxp["fecha_vencimiento"] == str(date.fromisoformat(FECHA) + timedelta(days=15))


def test_sin_tipo_de_cambio_de_la_fecha_no_registra_el_gasto_en_dolares(cliente, naviera):
    respuesta = cliente.post(URL, json=_gasto(naviera, moneda="USD", fecha="2026-10-21"))

    assert respuesta.status_code == 409
    assert "No existe tipo de cambio para el 21/10/2026" in respuesta.json()["detail"]
    assert _cuantos_gastos() == 0
    assert _cuantas_cuentas_por_pagar() == 0


def test_iva_de_importacion_es_credito_fiscal_y_no_suma_al_costo(cliente, sat):
    respuesta = cliente.post(URL, json=_gasto(sat, concepto="iva_importacion", monto="1020.00"))

    assert respuesta.status_code == 201
    gasto = respuesta.json()
    assert gasto["tratamiento"] == "credito_fiscal"
    assert gasto["cuenta"] == "1.1.03.02"
    assert gasto["suma_al_costo"] is False
    # Igual genera la cuenta por pagar a la SAT.
    assert gasto["cuenta_por_pagar"]["monto"] == "1020.000000"


# ── Total en la ficha de la unidad ─────────────────────────────────────────────


def test_resumen_de_la_unidad_suma_al_costo_sin_el_iva_de_importacion(cliente, naviera, sat):
    for gasto in (
        _gasto(naviera, moneda="USD", monto="100.00"),  # Q775.00
        _gasto(sat, concepto="dai", monto="3500.10"),
        _gasto(sat, concepto="iva_importacion", monto="1020.00"),
        _gasto(sat, vin=OTRO_VIN, concepto="placas", monto="900.00"),  # de otra unidad
    ):
        assert cliente.post(URL, json=gasto).status_code == 201

    respuesta = cliente.get(f"{URL}/unidad/{VIN.lower()}")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "vin": VIN,
        "gastos": 3,
        "total_costo_gtq": "4275.100000",
        "total_credito_fiscal_gtq": "1020.000000",
    }


def test_resumen_de_una_unidad_sin_gastos_es_cero(cliente):
    respuesta = cliente.get(f"{URL}/unidad/{VIN}")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "vin": VIN,
        "gastos": 0,
        "total_costo_gtq": "0.000000",
        "total_credito_fiscal_gtq": "0.000000",
    }


def test_resumen_de_una_unidad_inexistente_responde_404(cliente):
    assert cliente.get(f"{URL}/unidad/1M8GDM9AXKP042788").status_code == 404


# ── Consulta ───────────────────────────────────────────────────────────────────


def test_lista_los_gastos_por_unidad_y_por_proveedor(cliente, naviera, sat):
    primero = cliente.post(URL, json=_gasto(naviera, fecha="2026-10-19")).json()
    segundo = cliente.post(URL, json=_gasto(sat, concepto="dai")).json()
    otro = cliente.post(URL, json=_gasto(sat, vin=OTRO_VIN, concepto="placas")).json()

    todos = cliente.get(URL).json()
    assert [g["id"] for g in todos] == [otro["id"], segundo["id"], primero["id"]]

    de_la_unidad = cliente.get(URL, params={"vin": VIN.lower()}).json()
    assert [g["id"] for g in de_la_unidad] == [segundo["id"], primero["id"]]

    de_la_sat = cliente.get(URL, params={"proveedor_id": sat}).json()
    assert [g["id"] for g in de_la_sat] == [otro["id"], segundo["id"]]

    consulta = cliente.get(f"{URL}/{primero['id']}")
    assert consulta.status_code == 200
    assert consulta.json() == primero
    assert cliente.get(f"{URL}/999999").status_code == 404


# ── Validaciones ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"vin": "1M8GDM9AXKP042788"}, "No existe la unidad con VIN 1M8GDM9AXKP042788"),
        ({"vin": "1HGCM82633A004353"}, "dígito verificador"),
        ({"vin": "1HGCM8263OA004352"}, "sin I, O ni Q"),
        ({"concepto": "propina"}, "Concepto de gasto de importación desconocido"),
        ({"documento": "   "}, "Indique el documento"),
        ({"monto": "0"}, "El monto debe ser mayor que cero"),
        ({"monto": "-10"}, "El monto debe ser mayor que cero"),
        ({"monto": "1.1234567"}, "El monto admite hasta 6 decimales"),
        ({"monto": "abc"}, "El monto no es un número válido"),
        ({"monto": "NaN"}, "El monto no es un número válido"),
        ({"monto": "1000000000000"}, "El monto excede el máximo permitido"),
        ({"fecha": str(date.today() + timedelta(days=1))}, "no puede ser futura"),
    ],
)
def test_rechaza_gastos_invalidos(cliente, sat, cambios, mensaje):
    respuesta = cliente.post(URL, json=_gasto(sat, **cambios))

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert _cuantos_gastos() == 0


def test_rechaza_proveedor_inexistente(cliente):
    respuesta = cliente.post(URL, json=_gasto(999999))

    assert respuesta.status_code == 404
    assert _cuantos_gastos() == 0


@pytest.mark.parametrize("cambios", [{"monto": 3500.0}, {"moneda": "EUR"}, {"vin": None}])
def test_rechaza_monto_numerico_y_moneda_desconocida(cliente, sat, cambios):
    assert cliente.post(URL, json=_gasto(sat, **cambios)).status_code == 422


def test_la_cuenta_por_pagar_nace_de_un_solo_documento(cliente, sat):
    gasto = cliente.post(URL, json=_gasto(sat)).json()

    with SessionLocal() as db, pytest.raises(IntegrityError, match="ck_cuenta_por_pagar_origen"):
        db.execute(
            text(
                "INSERT INTO cuenta_por_pagar (proveedor_id, fecha, fecha_vencimiento, moneda, monto, saldo)"
                " VALUES (:p, :f, :f, 'GTQ', 1, 1)"
            ),
            {"p": sat, "f": FECHA},
        )
    with SessionLocal() as db, pytest.raises(IntegrityError, match="uq_cuenta_por_pagar_gasto_importacion"):
        db.execute(
            text(
                "INSERT INTO cuenta_por_pagar"
                " (proveedor_id, gasto_importacion_id, fecha, fecha_vencimiento, moneda, monto, saldo)"
                " VALUES (:p, :g, :f, :f, 'GTQ', 1, 1)"
            ),
            {"p": sat, "g": gasto["id"], "f": FECHA},
        )


# ── Bitácora (HU-1.11) ─────────────────────────────────────────────────────────


def test_el_gasto_y_su_cuenta_por_pagar_se_auditan_con_el_vin(cliente, naviera):
    with SessionLocal() as db:
        desde = db.scalar(text("SELECT coalesce(max(id), 0) FROM bitacora"))

    gasto = cliente.post(URL, json=_gasto(naviera, moneda="USD", monto="100.00")).json()

    with SessionLocal() as db:
        registros = list(
            db.scalars(
                select(RegistroBitacora)
                .where(RegistroBitacora.id > desde, RegistroBitacora.accion == "crear")
                .order_by(RegistroBitacora.id)
            )
        )
    alta_gasto = next(r for r in registros if r.entidad == "gasto_importacion")
    assert alta_gasto.registro_id == str(gasto["id"])
    assert alta_gasto.usuario_id is None
    assert alta_gasto.vin == VIN
    assert alta_gasto.nuevos["tratamiento"] == "costo"
    assert alta_gasto.nuevos["monto_gtq"] == 775

    alta_cxp = next(r for r in registros if r.entidad == "cuenta_por_pagar")
    assert alta_cxp.registro_id == str(gasto["cuenta_por_pagar"]["id"])
    assert alta_cxp.nuevos["gasto_importacion_id"] == gasto["id"]
    assert alta_cxp.nuevos["factura_compra_id"] is None
