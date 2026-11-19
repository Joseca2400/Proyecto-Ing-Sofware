"""HU-5.07 (versión delgada): cierre de la orden con su partida y paso de la unidad a lista."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.main import app
from app.modulos.taller import service
from tests.test_taller_horas import horas, tarifa
from tests.test_taller_ordenes import (  # noqa: F401
    API,
    OTRO_VIN,
    URL,
    VIN,
    _token,
    base_limpia,
    estado_unidad,
    orden,
    unidad,
)
from tests.test_taller_ordenes import cliente as cliente  # noqa: F401


def _partida(documento_id: int) -> list[tuple]:
    """Líneas de la partida de la orden: (cuenta, debe, haber, línea de negocio, VIN)."""
    with SessionLocal() as db:
        filas = db.execute(
            text(
                """
                SELECT c.codigo, l.debe, l.haber, l.linea_negocio, l.vin
                FROM linea_partida l
                JOIN partida p ON p.id = l.partida_id
                JOIN cuentas c ON c.id = l.cuenta_id
                WHERE p.documento_tipo = 'orden_trabajo' AND p.documento_id = :id
                  AND p.estado = 'contabilizada'
                ORDER BY l.numero_linea
                """
            ),
            {"id": str(documento_id)},
        )
        return [tuple(fila) for fila in filas]


def _cantidad_partidas() -> int:
    with SessionLocal() as db:
        return db.scalar(text("SELECT count(*) FROM partida"))


@pytest.fixture
def orden_con_horas(cliente) -> int:
    tarifa("45", "2026-11-01")
    orden_id = cliente.post(URL, json=orden()).json()["id"]
    assert cliente.post(f"{URL}/{orden_id}/horas", json=horas(horas="2.5")).status_code == 201  # 112.50
    assert cliente.post(f"{URL}/{orden_id}/horas", json=horas(horas="1")).status_code == 201  # 45.00
    return orden_id


def test_cerrar_genera_la_partida_con_vin_y_pasa_la_unidad_a_lista(cliente, orden_con_horas):
    respuesta = cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={})
    assert respuesta.status_code == 200, respuesta.text
    cerrada = respuesta.json()
    assert cerrada["estado"] == "cerrada"
    assert cerrada["costo_acumulado"] == "157.500000"
    assert cerrada["partida_id"] is not None
    assert cerrada["fecha_cierre"] is not None

    # Débito a unidades en proceso con la línea de la unidad; crédito a mano de obra aplicada (taller).
    assert _partida(orden_con_horas) == [
        ("1.1.04.01", Decimal("157.5"), Decimal(0), "alquiler", VIN),
        ("5.2", Decimal(0), Decimal("157.5"), "taller", VIN),
    ]
    assert estado_unidad(cliente) == "lista"
    historial = cliente.get(f"{API}/unidades/{VIN}/historial").json()
    assert [h["estado_nuevo"] for h in historial] == ["en_aduana", "en_taller", "lista"]
    assert historial[-1]["documento"] == f"Cierre de la orden OT-{orden_con_horas:05d}"
    with SessionLocal() as db:
        cierre = db.execute(
            text("SELECT cerrada_por, partida_id FROM orden_trabajo WHERE id = :id"), {"id": orden_con_horas}
        ).one()
    assert cierre.cerrada_por is not None
    assert cierre.partida_id == cerrada["partida_id"]


def test_no_cierra_dos_veces_ni_admite_horas_despues(cliente, orden_con_horas):
    assert cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={}).status_code == 200
    segundo = cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={})
    assert segundo.status_code == 409
    assert cliente.post(f"{URL}/{orden_con_horas}/horas", json=horas()).status_code == 409
    assert _cantidad_partidas() == 1
    assert cliente.post(f"{URL}/999/cerrar", json={}).status_code == 404


def test_sin_costo_exige_justificacion_y_con_ella_cierra_sin_partida(cliente):
    tarifa("45", "2026-11-01")
    orden_id = cliente.post(URL, json=orden()).json()["id"]
    for cuerpo in ({}, {"justificacion": "   "}):
        rechazo = cliente.post(f"{URL}/{orden_id}/cerrar", json=cuerpo)
        assert rechazo.status_code == 400
        assert "justificación" in rechazo.json()["detail"]
    assert estado_unidad(cliente) == "en_taller"

    cierre = cliente.post(f"{URL}/{orden_id}/cerrar", json={"justificacion": "Revisión sin trabajos"})
    assert cierre.status_code == 200
    assert cierre.json()["partida_id"] is None
    assert cierre.json()["justificacion"] == "Revisión sin trabajos"
    assert cierre.json()["costo_acumulado"] == "0.000000"
    assert _cantidad_partidas() == 0
    assert estado_unidad(cliente) == "lista"


def test_sin_regla_contable_no_se_guarda_nada(cliente, orden_con_horas):
    with SessionLocal() as db:
        db.execute(
            text(
                "UPDATE regla_contabilizacion SET cuenta_codigo = NULL"
                " WHERE documento_tipo = 'orden_trabajo' AND concepto = 'mano_obra_aplicada'"
            )
        )
        db.commit()
    try:
        respuesta = cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={})
        assert respuesta.status_code == 409
        assert "orden_trabajo · mano_obra_aplicada" in respuesta.json()["detail"]
    finally:
        with SessionLocal() as db:
            db.execute(
                text(
                    "UPDATE regla_contabilizacion SET cuenta_codigo = '5.2'"
                    " WHERE documento_tipo = 'orden_trabajo' AND concepto = 'mano_obra_aplicada'"
                )
            )
            db.commit()
    assert estado_unidad(cliente) == "en_taller"
    assert cliente.get(f"{URL}/{orden_con_horas}").json()["estado"] == "abierta"
    assert _cantidad_partidas() == 0


def test_si_la_partida_falla_se_revierte_tambien_el_estado_de_la_unidad(
    cliente, orden_con_horas, monkeypatch
):
    """La unidad ya pasó a lista (sin confirmar) cuando la partida falla: nada debe quedar guardado."""

    def falla(*args, **kwargs):
        raise ErrorNegocio("La partida no cuadra", 400)

    monkeypatch.setattr(service.contabilidad, "registrar_automatica", falla)
    assert cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={}).status_code == 400
    assert estado_unidad(cliente) == "en_taller"
    assert len(cliente.get(f"{API}/unidades/{VIN}/historial").json()) == 2
    assert cliente.get(f"{URL}/{orden_con_horas}").json()["estado"] == "abierta"
    assert _cantidad_partidas() == 0


def test_costo_de_taller_solo_cuenta_las_ordenes_cerradas(cliente, orden_con_horas):
    with SessionLocal() as db:
        assert service.costo_taller_de_unidad(db, VIN) == Decimal("0.00")
        abiertas = service.ordenes_de_unidad(db, VIN)
        assert [(o.numero, o.estado) for o in abiertas] == [("OT-00001", "abierta")]
        assert abiertas[0].costo_acumulado == Decimal("157.5")  # acumulado, aún no capitalizado
    assert cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={}).status_code == 200
    with SessionLocal() as db:
        assert service.costo_taller_de_unidad(db, VIN) == Decimal("157.50")
        assert service.costo_taller_de_unidad(db, OTRO_VIN) == Decimal("0.00")
        (cerrada,) = service.ordenes_de_unidad(db, VIN)
        assert (cerrada.estado, cerrada.costo_acumulado) == ("cerrada", Decimal("157.5"))
        assert cerrada.fecha_apertura and cerrada.fecha_cierre


def test_permisos(cliente, orden_con_horas):
    anonimo = TestClient(app)
    ruta = f"{URL}/{orden_con_horas}/cerrar"
    assert anonimo.post(ruta, json={}).status_code == 401
    for correo in ("auxiliar@empresa.gt", "gerencia@empresa.gt"):
        assert anonimo.post(ruta, json={}, headers=_token(anonimo, correo)).status_code == 403
    assert cliente.get(f"{URL}/{orden_con_horas}").json()["estado"] == "abierta"


def test_con_la_orden_abierta_la_unidad_no_pasa_a_lista_a_mano(cliente, orden_con_horas):
    a_mano = cliente.post(f"{API}/unidades/{VIN}/estado", json={"estado": "lista", "documento": "A mano"})

    assert a_mano.status_code == 409
    assert "orden de taller abierta" in a_mano.json()["detail"]
    assert estado_unidad(cliente) == "en_taller"
    # El cierre de la orden sí la pasa.
    assert cliente.post(f"{URL}/{orden_con_horas}/cerrar", json={}).status_code == 200
    assert estado_unidad(cliente) == "lista"
