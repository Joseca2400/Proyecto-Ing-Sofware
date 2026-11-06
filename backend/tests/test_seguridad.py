from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Sesion, Usuario
from app.modulos.seguridad.semilla import CUENTAS, crear_cuentas_iniciales

CLAVE = "Prueba-2026!"


@pytest.fixture(scope="module", autouse=True)
def cuentas():
    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE)


def _login(cliente, correo, clave=CLAVE):
    return cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": clave})


def _encabezado(cliente, correo):
    return {"Authorization": f"Bearer {_login(cliente, correo).json()['token']}"}


def test_la_semilla_es_idempotente_y_no_guarda_la_clave_en_claro():
    with SessionLocal() as db:
        assert crear_cuentas_iniciales(db, CLAVE) == 0
        hashes = [u.clave_hash for u in db.query(Usuario).all()]
    assert len(hashes) == len(CUENTAS)
    assert all(CLAVE not in h and h.startswith("scrypt$") for h in hashes)


@pytest.mark.parametrize(("correo", "nombre", "rol"), CUENTAS)
def test_cada_rol_inicia_sesion_y_se_identifica(cliente, correo, nombre, rol):
    respuesta = _login(cliente, correo)
    assert respuesta.status_code == 200
    assert respuesta.json()["usuario"]["rol"] == rol
    token = respuesta.json()["token"]
    yo = cliente.get("/api/v1/seguridad/yo", headers={"Authorization": f"Bearer {token}"})
    assert yo.json()["correo"] == correo


def test_credenciales_incorrectas_dan_401_sin_distinguir_el_motivo(cliente):
    mala_clave = _login(cliente, CUENTAS[0][0], "otra")
    sin_usuario = _login(cliente, "nadie@empresa.gt")
    assert mala_clave.status_code == sin_usuario.status_code == 401
    assert mala_clave.json() == sin_usuario.json()


def test_correo_inexistente_tambien_calcula_el_hash(cliente, monkeypatch):
    llamadas = []
    original = service._clave_correcta
    monkeypatch.setattr(service, "_clave_correcta", lambda *a: llamadas.append(a) or original(*a))
    _login(cliente, "nadie@empresa.gt")
    assert len(llamadas) == 1


def test_el_hash_guarda_su_costo_y_sigue_valiendo_si_cambia_el_costo_actual(monkeypatch):
    guardado = service.hashear_clave(CLAVE)
    monkeypatch.setattr(service, "_N", 2**14)
    assert guardado.startswith(f"scrypt${2**15}$")
    assert service._clave_correcta(CLAVE, guardado)
    assert not service._clave_correcta("otra-clave-larga", guardado)


def test_clave_corta_se_rechaza():
    with SessionLocal() as db, pytest.raises(ErrorNegocio, match="al menos 12"):
        service.crear_usuario(db, "corta@empresa.gt", "Corta", service.CONTADOR, "1234")


def test_al_iniciar_sesion_se_borran_las_vencidas(cliente):
    _login(cliente, CUENTAS[1][0])
    with SessionLocal() as db:
        db.execute(update(Sesion).values(expira_en=datetime.now(UTC) - timedelta(minutes=1)))
        db.commit()
    _login(cliente, CUENTAS[1][0])
    with SessionLocal() as db:
        assert db.query(Sesion).filter(Sesion.expira_en < datetime.now(UTC)).count() == 0


def test_sin_token_o_con_token_falso_da_401(cliente):
    assert cliente.get("/api/v1/seguridad/yo").status_code == 401
    assert cliente.get("/api/v1/seguridad/yo", headers={"Authorization": "Bearer falso"}).status_code == 401


def test_cerrar_sesion_invalida_el_token(cliente):
    cabecera = _encabezado(cliente, CUENTAS[1][0])
    assert cliente.post("/api/v1/seguridad/logout", headers=cabecera).status_code == 204
    assert cliente.get("/api/v1/seguridad/yo", headers=cabecera).status_code == 401


def test_sesion_vencida_da_401(cliente):
    cabecera = _encabezado(cliente, CUENTAS[1][0])
    with SessionLocal() as db:
        db.execute(update(Sesion).values(expira_en=datetime.now(UTC) - timedelta(minutes=1)))
        db.commit()
    assert cliente.get("/api/v1/seguridad/yo", headers=cabecera).status_code == 401


def test_usuario_dado_de_baja_no_entra_y_su_sesion_deja_de_valer(cliente):
    cabecera = _encabezado(cliente, CUENTAS[3][0])
    with SessionLocal() as db:
        db.execute(update(Usuario).where(Usuario.correo == CUENTAS[3][0]).values(activo=False))
        db.commit()
    assert _login(cliente, CUENTAS[3][0]).status_code == 401
    assert cliente.get("/api/v1/seguridad/yo", headers=cabecera).status_code == 401
    with SessionLocal() as db:
        db.execute(update(Usuario).where(Usuario.correo == CUENTAS[3][0]).values(activo=True))
        db.commit()


def test_requiere_rol_deja_pasar_o_da_403(cliente):
    from fastapi import Depends

    from app.main import app

    @app.get("/api/v1/_prueba/solo-contador")
    def solo_contador(_=Depends(service.requiere_rol(service.CONTADOR))):
        return {"ok": True}

    assert (
        cliente.get("/api/v1/_prueba/solo-contador", headers=_encabezado(cliente, CUENTAS[1][0])).status_code
        == 200
    )
    assert (
        cliente.get("/api/v1/_prueba/solo-contador", headers=_encabezado(cliente, CUENTAS[0][0])).status_code
        == 403
    )
