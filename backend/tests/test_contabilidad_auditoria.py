"""Regresiones de la auditoría del motor contable (HU-2.01, HU-2.02 y HU-2.03)."""

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.contabilidad import service
from app.modulos.contabilidad.models import Partida
from tests.test_contabilidad import (
    AUXILIAR,
    URL,
    _cuadrada,
    _cuerpo,
    _datos,
    _entrar,
    _linea,
    datos,  # noqa: F401  semilla compartida
)


@pytest.fixture
def db():
    with SessionLocal() as sesion:
        yield sesion


def test_vin_invalido_devuelve_error_de_negocio(cliente):
    cuerpo = _cuerpo()
    cuerpo["lineas"][1] = _linea("5.1", "haber", "100", vin="CORTO").model_dump()
    respuesta = cliente.post(URL, json=cuerpo, headers=_entrar(cliente, AUXILIAR))
    assert respuesta.status_code in (400, 422)
    assert "VIN" in respuesta.json()["detail"]


def test_equivalente_usd_fuera_de_rango_se_rechaza_antes_de_persistir(db):
    with pytest.raises(ErrorNegocio, match="máximo"):
        service.crear_borrador(db, _datos(_linea("1.1.01.03", "debe", "999999999999", "USD")))


def test_diferencia_de_seis_decimales_es_visible(db):
    partida = service.crear_borrador(
        db, _datos(_linea("1.1.01.01", "debe", "1.000001"), _linea("1.1.01.02", "haber", "1"))
    )
    with pytest.raises(ErrorNegocio, match=r"diferencia 0\.000001"):
        service.enviar_a_revision(db, partida.id)


def test_no_se_corrige_con_un_estado_obsoleto_en_la_sesion(db):
    partida = service.crear_borrador(db, _cuadrada())
    with SessionLocal() as otra:
        service.enviar_a_revision(otra, partida.id)
    with pytest.raises(ErrorNegocio, match="revisión|revision"):
        service.corregir(db, partida.id, _cuadrada("200"))
    db.expire_all()
    assert db.get(Partida, partida.id).lineas[0].debe == Decimal("100")


def test_no_se_inserta_cabecera_contabilizada_sin_lineas(db):
    with pytest.raises(DBAPIError, match="no cuadra"):
        db.execute(
            text("""
            INSERT INTO partida (numero, fecha, concepto, estado, origen)
            VALUES (999999, '2026-01-15', 'Inserción directa', 'contabilizada', 'manual')
        """)
        )
    db.rollback()


def test_no_se_traslada_una_linea_a_una_partida_contabilizada(db):
    destino = service.crear_borrador(db, _cuadrada())
    service.enviar_a_revision(db, destino.id)
    service.contabilizar(db, destino.id)
    origen = service.crear_borrador(db, _cuadrada())
    with pytest.raises(DBAPIError, match="contabilizada"):
        db.execute(
            text("UPDATE linea_partida SET partida_id = :destino, numero_linea = 3 WHERE id = :linea"),
            {"destino": destino.id, "linea": origen.lineas[0].id},
        )
    db.rollback()


def test_la_base_exige_original_y_tipo_cambio_para_usd(db):
    partida = service.crear_borrador(db, _cuadrada())
    with pytest.raises(DBAPIError, match="ck_linea_partida_moneda"):
        db.execute(text("UPDATE linea_partida SET moneda = 'USD' WHERE partida_id = :id"), {"id": partida.id})
    db.rollback()


@pytest.mark.parametrize("misma_partida", [True, False])
def test_contabilizaciones_concurrentes_serializan_estado_y_correlativo(db, misma_partida):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    primera = service.crear_borrador(db, _cuadrada())
    service.enviar_a_revision(db, primera.id)
    segunda = primera if misma_partida else service.crear_borrador(db, _cuadrada())
    if not misma_partida:
        service.enviar_a_revision(db, segunda.id)
    db.rollback()
    barrera = Barrier(2)

    def contabilizar(partida_id):
        with SessionLocal() as sesion:
            sesion.execute(text("SET LOCAL lock_timeout = '5s'"))
            # Ambas sesiones leen el estado antes de competir por la misma operación.
            anterior = sesion.get(Partida, partida_id)
            assert anterior.estado == "en_revision"
            barrera.wait(timeout=5)
            try:
                return service.contabilizar(sesion, partida_id).numero
            except ErrorNegocio as error:
                assert error.status == 409
                return None

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        tareas = [ejecutor.submit(contabilizar, p.id) for p in (primera, segunda)]
        numeros = [tarea.result(timeout=10) for tarea in tareas]
    if misma_partida:
        assert numeros.count(None) == 1
    else:
        assert abs(numeros[0] - numeros[1]) == 1


def test_la_linea_espera_la_contabilizacion_y_rechaza_el_cambio(db):
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue
    from threading import Event
    from time import monotonic

    partida = service.crear_borrador(db, _cuadrada())
    service.enviar_a_revision(db, partida.id)
    partida = service._obtener(db, partida.id, bloquear=True)
    service._contabilizar(db, partida, None)
    procesos = Queue()

    def alterar_linea():
        with SessionLocal() as sesion:
            sesion.execute(text("SET LOCAL lock_timeout = '5s'"))
            procesos.put(sesion.scalar(text("SELECT pg_backend_pid()")))
            with pytest.raises(DBAPIError, match="contabilizada"):
                sesion.execute(
                    text("UPDATE linea_partida SET debe = 200 WHERE partida_id = :id AND debe > 0"),
                    {"id": partida.id},
                )
            sesion.rollback()

    with ThreadPoolExecutor(max_workers=1) as ejecutor:
        tarea = ejecutor.submit(alterar_linea)
        proceso = procesos.get(timeout=5)
        limite = monotonic() + 3
        bloqueada = False
        while monotonic() < limite:
            bloqueada = db.scalar(text("SELECT cardinality(pg_blocking_pids(:pid)) > 0"), {"pid": proceso})
            if bloqueada:
                break
            Event().wait(0.01)
        db.commit()
        tarea.result(timeout=10)
    assert bloqueada, "La escritura debe esperar a que se confirme la contabilización"
    db.expire_all()
    assert service.totales(db.get(Partida, partida.id)) == (Decimal("100"), Decimal("100"))


def test_api_audita_actor_y_vin_y_la_reversion_no_deja_bitacora(cliente, db):
    cuerpo = _cuerpo()
    cuerpo["lineas"][1] = _linea("5.1", "haber", "100", vin="1HGCM82633A004352").model_dump()
    respuesta = cliente.post(URL, json=cuerpo, headers=_entrar(cliente, AUXILIAR))
    assert respuesta.status_code == 201
    partida = respuesta.json()
    filas = db.execute(
        text("""
            SELECT usuario_id, vin FROM bitacora
            WHERE entidad = 'linea_partida' AND nuevos ->> 'partida_id' = :id
        """),
        {"id": str(partida["id"])},
    ).all()
    assert len(filas) == 2
    assert all(f.usuario_id == partida["creado_por"] for f in filas)
    assert "1HGCM82633A004352" in [f.vin for f in filas]
    entrada = _cuadrada()
    automatica = service.registrar_automatica(
        db, entrada.fecha, entrada.concepto, entrada.lineas, "prueba_atomica", "rollback"
    )
    registro = str(automatica.id)
    db.rollback()
    assert (
        db.scalar(
            text("SELECT count(*) FROM bitacora WHERE entidad = 'partida' AND registro_id = :id"),
            {"id": registro},
        )
        == 0
    )


def test_automatica_no_disfraza_otra_restriccion_como_documento_duplicado(db):
    from sqlalchemy.exc import IntegrityError

    entrada = _cuadrada()
    db.add(Partida(fecha=entrada.fecha, concepto="Origen inválido", origen="invalido"))
    with pytest.raises(IntegrityError, match="ck_partida_origen"):
        service.registrar_automatica(
            db, entrada.fecha, entrada.concepto, entrada.lineas, "prueba_atomica", "restriccion"
        )
    assert (
        db.query(Partida).filter_by(documento_tipo="prueba_atomica", documento_id="restriccion").count() == 0
    )
