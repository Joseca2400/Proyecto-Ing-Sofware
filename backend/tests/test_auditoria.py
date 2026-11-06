"""HU-1.11: auditoría real contra PostgreSQL, incluida escritura fuera del ORM."""

import json

import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import DBAPIError

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal, engine, fijar_actor, get_db
from app.main import app
from app.modulos.configuracion.models import Cuenta
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.seguridad.models import Usuario
from app.modulos.seguridad.semilla import CUENTAS, crear_cuentas_iniciales

CLAVE = "Prueba-2026!"


@pytest.fixture
def db_auditada():
    # Los servicios pueden confirmar; la transacción exterior aísla cada prueba de las demás.
    with engine.connect() as conexion, conexion.begin() as transaccion:
        with SessionLocal(bind=conexion, join_transaction_mode="create_savepoint") as db:
            crear_cuentas_iniciales(db, CLAVE)
            crear_catalogo_inicial(db)

            def sesion_de_prueba():
                yield db

            app.dependency_overrides[get_db] = sesion_de_prueba
            try:
                yield db
            finally:
                app.dependency_overrides.pop(get_db)
        transaccion.rollback()


def _entrar(cliente, indice=1):
    respuesta = cliente.post("/api/v1/seguridad/login", json={"correo": CUENTAS[indice][0], "clave": CLAVE})
    assert respuesta.status_code == 200
    return {"Authorization": f"Bearer {respuesta.json()['token']}"}, respuesta.json()["usuario"]["id"]


def test_alta_y_dimensiones_guardan_actor_y_valores_y_se_consultan(cliente, db_auditada):
    encabezado, usuario_id = _entrar(cliente)
    datos = {"codigo": "auditoria", "nombre": "Auditoría", "tipo": "gasto", "naturaleza": "deudora"}
    alta = cliente.post("/api/v1/configuracion/cuentas", json=datos, headers=encabezado)
    assert alta.status_code == 201
    cuenta_id = alta.json()["id"]
    cambio = cliente.put(
        f"/api/v1/configuracion/cuentas/{cuenta_id}/dimensiones",
        headers=encabezado,
        json={"linea_obligatoria": True, "vin": "obligatorio", "linea_defecto": "venta"},
    )
    assert cambio.status_code == 200
    respuesta = cliente.get(
        "/api/v1/seguridad/bitacora",
        headers=encabezado,
        params={"usuario_id": usuario_id, "entidad": "cuentas"},
    )
    assert respuesta.status_code == 200
    registros = respuesta.json()
    assert len(registros) == 2
    modificacion, creacion = registros
    assert all(r["usuario_id"] == usuario_id and r["registro_id"] == str(cuenta_id) for r in registros)
    assert all(r["fecha"] and r["vin"] is None for r in registros)
    assert creacion["accion"] == "crear" and creacion["anteriores"] is None
    assert creacion["nuevos"]["codigo"] == "auditoria"
    assert modificacion["accion"] == "modificar"
    assert modificacion["anteriores"]["vin"] == "no_aplica"
    assert modificacion["nuevos"]["vin"] == "obligatorio"
    vacia = cliente.get("/api/v1/seguridad/bitacora", headers=encabezado, params={"entidad": "inexistente"})
    assert vacia.json() == []
    pagina = cliente.get("/api/v1/seguridad/bitacora", headers=encabezado, params={"limite": 1})
    assert len(pagina.json()) == 1


@pytest.mark.parametrize(("indice", "estado"), [(0, 403), (1, 200), (2, 200), (3, 403)])
def test_permisos_de_consulta(cliente, db_auditada, indice, estado):
    assert cliente.get("/api/v1/seguridad/bitacora").status_code == 401
    encabezado, _ = _entrar(cliente, indice)
    assert cliente.get("/api/v1/seguridad/bitacora", headers=encabezado).status_code == estado


def test_usuarios_se_auditan_sin_hashes_y_sesiones_no_se_copian(cliente, db_auditada):
    encabezado, usuario_id = _entrar(cliente)
    fijar_actor(db_auditada, usuario_id)
    db_auditada.execute(update(Usuario).where(Usuario.id == usuario_id).values(nombre="Contador actualizado"))
    db_auditada.commit()
    respuesta = cliente.get("/api/v1/seguridad/bitacora", headers=encabezado, params={"entidad": "usuarios"})
    assert respuesta.status_code == 200
    registros = respuesta.json()
    assert registros[0]["anteriores"]["nombre"] == "Contador"
    assert registros[0]["nuevos"]["nombre"] == "Contador actualizado"
    permitidos = {"id", "correo", "nombre", "rol", "activo", "creado_en"}
    for registro in registros:
        for campo in ("anteriores", "nuevos"):
            assert set(registro[campo] or {}) <= permitidos
    contenido = json.dumps(registros)
    assert "scrypt$" not in contenido and CLAVE not in contenido
    assert (
        db_auditada.scalar(
            select(func.count()).select_from(RegistroBitacora).where(RegistroBitacora.entidad == "sesiones")
        )
        == 0
    )


def test_rollback_revierte_el_cambio_y_su_auditoria(db_auditada):
    antes = db_auditada.scalar(select(func.count()).select_from(RegistroBitacora))
    cuenta_id = db_auditada.scalar(select(Cuenta.id).where(Cuenta.codigo == "1.1.01.01"))
    db_auditada.execute(text("UPDATE cuentas SET nombre = 'Revertir' WHERE id = :id"), {"id": cuenta_id})
    assert db_auditada.scalar(select(func.count()).select_from(RegistroBitacora)) == antes + 1
    db_auditada.rollback()
    assert db_auditada.scalar(select(func.count()).select_from(RegistroBitacora)) == antes
    assert db_auditada.get(Cuenta, cuenta_id).nombre == "Caja general"


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE bitacora SET accion = 'alterar'",
        "DELETE FROM bitacora",
        "TRUNCATE bitacora",
    ],
)
def test_bitacora_no_admite_modificacion_ni_borrado(db_auditada, sentencia):
    with pytest.raises(DBAPIError, match="no permite modificación ni borrado"), db_auditada.begin_nested():
        db_auditada.execute(text(sentencia))


@pytest.mark.parametrize("metodo", ["post", "put", "patch", "delete"])
def test_api_no_expone_escritura_de_bitacora(cliente, db_auditada, metodo):
    encabezado, _ = _entrar(cliente)
    assert getattr(cliente, metodo)("/api/v1/seguridad/bitacora", headers=encabezado).status_code == 405


def test_trigger_generico_captura_vin_y_eliminacion_y_filtra(cliente, db_auditada):
    encabezado, usuario_id = _entrar(cliente)
    fijar_actor(db_auditada, usuario_id)
    # Entidad temporal: comprueba el contrato de integración sin modificar módulos de otros equipos.
    db_auditada.execute(text("CREATE TEMP TABLE entidad_prueba (id integer, vin text, secreto text)"))
    db_auditada.execute(
        text("""
        CREATE TRIGGER auditar_prueba AFTER INSERT OR UPDATE OR DELETE ON entidad_prueba
        FOR EACH ROW EXECUTE FUNCTION public.registrar_cambio('id', 'vin')
    """)
    )
    db_auditada.execute(text("INSERT INTO entidad_prueba VALUES (1, '1HGCM82633A004352', 'no copiar')"))
    db_auditada.execute(text("DELETE FROM entidad_prueba WHERE id = 1"))
    respuesta = cliente.get(
        "/api/v1/seguridad/bitacora",
        headers=encabezado,
        params={
            "vin": "1hgcm82633a004352",
            "entidad": "entidad_prueba",
            "usuario_id": usuario_id,
        },
    )
    registros = respuesta.json()
    assert respuesta.status_code == 200 and len(registros) == 2
    assert registros[0]["accion"] == "eliminar"
    assert registros[0]["nuevos"] is None
    assert registros[0]["anteriores"] == {"id": 1, "vin": "1HGCM82633A004352"}
    assert "no copiar" not in json.dumps(registros)


def test_actor_se_reaplica_tras_commit_y_no_se_filtra_al_pool():
    with SessionLocal() as primera:
        fijar_actor(primera, 123)
        primera.commit()
        assert primera.scalar(text("SELECT current_setting('app.usuario_id')")) == "123"
    with SessionLocal() as siguiente:
        assert siguiente.scalar(text("SELECT current_setting('app.usuario_id')")) == ""
