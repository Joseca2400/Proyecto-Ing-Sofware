"""HU-4.07 (versión delgada): etapas de importación en orden y listado por etapa con días y costo."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal
from app.modulos.configuracion.semilla import crear_catalogo_inicial


@pytest.fixture
def cliente(cliente_contador):
    """Las rutas exigen sesión (HU-1.09): las reglas se prueban como contador."""
    return cliente_contador


URL = "/api/v1/unidades"
URL_ETAPAS = f"{URL}/etapas-importacion"
URL_PROVEEDORES = "/api/v1/compras/proveedores"
URL_COMPRAS = "/api/v1/compras/compras-unidades"
URL_GASTOS = "/api/v1/compras/gastos-importacion"
VIN = "1HGCM82633A004352"
OTRO_VIN = "1FTFW1ET9DFC10312"
FECHA = "2026-10-20"


def _unidad(vin: str = VIN, **cambios) -> dict:
    return {
        "vin": vin,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2007,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        **cambios,
    }


def _cambiar(cliente, estado: str, vin: str = VIN):
    return cliente.post(f"{URL}/{vin}/estado", json={"estado": estado, "documento": f"Doc {estado}"})


def _historial(cliente, vin: str = VIN) -> list[str]:
    return [c["estado_nuevo"] for c in cliente.get(f"{URL}/{vin}/historial").json()]


def _atrasar_ultimo_cambio(vin: str, dias: int) -> None:
    """Simula que la unidad entró a su etapa actual hace `dias` días (y una hora)."""
    fecha = datetime.now(UTC) - timedelta(days=dias, hours=1)
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE cambio_estado_unidad SET fecha = :fecha WHERE id = (SELECT max(c.id)"
                " FROM cambio_estado_unidad c JOIN unidad u ON u.id = c.unidad_id WHERE u.vin = :vin)"
            ),
            {"fecha": fecha, "vin": vin},
        )
        db.commit()


@pytest.fixture(autouse=True)
def tablas_vacias():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE proveedor, unidad, partida RESTART IDENTITY CASCADE"))
        db.commit()


# ── Criterio 1: el orden de las etapas ────────────────────────────────────────


def test_avanza_en_orden_hasta_lista_con_historial_y_bitacora(cliente):
    with SessionLocal() as db:
        desde = db.scalar(text("SELECT coalesce(max(id), 0) FROM bitacora"))
    cliente.post(URL, json=_unidad())
    for estado in ("en_aduana", "en_taller", "lista"):
        respuesta = _cambiar(cliente, estado)
        assert respuesta.status_code == 200, respuesta.json()
        assert respuesta.json()["estado"] == estado

    assert _historial(cliente) == ["en_transito", "en_aduana", "en_taller", "lista"]
    with SessionLocal() as db:
        cambios = (
            db.query(RegistroBitacora)
            .filter_by(entidad="cambio_estado_unidad")
            .filter(RegistroBitacora.id > desde)
            .order_by(RegistroBitacora.id)
            .all()
        )
    assert [r.nuevos["estado_nuevo"] for r in cambios] == ["en_transito", "en_aduana", "en_taller", "lista"]


@pytest.mark.parametrize(
    ("previos", "estado", "mensaje"),
    [
        ([], "en_taller", "solo puede pasar a en aduana"),  # se salta la aduana
        ([], "lista", "solo puede pasar a en aduana"),
        ([], "en_flota", "solo puede pasar a en aduana"),  # sale de importación sin terminarla
        (["en_aduana"], "en_transito", "solo puede pasar a en taller"),  # regresa
        (["en_aduana"], "lista", "solo puede pasar a en taller"),
        (["en_aduana", "en_taller"], "en_aduana", "solo puede pasar a lista"),
        (["en_aduana", "en_taller"], "en_venta", "solo puede pasar a lista"),
        (["en_aduana", "en_taller", "lista"], "en_taller", "no puede volver a en taller"),
        (["en_aduana", "en_taller", "lista"], "en_aduana", "no puede volver a en aduana"),
    ],
)
def test_no_se_salta_etapas_ni_regresa(cliente, previos, estado, mensaje):
    cliente.post(URL, json=_unidad())
    for previo in previos:
        assert _cambiar(cliente, previo).status_code == 200

    respuesta = _cambiar(cliente, estado)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert _historial(cliente) == ["en_transito", *previos]


def test_la_flota_entra_al_taller_pero_no_vuelve_a_lista(cliente):
    """Fuera de importación el taller es mantenimiento (HU-5.01): no vuelve a lista ni a aduana."""
    # De lista a la flota solo se pasa con el alta (HU-3.01): la unidad se carga ya en flota.
    cliente.post(URL, json=_unidad(estado="en_flota"))
    assert _cambiar(cliente, "en_taller").status_code == 200

    respuesta = _cambiar(cliente, "lista")

    assert respuesta.status_code == 400
    assert "ya terminó la importación" in respuesta.json()["detail"]
    assert _cambiar(cliente, "en_flota").status_code == 200


def test_una_unidad_cargada_en_aduana_sigue_el_orden_desde_ahi(cliente):
    cliente.post(URL, json=_unidad(estado="en_aduana"))

    assert _cambiar(cliente, "lista").status_code == 400
    assert _cambiar(cliente, "en_taller").status_code == 200


def test_una_unidad_dada_de_alta_en_flota_no_entra_a_importacion(cliente):
    cliente.post(URL, json=_unidad(estado="en_flota"))

    assert _cambiar(cliente, "en_aduana").status_code == 400
    assert _cambiar(cliente, "en_taller").status_code == 200
    assert _cambiar(cliente, "en_flota").status_code == 200


# ── Criterio 4: listado por etapa con días y costo ────────────────────────────


@pytest.fixture
def con_compra_y_gastos(cliente):
    """Compra en USD de VIN con un gasto que suma al costo y otro que es crédito fiscal."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
    tipo = cliente.post("/api/v1/configuracion/tipos-cambio", json={"fecha": FECHA, "valor": "7.75"})
    assert tipo.status_code == 201
    subasta = cliente.post(
        URL_PROVEEDORES,
        json={
            "tipo": "exterior",
            "nombre": "Copart Inc.",
            "identificacion_fiscal": "94-2867490",
            "pais": "US",
            "rubro": "subasta",
            "moneda_habitual": "USD",
            "dias_credito": 30,
        },
    ).json()["id"]
    agente = cliente.post(
        URL_PROVEEDORES,
        json={
            "tipo": "local",
            "nombre": "Aduanas Express, S. A.",
            "nit": "1669394-9",
            "regimen": "general",
            "rubro": "agente_aduanal",
            "moneda_habitual": "GTQ",
            "dias_credito": 0,
        },
    ).json()["id"]
    compra = {
        **_unidad(),
        "proveedor_id": subasta,
        "fecha": FECHA,
        "documento": "LOT-1",
        "precio_usd": "8000.00",
    }
    assert cliente.post(URL_COMPRAS, json=compra).status_code == 201  # 62 000.00 GTQ
    for concepto, monto in (("agente_aduanal", "3500.00"), ("iva_importacion", "1020.00")):
        gasto = {
            "vin": VIN,
            "proveedor_id": agente,
            "fecha": FECHA,
            "documento": "F-1",
            "moneda": "GTQ",
            "concepto": concepto,
            "monto": monto,
        }
        assert cliente.post(URL_GASTOS, json=gasto).status_code == 201


def test_lista_las_unidades_por_etapa_con_dias_y_costo(cliente, con_compra_y_gastos):
    cliente.post(URL, json=_unidad(OTRO_VIN, marca="Ford", linea="F-150"))
    _cambiar(cliente, "en_aduana", OTRO_VIN)
    _atrasar_ultimo_cambio(VIN, 12)
    _atrasar_ultimo_cambio(OTRO_VIN, 3)

    cuerpo = cliente.get(URL_ETAPAS).json()

    assert cuerpo["etapas"] == [
        {"estado": "en_transito", "unidades": 1, "costo_total_gtq": "65500.000000"},
        {"estado": "en_aduana", "unidades": 1, "costo_total_gtq": "0.000000"},
        {"estado": "en_taller", "unidades": 0, "costo_total_gtq": "0.000000"},
        {"estado": "lista", "unidades": 0, "costo_total_gtq": "0.000000"},
    ]
    honda, ford = cuerpo["unidades"]
    assert (honda["vin"], honda["estado"], honda["dias_en_etapa"]) == (VIN, "en_transito", 12)
    assert honda["costo_total_gtq"] == "65500.000000"  # compra + agente aduanal, sin el IVA
    assert honda["siguiente_etapa"] == "en_aduana"
    assert (ford["vin"], ford["estado"], ford["dias_en_etapa"]) == (OTRO_VIN, "en_aduana", 3)
    assert ford["siguiente_etapa"] == "en_taller"


def test_el_costo_coincide_con_el_de_la_ficha(cliente, con_compra_y_gastos):
    ficha = cliente.get(f"{URL_GASTOS}/unidad/{VIN}").json()

    assert cliente.get(URL_ETAPAS).json()["unidades"][0]["costo_total_gtq"] == ficha["costo_total_gtq"]


def test_los_dias_se_reinician_al_cambiar_de_etapa(cliente):
    cliente.post(URL, json=_unidad())
    _atrasar_ultimo_cambio(VIN, 20)
    assert cliente.get(URL_ETAPAS).json()["unidades"][0]["dias_en_etapa"] == 20

    _cambiar(cliente, "en_aduana")

    unidad = cliente.get(URL_ETAPAS).json()["unidades"][0]
    assert (unidad["estado"], unidad["dias_en_etapa"]) == ("en_aduana", 0)


def test_dentro_de_la_etapa_primero_la_que_lleva_mas_dias(cliente):
    for vin, dias in ((VIN, 2), (OTRO_VIN, 9)):
        cliente.post(URL, json=_unidad(vin))
        _atrasar_ultimo_cambio(vin, dias)

    assert [u["vin"] for u in cliente.get(URL_ETAPAS).json()["unidades"]] == [OTRO_VIN, VIN]


def test_filtra_por_etapa_y_excluye_lo_que_salio_de_importacion(cliente):
    cliente.post(URL, json=_unidad())
    for estado in ("en_aduana", "en_taller", "lista"):
        _cambiar(cliente, estado)
    cliente.post(URL, json=_unidad(OTRO_VIN, estado="en_flota"))
    _cambiar(cliente, "en_taller", OTRO_VIN)  # mantenimiento: no es importación

    todas = cliente.get(URL_ETAPAS).json()
    assert [(u["vin"], u["estado"], u["siguiente_etapa"]) for u in todas["unidades"]] == [
        (VIN, "lista", None)
    ]

    solo_taller = cliente.get(URL_ETAPAS, params={"etapa": "en_taller"}).json()
    assert solo_taller["unidades"] == []
    assert [e["estado"] for e in solo_taller["etapas"]] == ["en_taller"]


def test_rechaza_una_etapa_que_no_es_de_importacion(cliente):
    assert cliente.get(URL_ETAPAS, params={"etapa": "en_flota"}).status_code == 422
