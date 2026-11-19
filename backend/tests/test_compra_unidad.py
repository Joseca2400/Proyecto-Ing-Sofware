"""HU-4.02 (versión delgada): compra en USD que crea la unidad, la cuenta por pagar y la partida."""

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import pytest
from sqlalchemy import select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.compras import service as compras
from app.modulos.configuracion.semilla import crear_catalogo_inicial

URL = "/api/v1/compras/compras-unidades"
URL_PROVEEDORES = "/api/v1/compras/proveedores"
URL_UNIDADES = "/api/v1/unidades"
URL_GASTOS = "/api/v1/compras/gastos-importacion"
VIN = "1HGCM82633A004352"
FECHA = "2026-10-20"
TIPO_CAMBIO = "7.75"

SUBASTA = {
    "tipo": "exterior",
    "nombre": "Copart Inc.",
    "identificacion_fiscal": "94-2867490",
    "pais": "US",
    "rubro": "subasta",
    "moneda_habitual": "USD",
    "dias_credito": 30,
}
AGENTE = {
    "tipo": "local",
    "nombre": "Aduanas Express, S. A.",
    "nit": "1669394-9",
    "regimen": "general",
    "rubro": "agente_aduanal",
    "moneda_habitual": "GTQ",
    "dias_credito": 0,
}


def _compra(proveedor_id: int, **cambios) -> dict:
    return {
        "proveedor_id": proveedor_id,
        "fecha": FECHA,
        "documento": "LOT-44871203",
        "vin": VIN,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "precio_usd": "8500.00",
        "comision_usd": "350.00",
        "documentacion_usd": "75.00",
        "arrastre_usd": "150.00",
        **cambios,
    }


@pytest.fixture(autouse=True)
def datos_base(cliente):
    """Sin compras, unidades ni partidas previas; catálogo semilla y el tipo de cambio de la fecha.

    TRUNCATE no dispara los triggers que protegen las partidas contabilizadas: así cada prueba
    empieza sin partidas y el id de la compra (que liga su partida) puede repetirse.
    """
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("TRUNCATE proveedor, unidad, partida RESTART IDENTITY CASCADE"))
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
    tipo = cliente.post("/api/v1/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": TIPO_CAMBIO})
    assert tipo.status_code == 201


@pytest.fixture
def subasta(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=SUBASTA).json()["id"]


@pytest.fixture
def agente(cliente) -> int:
    return cliente.post(URL_PROVEEDORES, json=AGENTE).json()["id"]


def _cuantos(tabla: str) -> int:
    with SessionLocal() as db:
        return db.scalar(text(f"SELECT count(*) FROM {tabla}"))  # noqa: S608 (tablas fijas de la prueba)


def _nada_creado() -> None:
    for tabla in ("unidad", "cambio_estado_unidad", "compra_unidad", "cuenta_por_pagar", "partida"):
        assert _cuantos(tabla) == 0, tabla


# ── Registro en una sola transacción (criterios 1, 2 y 3) ─────────────────────


def test_la_compra_crea_la_unidad_en_transito_y_su_cuenta_por_pagar_en_usd(cliente, subasta):
    respuesta = cliente.post(URL, json=_compra(subasta, vin=" 1hgcm82633a004352 "))

    assert respuesta.status_code == 201
    compra = respuesta.json()
    assert compra["vin"] == VIN
    assert compra["proveedor"] == {"id": subasta, "nombre": "Copart Inc.", "tipo": "exterior"}
    assert compra["documento"] == "LOT-44871203"
    assert compra["precio_usd"] == "8500.000000"
    assert compra["comision_usd"] == "350.000000"
    assert compra["documentacion_usd"] == "75.000000"
    assert compra["arrastre_usd"] == "150.000000"
    assert compra["total_usd"] == "9075.000000"
    assert compra["tipo_cambio"] == "7.75000000"
    assert compra["total_gtq"] == "70331.250000"  # 9075.00 × 7.75, sin pasar por float

    cxp = compra["cuenta_por_pagar"]
    assert cxp["moneda"] == "USD"
    assert cxp["monto"] == cxp["saldo"] == "9075.000000"
    assert cxp["fecha"] == FECHA
    assert cxp["fecha_vencimiento"] == str(date.fromisoformat(FECHA) + timedelta(days=30))

    unidad = cliente.get(f"{URL_UNIDADES}/{VIN}").json()
    assert unidad["estado"] == "en_transito"
    assert (unidad["marca"], unidad["linea"], unidad["modelo"]) == ("Honda", "Accord", 2007)
    [alta] = cliente.get(f"{URL_UNIDADES}/{VIN}/historial").json()
    assert alta["estado_nuevo"] == "en_transito"
    assert alta["documento"] == "Compra LOT-44871203 a Copart Inc."


def test_la_partida_carga_vehiculos_en_transito_contra_proveedores_del_exterior(cliente, subasta):
    compra = cliente.post(URL, json=_compra(subasta)).json()

    with SessionLocal() as db:
        partida = db.execute(
            text(
                "SELECT id, estado, origen, documento_tipo, documento_id, numero, fecha"
                " FROM partida WHERE id = :id"
            ),
            {"id": compra["partida_id"]},
        ).one()
        lineas = db.execute(
            text(
                "SELECT c.codigo, l.debe, l.haber, l.moneda, l.monto_usd, l.tipo_cambio, l.vin"
                " FROM linea_partida l JOIN cuentas c ON c.id = l.cuenta_id"
                " WHERE l.partida_id = :id ORDER BY l.numero_linea"
            ),
            {"id": compra["partida_id"]},
        ).all()

    assert partida.estado == "contabilizada"
    assert partida.origen == "automatica"
    assert (partida.documento_tipo, partida.documento_id) == ("compra_unidad", str(compra["id"]))
    assert partida.numero is not None
    assert str(partida.fecha) == FECHA

    total = Decimal("70331.25")
    debito, credito = lineas
    assert debito.codigo == "1.1.04.01"
    assert (debito.debe, debito.haber, debito.moneda, debito.vin) == (total, 0, "GTQ", VIN)
    assert credito.codigo == "2.1.01.01"
    assert (credito.debe, credito.haber, credito.moneda) == (0, total, "USD")
    assert credito.monto_usd == Decimal("9075")
    assert credito.tipo_cambio == Decimal("7.75")
    assert credito.vin == VIN


def test_la_partida_cuadra_con_montos_que_redondean(cliente, subasta):
    """El equivalente se redondea una vez (6 decimales, mitad hacia arriba) y ambos lados coinciden."""
    otra_fecha = "2026-10-19"
    tipo = "7.71234567"
    assert (
        cliente.post(
            "/api/v1/configuracion/tipos-cambio", json={"fecha": otra_fecha, "valor": tipo}
        ).status_code
        == 201
    )
    datos = _compra(subasta, fecha=otra_fecha, precio_usd="1234.567891", comision_usd="0.000001")
    datos.pop("documentacion_usd")
    datos.pop("arrastre_usd")

    compra = cliente.post(URL, json=datos).json()

    esperado = (Decimal("1234.567892") * Decimal(tipo)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    assert compra["total_usd"] == "1234.567892"
    assert compra["documentacion_usd"] == compra["arrastre_usd"] == "0.000000"
    assert compra["total_gtq"] == f"{esperado:.6f}"
    with SessionLocal() as db:
        debe, haber = db.execute(
            text("SELECT sum(debe), sum(haber) FROM linea_partida WHERE partida_id = :id"),
            {"id": compra["partida_id"]},
        ).one()
    assert debe == haber == esperado


# ── El costo de la unidad en la ficha ─────────────────────────────────────────


def test_el_precio_de_compra_suma_al_costo_con_los_gastos_de_importacion(cliente, subasta, agente):
    cliente.post(URL, json=_compra(subasta))
    gastos = (
        {"concepto": "agente_aduanal", "monto": "3500.00"},
        {"concepto": "iva_importacion", "monto": "1020.00"},  # crédito fiscal: no suma
    )
    for gasto in gastos:
        datos = {"vin": VIN, "proveedor_id": agente, "fecha": FECHA, "documento": "F-1", "moneda": "GTQ"}
        assert cliente.post(URL_GASTOS, json={**datos, **gasto}).status_code == 201

    resumen = cliente.get(f"{URL_GASTOS}/unidad/{VIN}").json()

    assert resumen["compra_gtq"] == "70331.250000"
    assert resumen["total_costo_gtq"] == "3500.000000"
    assert resumen["total_credito_fiscal_gtq"] == "1020.000000"
    assert resumen["costo_total_gtq"] == "73831.250000"


def test_una_unidad_sin_compra_cuesta_solo_sus_gastos(cliente):
    unidad = {k: _compra(0)[k] for k in ("vin", "marca", "linea", "modelo", "color", "tipo_vehiculo")}
    assert cliente.post(URL_UNIDADES, json=unidad).status_code == 201

    resumen = cliente.get(f"{URL_GASTOS}/unidad/{VIN}").json()

    assert resumen["compra_gtq"] == resumen["costo_total_gtq"] == "0.000000"


# ── Si algo falla no se crea nada ─────────────────────────────────────────────


def test_vin_existente_no_crea_nada(cliente, subasta):
    assert cliente.post(URL, json=_compra(subasta)).status_code == 201

    respuesta = cliente.post(URL, json=_compra(subasta, documento="LOT-2"))

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == f"Ya existe una unidad con el VIN {VIN}"
    assert _cuantos("compra_unidad") == 1
    assert _cuantos("cuenta_por_pagar") == 1
    assert _cuantos("partida") == 1


def test_unidad_ya_registrada_sin_compra_no_se_compra(cliente, subasta):
    unidad = {k: _compra(0)[k] for k in ("vin", "marca", "linea", "modelo", "color", "tipo_vehiculo")}
    assert cliente.post(URL_UNIDADES, json=unidad).status_code == 201

    respuesta = cliente.post(URL, json=_compra(subasta))

    assert respuesta.status_code == 409
    assert _cuantos("compra_unidad") == 0
    assert _cuantos("partida") == 0


def test_sin_tipo_de_cambio_de_la_fecha_no_crea_nada(cliente, subasta):
    respuesta = cliente.post(URL, json=_compra(subasta, fecha="2026-10-21"))

    assert respuesta.status_code == 409
    assert "No existe tipo de cambio para el 21/10/2026" in respuesta.json()["detail"]
    _nada_creado()


def test_si_el_motor_rechaza_la_partida_no_queda_la_unidad(cliente, subasta, monkeypatch):
    # Caja general no admite VIN: el motor rechaza la línea después de escribir la unidad.
    monkeypatch.setattr(compras, "CUENTA_EN_TRANSITO", "1.1.01.01")

    respuesta = cliente.post(URL, json=_compra(subasta))

    assert respuesta.status_code == 400
    assert "no admite VIN" in respuesta.json()["detail"]
    _nada_creado()


def test_si_la_partida_falla_por_cualquier_error_de_negocio_no_queda_nada(cliente, subasta, monkeypatch):
    def falla(*_, **__):
        raise ErrorNegocio("La partida no cuadra", 400)

    monkeypatch.setattr(compras.contabilidad, "registrar_automatica", falla)

    respuesta = cliente.post(URL, json=_compra(subasta))

    assert respuesta.status_code == 400
    assert respuesta.json()["detail"] == "La partida no cuadra"
    _nada_creado()


def test_sin_las_cuentas_del_catalogo_no_crea_nada(cliente, subasta, monkeypatch):
    monkeypatch.setattr(compras, "CUENTA_PROVEEDORES_EXTERIOR", "9.9.99")

    respuesta = cliente.post(URL, json=_compra(subasta))

    assert respuesta.status_code == 409
    assert "no tiene 9.9.99" in respuesta.json()["detail"]
    _nada_creado()


# ── Validaciones ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"vin": "1HGCM82633A004353"}, "no pasa el dígito verificador"),
        ({"vin": "1HGCM82633A00435"}, "17 letras o dígitos"),
        ({"marca": "  "}, "La marca, la línea y el color son obligatorios"),
        ({"modelo": 1975}, "El modelo es el año del vehículo"),
        ({"tipo_vehiculo": "tanque"}, "Tipo de vehículo desconocido"),
        ({"documento": "  "}, "número de lote o de factura"),
        ({"fecha": str(date.today() + timedelta(days=1))}, "no puede ser futura"),
        ({"precio_usd": "0"}, "El precio debe ser mayor que cero"),
        ({"precio_usd": "abc"}, "El precio no es un número válido"),
        ({"comision_usd": "-1"}, "La comisión no puede ser negativo"),
        ({"arrastre_usd": "1.0000001"}, "El arrastre admite hasta 6 decimales"),
    ],
)
def test_rechaza_compras_invalidas_sin_crear_nada(cliente, subasta, cambios, mensaje):
    respuesta = cliente.post(URL, json=_compra(subasta, **cambios))

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    _nada_creado()


def test_solo_a_proveedores_del_exterior(cliente, agente):
    respuesta = cliente.post(URL, json=_compra(agente))

    assert respuesta.status_code == 400
    assert "proveedor del exterior" in respuesta.json()["detail"]
    _nada_creado()


def test_rechaza_proveedor_inexistente_y_montos_numericos(cliente, subasta):
    assert cliente.post(URL, json=_compra(999)).status_code == 404
    assert cliente.post(URL, json=_compra(subasta, precio_usd=8500.0)).status_code == 422
    _nada_creado()


# ── Consulta ──────────────────────────────────────────────────────────────────


def test_lista_y_consulta_las_compras(cliente, subasta):
    otro_vin = "JHMCM56557C404453"
    primera = cliente.post(URL, json=_compra(subasta)).json()
    segunda = cliente.post(URL, json=_compra(subasta, vin=otro_vin, documento="LOT-2")).json()

    assert [c["id"] for c in cliente.get(URL).json()] == [segunda["id"], primera["id"]]
    assert [c["vin"] for c in cliente.get(URL, params={"vin": otro_vin.lower()}).json()] == [otro_vin]
    assert len(cliente.get(URL, params={"proveedor_id": subasta}).json()) == 2
    assert cliente.get(f"{URL}/{primera['id']}").json()["documento"] == "LOT-44871203"
    assert cliente.get(f"{URL}/999").status_code == 404


# ── Bitácora (HU-1.11) ────────────────────────────────────────────────────────


def test_la_compra_y_su_cuenta_por_pagar_se_auditan_con_el_vin(cliente, subasta):
    with SessionLocal() as db:
        desde = db.scalar(text("SELECT coalesce(max(id), 0) FROM bitacora"))

    compra = cliente.post(URL, json=_compra(subasta)).json()

    with SessionLocal() as db:
        registros = list(
            db.scalars(
                select(RegistroBitacora)
                .where(RegistroBitacora.id > desde, RegistroBitacora.accion == "crear")
                .order_by(RegistroBitacora.id)
            )
        )
    entidades = {r.entidad for r in registros}
    assert {"unidad", "compra_unidad", "cuenta_por_pagar", "partida"} <= entidades

    alta = next(r for r in registros if r.entidad == "compra_unidad")
    assert alta.registro_id == str(compra["id"])
    assert alta.vin == VIN
    assert alta.nuevos["partida_id"] == compra["partida_id"]
    assert alta.nuevos["total_usd"] == 9075

    cxp = next(r for r in registros if r.entidad == "cuenta_por_pagar")
    assert cxp.nuevos["compra_unidad_id"] == compra["id"]
    assert cxp.nuevos["gasto_importacion_id"] is None
