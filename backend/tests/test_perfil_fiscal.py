"""HU-1.01: perfil fiscal de la empresa en versiones con vigencia y tasas impositivas."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal
from app.modulos.configuracion import service

URL = "/api/v1/configuracion/perfil-fiscal"
URL_TASAS = "/api/v1/configuracion/tasas-impositivas"

PERFIL = {
    "vigente_desde": "2026-01-01",
    "razon_social": "Kilómetro Cero, Sociedad Anónima",
    "nombre_comercial": "Kilómetro Cero",
    "nit": "1234567-9",
    "direccion_fiscal": "Calzada Roosevelt 22-43 zona 11, Guatemala",
    "establecimiento_sat": 1,
    "regimen_isr": "sobre_utilidades",
    "agente_retencion_iva": True,
}


@pytest.fixture(autouse=True)
def tablas_limpias():
    """Vacía los perfiles y deja solo las tasas de la carga inicial (vigentes desde 2015)."""
    with SessionLocal() as db:
        db.execute(text("TRUNCATE perfil_fiscal RESTART IDENTITY"))
        db.execute(text("DELETE FROM tasa_impositiva WHERE vigente_desde > '2015-01-01'"))
        db.commit()


def test_registra_el_perfil_fiscal(cliente):
    respuesta = cliente.post(URL, json=PERFIL)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["nit"] == "12345679"
    assert cuerpo["nit_formateado"] == "1234567-9"
    assert cuerpo["regimen_isr"] == "sobre_utilidades"
    assert cuerpo["agente_retencion_iva"] is True
    assert cuerpo["agente_retencion_isr"] is False
    assert cuerpo["tasas_del_regimen"] == ["IVA_GENERAL", "ISR_UTILIDADES", "ISO", "UMBRAL_CF"]


@pytest.mark.parametrize(
    ("cambio", "mensaje"),
    [
        ({"razon_social": "  "}, "La razón social es obligatorio"),
        ({"nombre_comercial": ""}, "El nombre comercial es obligatorio"),
        ({"direccion_fiscal": " "}, "La dirección fiscal es obligatorio"),
        ({"nit": "1234567-8"}, "dígito verificador"),
    ],
)
def test_exige_los_datos_de_la_empresa(cliente, cambio, mensaje):
    respuesta = cliente.post(URL, json={**PERFIL, **cambio})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_rechaza_regimen_y_establecimiento_invalidos(cliente):
    assert cliente.post(URL, json={**PERFIL, "regimen_isr": "general"}).status_code == 422
    assert cliente.post(URL, json={**PERFIL, "establecimiento_sat": 0}).status_code == 422


def test_cada_cambio_es_una_version_y_las_fechas_anteriores_conservan_su_perfil(cliente):
    assert cliente.post(URL, json=PERFIL).status_code == 201
    cambio = {**PERFIL, "vigente_desde": "2026-07-01", "regimen_isr": "opcional_simplificado"}
    assert cliente.post(URL, json=cambio).status_code == 201

    antes = cliente.get(f"{URL}/vigente", params={"fecha": "2026-06-30"}).json()
    despues = cliente.get(f"{URL}/vigente", params={"fecha": "2026-07-01"}).json()
    assert antes["regimen_isr"] == "sobre_utilidades"
    assert despues["regimen_isr"] == "opcional_simplificado"
    assert despues["tasas_del_regimen"] == [
        "IVA_GENERAL",
        "ISR_SIMPLIFICADO_1",
        "ISR_SIMPLIFICADO_2",
        "UMBRAL_CF",
    ]
    assert [p["vigente_desde"] for p in cliente.get(URL).json()] == ["2026-07-01", "2026-01-01"]


@pytest.mark.parametrize("fecha", ["2026-01-01", "2025-12-31"])
def test_un_cambio_no_puede_reescribir_fechas_ya_cubiertas(cliente, fecha):
    assert cliente.post(URL, json=PERFIL).status_code == 201

    respuesta = cliente.post(URL, json={**PERFIL, "vigente_desde": fecha})

    assert respuesta.status_code == 400
    assert "posterior a la del perfil actual (01/01/2026)" in respuesta.json()["detail"]


def test_sin_perfil_vigente_responde_404(cliente):
    assert cliente.post(URL, json=PERFIL).status_code == 201

    respuesta = cliente.get(f"{URL}/vigente", params={"fecha": "2025-12-31"})

    assert respuesta.status_code == 404


def test_el_perfil_queda_en_la_bitacora(cliente):
    with SessionLocal() as db:
        desde = db.scalar(select(func.coalesce(func.max(RegistroBitacora.id), 0)))
    creado = cliente.post(URL, json=PERFIL).json()

    with SessionLocal() as db:
        registro = db.scalars(
            select(RegistroBitacora).where(
                RegistroBitacora.id > desde,
                RegistroBitacora.entidad == "perfil_fiscal",
                RegistroBitacora.registro_id == str(creado["id"]),
            )
        ).one()
    assert registro.accion == "crear"
    assert registro.nuevos["regimen_isr"] == "sobre_utilidades"


# ── Tasas impositivas ──────────────────────────────────────────────────────────


def test_la_carga_inicial_trae_las_tasas_vigentes(cliente):
    vigentes = {t["tipo"]: t for t in cliente.get(f"{URL_TASAS}/vigentes").json()}

    assert vigentes["IVA_GENERAL"]["tasa"] == "0.120000"
    assert vigentes["IVA_GENERAL"]["porcentaje"] == "12"
    assert vigentes["ISR_SIMPLIFICADO_1"]["porcentaje"] == "5"
    assert vigentes["ISR_SIMPLIFICADO_1"]["monto_limite"] == "30000.000000"
    assert vigentes["ISR_SIMPLIFICADO_2"]["porcentaje"] == "7"
    assert vigentes["ISR_UTILIDADES"]["porcentaje"] == "25"
    assert vigentes["ISO"]["porcentaje"] == "1"
    assert vigentes["UMBRAL_CF"]["porcentaje"] is None
    assert vigentes["UMBRAL_CF"]["monto_limite"] == "2500.000000"


def test_un_cambio_de_tasa_no_altera_las_fechas_anteriores(cliente):
    respuesta = cliente.post(
        URL_TASAS, json={"tipo": "IVA_GENERAL", "porcentaje": "12.5", "vigente_desde": "2027-01-01"}
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["tasa"] == "0.125000"

    def iva(fecha: str) -> str:
        vigentes = cliente.get(f"{URL_TASAS}/vigentes", params={"fecha": fecha}).json()
        return next(t["porcentaje"] for t in vigentes if t["tipo"] == "IVA_GENERAL")

    assert iva("2026-12-31") == "12"
    assert iva("2027-01-01") == "12.5"
    with SessionLocal() as db:
        assert service.tasa_vigente(db, "IVA_GENERAL", date(2026, 6, 15)).tasa == Decimal("0.12")
        assert service.tasa_vigente(db, "IVA_GENERAL", date(2027, 6, 15)).tasa == Decimal("0.125")


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        ({"tipo": "IVA_GENERAL"}, "Indique el porcentaje"),
        ({"tipo": "IVA_GENERAL", "porcentaje": "0"}, "mayor que cero"),
        ({"tipo": "IVA_GENERAL", "porcentaje": "101"}, "no puede ser mayor que 100"),
        ({"tipo": "IVA_GENERAL", "porcentaje": "doce"}, "debe ser un número"),
        ({"tipo": "IVA_GENERAL", "porcentaje": "12", "monto_limite": "10"}, "no lleva monto"),
        ({"tipo": "ISR_SIMPLIFICADO_1", "porcentaje": "5"}, "Indique el monto límite"),
        ({"tipo": "UMBRAL_CF", "porcentaje": "1", "monto_limite": "2500"}, "no lleva porcentaje"),
        ({"tipo": "IVA_GENERAL", "porcentaje": "12", "vigente_desde": "2015-01-01"}, "posterior"),
    ],
)
def test_valida_las_tasas(cliente, datos, mensaje):
    respuesta = cliente.post(URL_TASAS, json={"vigente_desde": "2027-01-01", **datos})

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


def test_el_porcentaje_se_envia_como_texto(cliente):
    respuesta = cliente.post(
        URL_TASAS, json={"tipo": "IVA_GENERAL", "porcentaje": 12, "vigente_desde": "2027-01-01"}
    )

    assert respuesta.status_code == 422
