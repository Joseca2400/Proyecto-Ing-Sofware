"""HU-1.05 (versión delgada): unidades por VIN, ficha mínima, estados e historial."""

from datetime import date

import pytest
from sqlalchemy import select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.unidades.service import digito_verificador, validar_vin

URL = "/api/v1/unidades"
VIN = "1HGCM82633A004352"


def _unidad(**cambios) -> dict:
    return {
        "vin": VIN,
        "marca": "Honda",
        "linea": "Accord",
        "modelo": 2003,
        "color": "Gris",
        "tipo_vehiculo": "sedan",
        "linea_negocio": "alquiler",
        **cambios,
    }


@pytest.fixture(autouse=True)
def tablas_vacias():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE unidad RESTART IDENTITY CASCADE"))
        db.commit()


# ── Validación del VIN ────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("vin", "digito"),
    [
        ("1HGCM82633A004352", "3"),
        ("1M8GDM9AXKP042788", "X"),  # residuo 10
        ("3VWFE21C04M000001", "0"),
        ("1FTFW1ET9DFC10312", "9"),
    ],
)
def test_calcula_el_digito_verificador(vin, digito):
    assert digito_verificador(vin) == digito
    assert validar_vin(vin) == vin


def test_normaliza_espacios_y_minusculas():
    assert validar_vin("  1hgcm82633a004352 ") == VIN


@pytest.mark.parametrize(
    ("vin", "mensaje"),
    [
        ("1HGCM82633A00435", "17"),  # 16 caracteres
        ("1HGCM82633A0043521", "17"),  # 18 caracteres
        ("1HGCM82633A0O4352", "sin I, O ni Q"),
        ("1HGCM82633A0I4352", "sin I, O ni Q"),
        ("1HGCQ82633A004352", "sin I, O ni Q"),
        ("1HGCM8263-A004352", "17"),
        ("1HGCM82623A004352", "posición 9 debería ser 3"),
    ],
)
def test_rechaza_vin_invalido(vin, mensaje):
    with pytest.raises(ErrorNegocio, match=mensaje):
        validar_vin(vin)


def test_el_verificador_solo_se_exige_a_vin_de_norteamerica():
    # Un VIN japonés (empieza con J) no está obligado al dígito verificador.
    assert validar_vin("JHMCM56567C404453") == "JHMCM56567C404453"


# ── Alta y consulta ───────────────────────────────────────────────────────────


def test_registra_unidad_con_su_ficha_y_el_alta_en_el_historial(cliente):
    respuesta = cliente.post(URL, json=_unidad(vin=" 1hgcm82633a004352 ", documento="Factura Copart 77"))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["vin"] == VIN
    assert cuerpo["marca"] == "Honda"
    assert cuerpo["linea"] == "Accord"
    assert cuerpo["modelo"] == 2003
    assert cuerpo["color"] == "Gris"
    assert cuerpo["tipo_vehiculo"] == "sedan"
    assert cuerpo["linea_negocio"] == "alquiler"
    assert cuerpo["estado"] == "en_transito"

    [alta] = cliente.get(f"{URL}/{VIN}/historial").json()
    assert alta["estado_anterior"] is None
    assert alta["estado_nuevo"] == "en_transito"
    assert alta["documento"] == "Factura Copart 77"
    assert alta["usuario_id"] is None  # las rutas aún no exigen sesión
    assert alta["fecha"]


def test_el_alta_sin_documento_queda_como_alta_de_la_unidad(cliente):
    cliente.post(URL, json=_unidad(estado="lista", linea_negocio=None))

    [alta] = cliente.get(f"{URL}/{VIN}/historial").json()
    assert alta["estado_nuevo"] == "lista"
    assert alta["documento"] == "Alta de la unidad"
    assert cliente.get(f"{URL}/{VIN}").json()["linea_negocio"] is None


def test_el_vin_es_unico(cliente):
    assert cliente.post(URL, json=_unidad()).status_code == 201

    repetida = cliente.post(URL, json=_unidad(vin=VIN.lower(), marca="Otra"))

    assert repetida.status_code == 409
    assert VIN in repetida.json()["detail"]


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"vin": "1HGCM82623A004352"}, "dígito verificador"),
        ({"vin": "1HGCM82633A0O4352"}, "sin I, O ni Q"),
        ({"marca": "  "}, "obligatorios"),
        ({"color": ""}, "obligatorios"),
        ({"modelo": 1975}, "año"),
        ({"modelo": date.today().year + 2}, "año"),
        ({"tipo_vehiculo": "tanque"}, "Tipo de vehículo"),
        ({"linea_negocio": "sucursal"}, "Línea de negocio desconocida"),
        ({"estado": "vendida"}, "no puede darse de alta"),
        ({"estado": "recuperada"}, "no puede darse de alta"),
    ],
)
def test_valida_la_ficha(cliente, cambios, mensaje):
    respuesta = cliente.post(URL, json=_unidad(**cambios))

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert cliente.get(URL).json() == []


def test_rechaza_estado_desconocido(cliente):
    assert cliente.post(URL, json=_unidad(estado="perdida")).status_code == 422


def test_lista_filtra_por_estado_y_texto(cliente):
    honda = cliente.post(URL, json=_unidad()).json()
    ford = cliente.post(
        URL,
        json=_unidad(vin="1FTFW1ET9DFC10312", marca="Ford", linea="F-150", tipo_vehiculo="pickup"),
    ).json()
    cliente.post(f"{URL}/{ford['vin']}/estado", json={"estado": "en_aduana", "documento": "BL 123"})

    assert [u["vin"] for u in cliente.get(URL).json()] == [ford["vin"], honda["vin"]]
    assert [u["vin"] for u in cliente.get(URL, params={"estado": "en_aduana"}).json()] == [ford["vin"]]
    assert [u["vin"] for u in cliente.get(URL, params={"buscar": "f-15"}).json()] == [ford["vin"]]
    assert [u["vin"] for u in cliente.get(URL, params={"buscar": "a004"}).json()] == [honda["vin"]]
    assert cliente.get(URL, params={"buscar": "%"}).json() == []


def test_consulta_por_vin(cliente):
    creada = cliente.post(URL, json=_unidad()).json()

    assert cliente.get(f"{URL}/{VIN.lower()}").json() == creada
    faltante = cliente.get(f"{URL}/1FTFW1ET9DFC10312")
    assert faltante.status_code == 404
    assert cliente.get(f"{URL}/1FTFW1ET9DFC10312/historial").status_code == 404


def test_catalogos_usan_las_lineas_de_negocio_de_configuracion(cliente):
    from app.modulos.configuracion.service import LINEAS_NEGOCIO

    cuerpo = cliente.get(f"{URL}/catalogos").json()

    assert cuerpo["lineas_negocio"] == list(LINEAS_NEGOCIO)
    assert cuerpo["estados"] == [
        "en_transito", "en_aduana", "en_taller", "lista", "en_flota", "en_venta", "vendida", "recuperada",
    ]  # fmt: skip
    assert "sedan" in cuerpo["tipos_vehiculo"]


# ── Estados e historial ───────────────────────────────────────────────────────


def _cambiar(cliente, estado: str, documento: str = "Documento"):
    return cliente.post(f"{URL}/{VIN}/estado", json={"estado": estado, "documento": documento})


def test_cada_cambio_de_estado_queda_en_el_historial(cliente):
    cliente.post(URL, json=_unidad())
    for estado, documento in [
        ("en_aduana", "BL MSCU1234567"),
        ("en_taller", "DUCA 4-2026-000123"),
        ("lista", "Orden de taller 15"),
        ("en_venta", "Memo gerencia 3"),
        ("vendida", "Factura FEL A-1"),
        ("recuperada", "Acta de recuperación 1"),
    ]:
        respuesta = _cambiar(cliente, estado, documento)
        assert respuesta.status_code == 200
        assert respuesta.json()["estado"] == estado

    historial = cliente.get(f"{URL}/{VIN}/historial").json()
    assert [(c["estado_anterior"], c["estado_nuevo"]) for c in historial] == [
        (None, "en_transito"),
        ("en_transito", "en_aduana"),
        ("en_aduana", "en_taller"),
        ("en_taller", "lista"),
        ("lista", "en_venta"),
        ("en_venta", "vendida"),
        ("vendida", "recuperada"),
    ]
    assert historial[1]["documento"] == "BL MSCU1234567"
    assert cliente.get(f"{URL}/{VIN}").json()["estado"] == "recuperada"


@pytest.mark.parametrize(
    ("previos", "estado", "mensaje"),
    [
        ([], "en_transito", "ya está en estado"),
        ([], "recuperada", "Solo una unidad vendida"),
        (["en_venta", "vendida"], "en_flota", "solo puede pasar a recuperada"),
    ],
)
def test_rechaza_cambios_sin_sentido(cliente, previos, estado, mensaje):
    cliente.post(URL, json=_unidad())
    for previo in previos:
        assert _cambiar(cliente, previo).status_code == 200

    respuesta = _cambiar(cliente, estado)

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
    assert len(cliente.get(f"{URL}/{VIN}/historial").json()) == len(previos) + 1


def test_el_cambio_de_estado_exige_documento(cliente):
    cliente.post(URL, json=_unidad())

    respuesta = _cambiar(cliente, "en_aduana", "   ")

    assert respuesta.status_code == 400
    assert "documento" in respuesta.json()["detail"]
    assert cliente.get(f"{URL}/{VIN}").json()["estado"] == "en_transito"


def test_cambio_de_estado_de_unidad_inexistente(cliente):
    assert _cambiar(cliente, "en_aduana").status_code == 404


def test_la_base_impide_un_estado_desconocido(cliente):
    cliente.post(URL, json=_unidad())

    with SessionLocal() as db, pytest.raises(Exception, match="ck_unidad_estado"):
        db.execute(text("UPDATE unidad SET estado = 'perdida'"))


# ── Bitácora (HU-1.11) ────────────────────────────────────────────────────────


def test_alta_y_cambio_de_estado_se_auditan_con_el_vin(cliente):
    with SessionLocal() as db:
        desde = db.scalar(text("SELECT coalesce(max(id), 0) FROM bitacora"))

    unidad = cliente.post(URL, json=_unidad()).json()
    _cambiar(cliente, "en_aduana", "BL 1")

    with SessionLocal() as db:
        registros = list(
            db.scalars(
                select(RegistroBitacora).where(RegistroBitacora.id > desde).order_by(RegistroBitacora.id)
            )
        )
    de_unidad = [r for r in registros if r.entidad == "unidad"]
    assert [r.accion for r in de_unidad] == ["crear", "modificar"]
    assert all(r.vin == VIN and r.usuario_id is None for r in de_unidad)
    assert de_unidad[0].registro_id == str(unidad["id"])
    assert de_unidad[1].anteriores["estado"] == "en_transito"
    assert de_unidad[1].nuevos["estado"] == "en_aduana"

    historial = [r for r in registros if r.entidad == "cambio_estado_unidad"]
    assert [r.nuevos["estado_nuevo"] for r in historial] == ["en_transito", "en_aduana"]
