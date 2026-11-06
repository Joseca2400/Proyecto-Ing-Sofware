from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal, engine, get_db
from app.comun.errores import ErrorNegocio
from app.main import app
from app.modulos.configuracion import service
from app.modulos.configuracion.models import Cuenta
from app.modulos.configuracion.semilla import CATALOGO, crear_catalogo_inicial
from app.modulos.seguridad.semilla import CUENTAS, crear_cuentas_iniciales

CLAVE = "Prueba-2026!"
AUXILIAR, CONTADOR, _, GERENCIA = (c[0] for c in CUENTAS)


@pytest.fixture(scope="module", autouse=True)
def datos():
    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE)
        crear_catalogo_inicial(db)


def _entrar(cliente, correo):
    token = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _id(codigo):
    with SessionLocal() as db:
        return db.query(Cuenta).filter_by(codigo=codigo).one().id


def test_la_semilla_es_idempotente_y_arma_la_jerarquia():
    with SessionLocal() as db:
        assert crear_catalogo_inicial(db) == 0
        cuentas = {c.codigo: c for c in db.query(Cuenta)}
    assert len(cuentas) == len(CATALOGO)
    assert cuentas["1.1.01.03"].nivel == 4
    assert cuentas["1.1.01.03"].padre_id == cuentas["1.1.01"].id
    assert cuentas["1.1.01.03"].monetaria_usd
    assert all(
        c.es_detalle == (not any(o.padre_id == c.id for o in cuentas.values())) for c in cuentas.values()
    )


def test_cualquier_rol_consulta_el_catalogo_ordenado_y_sin_sesion_no(cliente):
    assert cliente.get("/api/v1/configuracion/cuentas").status_code == 401
    cuentas = cliente.get("/api/v1/configuracion/cuentas", headers=_entrar(cliente, GERENCIA)).json()
    codigos = [c["codigo"] for c in cuentas]
    assert codigos == sorted(codigos)
    detalle = cliente.get(
        "/api/v1/configuracion/cuentas?solo_detalle=true", headers=_entrar(cliente, AUXILIAR)
    ).json()
    assert detalle and all(c["es_detalle"] for c in detalle)


def test_solo_el_contador_crea_cuentas(cliente):
    cuerpo = {"codigo": "6.1.03", "nombre": "Papelería", "tipo": "gasto", "naturaleza": "deudora"}
    cuerpo["padre_id"] = _id("6.1")
    assert (
        cliente.post(
            "/api/v1/configuracion/cuentas", json=cuerpo, headers=_entrar(cliente, AUXILIAR)
        ).status_code
        == 403
    )
    creada = cliente.post("/api/v1/configuracion/cuentas", json=cuerpo, headers=_entrar(cliente, CONTADOR))
    assert creada.status_code == 201
    assert creada.json()["nivel"] == 3
    repetida = cliente.post("/api/v1/configuracion/cuentas", json=cuerpo, headers=_entrar(cliente, CONTADOR))
    assert repetida.status_code == 409


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"padre_id": "detalle"}, "detalle no puede tener"),
        ({"padre_id": "otro_tipo"}, "mismo tipo"),
        ({"tipo": "inventado"}, "desconocidos"),
        ({"codigo": " "}, "obligatorios"),
        ({"vin": "obligatorio", "es_detalle": False}, "solo se definen en cuentas de detalle"),
    ],
)
def test_alta_de_cuenta_rechazos(cambios, mensaje):
    valores = {"codigo": "9.9", "nombre": "X", "tipo": "gasto", "naturaleza": "deudora"}
    cambios = dict(cambios)
    if cambios.get("padre_id") == "detalle":
        cambios["padre_id"] = _id("6.1.01")
    elif cambios.get("padre_id") == "otro_tipo":
        cambios["padre_id"] = _id("1.1")
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match=mensaje):
        service.crear_cuenta(db, **{**valores, **cambios})


def test_definir_dimensiones_por_api(cliente):
    ruta = f"/api/v1/configuracion/cuentas/{_id('6.1.02')}/dimensiones"
    cuerpo = {"linea_obligatoria": True, "vin": "opcional", "linea_defecto": "taller"}
    assert cliente.put(ruta, json=cuerpo, headers=_entrar(cliente, AUXILIAR)).status_code == 403
    respuesta = cliente.put(ruta, json=cuerpo, headers=_entrar(cliente, CONTADOR))
    assert respuesta.json()["vin"] == "opcional"
    assert respuesta.json()["linea_defecto"] == "taller"
    mala = cliente.put(ruta, json={**cuerpo, "linea_defecto": "sucursal"}, headers=_entrar(cliente, CONTADOR))
    assert mala.status_code == 422


def test_la_cuenta_que_exige_vin_no_deja_guardar_sin_el():
    with SessionLocal() as db:
        transito = _id("1.1.04.01")
        with pytest.raises(ErrorNegocio, match="exige el VIN"):
            service.resolver_dimensiones(db, transito, "venta", None)
        assert service.resolver_dimensiones(db, transito, "venta", "1HGCM82633A004352") == "venta"


def test_la_linea_por_defecto_se_aplica_y_la_obligatoria_se_exige():
    with SessionLocal() as db:
        assert service.resolver_dimensiones(db, _id("4.1"), None, "1HGCM82633A004352") == "alquiler"
        service.definir_dimensiones(db, _id("1.1.02.01"), True, service.VIN_NO_APLICA, None)
        with pytest.raises(ErrorNegocio, match="exige línea de negocio"):
            service.resolver_dimensiones(db, _id("1.1.02.01"), None, None)
        with pytest.raises(ErrorNegocio, match="Línea de negocio desconocida"):
            service.resolver_dimensiones(db, _id("4.1"), "sucursal", "1HGCM82633A004352")


def test_una_cuenta_de_agrupacion_no_recibe_movimientos():
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="agrupación"):
        service.resolver_dimensiones(db, _id("1.1.01"), "administracion", None)


@pytest.mark.parametrize(("campo", "valor"), [("codigo", "X" * 31), ("nombre", "X" * 201)])
def test_limites_de_texto_se_rechazan_antes_de_persistir(cliente, campo, valor):
    datos = {"codigo": "limites", "nombre": "Límites", "tipo": "gasto", "naturaleza": "deudora"}
    datos[campo] = valor
    respuesta = cliente.post("/api/v1/configuracion/cuentas", json=datos, headers=_entrar(cliente, CONTADOR))
    assert respuesta.status_code == 422
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="hasta 30"):
        service.crear_cuenta(db, **datos)


def test_limites_exactos_y_espacios_exteriores(cliente):
    datos = {
        "codigo": " C" + "X" * 29 + " ",
        "nombre": " " + "N" * 200 + " ",
        "tipo": "gasto",
        "naturaleza": "deudora",
    }
    respuesta = cliente.post("/api/v1/configuracion/cuentas", json=datos, headers=_entrar(cliente, CONTADOR))
    assert respuesta.status_code == 201
    assert respuesta.json()["codigo"] == datos["codigo"].strip()
    assert respuesta.json()["nombre"] == datos["nombre"].strip()


@pytest.mark.parametrize("vin", [None, "", "   ", "\t\n"])
def test_vin_obligatorio_rechaza_valores_vacios(vin):
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="exige el VIN"):
        service.resolver_dimensiones(db, _id("1.1.04.01"), "venta", vin)


def test_vin_no_aplica_rechaza_unidad_y_opcional_admite_ausencia():
    with SessionLocal() as db:
        with pytest.raises(ErrorNegocio, match="no admite VIN"):
            service.resolver_dimensiones(db, _id("1.1.01.01"), None, "1HGCM82633A004352")
        assert service.resolver_dimensiones(db, _id("1.1.01.01"), None, "  ") == "administracion"
        assert service.resolver_dimensiones(db, _id("1.1.03.02"), "venta", None) == "venta"
        assert service.resolver_dimensiones(db, _id("1.1.03.02"), "venta", "1HGCM82633A004352") == "venta"


def test_altas_simultaneas_del_mismo_codigo_devuelven_201_y_409(cliente):
    encabezado = _entrar(cliente, CONTADOR)
    barrera = Barrier(2)

    class SesionConcurrente(Session):
        def scalar(self, consulta, *args, **kwargs):
            resultado = super().scalar(consulta, *args, **kwargs)
            # Ambas transacciones deben haber comprobado que el código todavía no existe.
            if "SELECT cuentas.id" in str(consulta):
                barrera.wait(timeout=10)
            return resultado

    def db_concurrente():
        with SesionConcurrente(bind=engine, autoflush=False, expire_on_commit=False) as db:
            yield db

    def crear(_):
        with TestClient(app, raise_server_exceptions=False) as c:
            return c.post(
                "/api/v1/configuracion/cuentas",
                headers=encabezado,
                json={
                    "codigo": "concurrente",
                    "nombre": "Concurrente",
                    "tipo": "gasto",
                    "naturaleza": "deudora",
                },
            ).status_code

    app.dependency_overrides[get_db] = db_concurrente
    try:
        with ThreadPoolExecutor(max_workers=2) as ejecutor:
            assert sorted(ejecutor.map(crear, range(2))) == [201, 409]
    finally:
        app.dependency_overrides.pop(get_db)
    with SessionLocal() as db:
        cuenta = db.scalars(select(Cuenta).where(Cuenta.codigo == "concurrente")).one()
        assert (
            db.scalar(
                select(func.count())
                .select_from(RegistroBitacora)
                .where(RegistroBitacora.entidad == "cuentas", RegistroBitacora.registro_id == str(cuenta.id))
            )
            == 1
        )
