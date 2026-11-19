"""HU-1.09: administración de usuarios, bloqueo por intentos y renovación de la sesión."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.comun import config
from app.comun.db import SessionLocal
from app.main import app
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Sesion, Usuario
from app.modulos.seguridad.semilla import crear_cuentas_iniciales

CLAVE = "Prueba-2026!"
URL = "/api/v1/seguridad/usuarios"
GERENTE = "gerente.financiero@empresa.gt"


@pytest.fixture(scope="module", autouse=True)
def cuentas():
    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE)


def _login(correo, clave=CLAVE):
    return TestClient(app).post("/api/v1/seguridad/login", json={"correo": correo, "clave": clave})


def _cabecera(correo):
    return {"Authorization": f"Bearer {_login(correo).json()['token']}"}


@pytest.fixture(scope="module")
def gerente():
    return TestClient(app, headers=_cabecera(GERENTE))


def _alta(gerente, correo, rol="contador", clave=CLAVE):
    return gerente.post(URL, json={"correo": correo, "nombre": "Prueba", "rol": rol, "clave": clave})


def test_alta_y_el_nuevo_usuario_inicia_sesion(gerente):
    r = _alta(gerente, "Nuevo.Alta@empresa.gt")
    assert r.status_code == 201
    assert r.json()["correo"] == "nuevo.alta@empresa.gt" and r.json()["estado"] == "activo"
    assert "clave" not in r.text and "hash" not in r.text
    assert _login("nuevo.alta@empresa.gt").status_code == 200
    assert any(u["correo"] == "nuevo.alta@empresa.gt" for u in gerente.get(URL).json())


@pytest.mark.parametrize("clave", ["corta1A", "sin-mayuscula-1", "SIN-MINUSCULA-1", "Sin-digitos-aqui"])
def test_clave_debil_se_rechaza(gerente, clave):
    assert _alta(gerente, "debil@empresa.gt", clave=clave).status_code == 400


def test_alta_rechaza_correo_repetido_rol_desconocido_y_datos_vacios(gerente):
    assert _alta(gerente, "contador@empresa.gt").status_code == 409
    assert _alta(gerente, "rol.malo@empresa.gt", rol="dios").status_code == 400
    assert _alta(gerente, "sin-arroba").status_code == 400
    r = gerente.post(
        URL, json={"correo": "vacio@empresa.gt", "nombre": " ", "rol": "contador", "clave": CLAVE}
    )
    assert r.status_code == 400


def test_solo_el_gerente_financiero_administra(cliente):
    assert cliente.get(URL).status_code == 401
    contador = _cabecera("contador@empresa.gt")
    assert cliente.get(URL, headers=contador).status_code == 403
    assert cliente.post(f"{URL}/1/suspender", headers=contador).status_code == 403


def test_suspender_impide_login_y_mata_la_sesion_y_reactivar_lo_devuelve(gerente):
    correo = "suspendido@empresa.gt"
    uid = _alta(gerente, correo).json()["id"]
    cabecera = _cabecera(correo)
    r = gerente.post(f"{URL}/{uid}/suspender")
    assert r.status_code == 200 and r.json()["estado"] == "suspendido"
    assert _login(correo).status_code == 401
    assert TestClient(app).get("/api/v1/seguridad/yo", headers=cabecera).status_code == 401
    with SessionLocal() as db:
        assert db.query(Sesion).filter_by(usuario_id=uid).count() == 0
    assert gerente.post(f"{URL}/{uid}/reactivar").json()["estado"] == "activo"
    assert _login(correo).status_code == 200


def test_baja_es_definitiva_y_conserva_al_usuario(gerente):
    correo = "baja@empresa.gt"
    uid = _alta(gerente, correo).json()["id"]
    assert gerente.post(f"{URL}/{uid}/baja").json()["estado"] == "baja"
    assert _login(correo).status_code == 401
    assert gerente.post(f"{URL}/{uid}/reactivar").status_code == 409
    assert gerente.post(f"{URL}/{uid}/suspender").status_code == 409
    with SessionLocal() as db:
        assert db.get(Usuario, uid).baja_en is not None


def test_nadie_se_suspende_ni_se_da_de_baja_a_si_mismo(gerente):
    with SessionLocal() as db:
        propio = db.scalar(select(Usuario.id).where(Usuario.correo == GERENTE))
    assert gerente.post(f"{URL}/{propio}/suspender").status_code == 409
    assert gerente.post(f"{URL}/{propio}/baja").status_code == 409
    assert gerente.post(f"{URL}/999999/suspender").status_code == 404


def test_bloqueo_tras_intentos_fallidos_aun_con_la_clave_correcta_y_vence(gerente, monkeypatch):
    monkeypatch.setattr(config, "INTENTOS_MAXIMOS", 2)
    correo = "bloqueable@empresa.gt"
    uid = _alta(gerente, correo).json()["id"]
    mensajes = {_login(correo, "mala").json()["detail"] for _ in range(2)}
    mensajes.add(_login(correo).json()["detail"])  # clave correcta, pero bloqueado
    mensajes.add(_login("nadie@empresa.gt").json()["detail"])
    assert mensajes == {service.MENSAJE_LOGIN}
    assert next(u["estado"] for u in gerente.get(URL).json() if u["id"] == uid) == "bloqueado"
    # El bloqueo queda en la bitácora (sin actor: nadie tenía sesión).
    registros = gerente.get("/api/v1/seguridad/bitacora", params={"entidad": "usuarios"}).json()
    assert any(r["registro_id"] == str(uid) and r["nuevos"]["bloqueado_hasta"] for r in registros)
    with SessionLocal() as db:
        db.execute(
            update(Usuario)
            .where(Usuario.id == uid)
            .values(bloqueado_hasta=datetime.now(UTC) - timedelta(seconds=1))
        )
        db.commit()
    assert _login(correo).status_code == 200
    with SessionLocal() as db:
        assert db.get(Usuario, uid).intentos_fallidos == 0


def test_login_correcto_reinicia_el_contador(gerente, monkeypatch):
    monkeypatch.setattr(config, "INTENTOS_MAXIMOS", 2)
    correo = "reinicia@empresa.gt"
    uid = _alta(gerente, correo).json()["id"]
    _login(correo, "mala")
    assert _login(correo).status_code == 200
    _login(correo, "mala")  # sería el segundo seguido si no se hubiera reiniciado
    assert _login(correo).status_code == 200
    with SessionLocal() as db:
        assert db.get(Usuario, uid).bloqueado_hasta is None


def test_la_actividad_renueva_la_sesion():
    cabecera = _cabecera(GERENTE)
    token_hash = service._hash_token(cabecera["Authorization"].split()[1])
    cerca = datetime.now(UTC) + timedelta(minutes=10)
    with SessionLocal() as db:
        db.execute(update(Sesion).where(Sesion.token_hash == token_hash).values(expira_en=cerca))
        db.commit()
    # La petición que renueva la sesión sigue auditando con su actor (el commit va antes de fijarlo).
    cliente = TestClient(app, headers=cabecera)
    uid = _alta(cliente, "tras.renovar@empresa.gt").json()["id"]
    with SessionLocal() as db:
        nueva = db.get(Sesion, token_hash).expira_en
        yo = db.scalar(select(Usuario.id).where(Usuario.correo == GERENTE))
    assert nueva > datetime.now(UTC) + timedelta(minutes=config.SESION_MINUTOS - 2)
    registros = cliente.get("/api/v1/seguridad/bitacora", params={"entidad": "usuarios"}).json()
    assert next(r for r in registros if r["registro_id"] == str(uid))["usuario_id"] == yo


def test_la_bitacora_no_guarda_la_clave(gerente):
    uid = _alta(gerente, "auditado@empresa.gt").json()["id"]
    registros = gerente.get("/api/v1/seguridad/bitacora", params={"entidad": "usuarios"}).json()
    propios = [r for r in registros if r["registro_id"] == str(uid)]
    assert propios and all("clave_hash" not in (r["nuevos"] or {}) for r in propios)
    assert "scrypt" not in str(registros)
