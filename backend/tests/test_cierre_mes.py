"""HU-2.12: cierre de un período mensual."""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.main import app
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service
from app.modulos.contabilidad.schemas import PartidaEntrada
from tests.test_balance_mayor import _id, _linea
from tests.test_taller_ordenes import _token

API = "/api/v1/contabilidad"
URL = f"{API}/periodos"


def _movimiento(db, fecha: date, monto: str, numero: int) -> None:
    lineas = [_linea(db, "1.1.01.01", "debe", monto), _linea(db, "1.1.01.02", "haber", monto)]
    service.registrar_automatica(db, fecha, f"Movimiento {numero}", lineas, "prueba", numero)


@pytest.fixture(autouse=True)
def libro(sesion_contador):
    """Una partida contabilizada en enero y otra en febrero de 2026. Al terminar no deja meses
    cerrados: bloquearían las partidas de los demás archivos de pruebas."""
    with SessionLocal() as db:
        crear_catalogo_inicial(db)
        db.execute(text("TRUNCATE partida, periodo_cerrado RESTART IDENTITY CASCADE"))
        _movimiento(db, date(2026, 1, 10), "1000", 1)
        _movimiento(db, date(2026, 2, 5), "300", 2)
        db.commit()
    yield
    with SessionLocal() as db:
        db.execute(text("TRUNCATE periodo_cerrado RESTART IDENTITY"))
        db.commit()


def _cerrar(cliente, mes: int, anio: int = 2026):
    return cliente.post(URL, json={"anio": anio, "mes": mes})


def _partida(fecha: str, monto: str = "50") -> dict:
    with SessionLocal() as db:
        caja, banco = _id(db, "1.1.01.01"), _id(db, "1.1.01.02")
    return {
        "fecha": fecha,
        "concepto": "Ajuste",
        "lineas": [
            {"cuenta_id": caja, "lado": "debe", "monto": monto},
            {"cuenta_id": banco, "lado": "haber", "monto": monto},
        ],
    }


def test_cierra_el_mes_con_usuario_fecha_e_instantanea_del_balance(cliente_contador):
    respuesta = _cerrar(cliente_contador, 1)
    assert respuesta.status_code == 201, respuesta.text
    periodo = respuesta.json()
    yo = cliente_contador.get("/api/v1/seguridad/yo").json()["id"]
    assert (periodo["fecha"], periodo["cerrado_por"]) == ("2026-01-31", yo)
    assert periodo["cerrado_en"]
    balance = periodo["balance"]
    assert balance["total_debe"] == balance["total_haber"] == "1000.000000"
    assert {fila["codigo"]: fila["saldo_final"] for fila in balance["filas"]} == {
        "1.1.01.01": "1000.000000",
        "1.1.01.02": "-1000.000000",
    }

    # La instantánea no cambia aunque el balance vivo siga moviéndose en los meses abiertos.
    assert _cerrar(cliente_contador, 2).status_code == 201
    enero, febrero = reversed(cliente_contador.get(URL).json())
    assert enero["balance"] == balance
    assert febrero["balance"]["filas"][0]["saldo_inicial"] == "1000.000000"


def test_no_cierra_con_partidas_sin_contabilizar(cliente_contador):
    borrador = cliente_contador.post(f"{API}/partidas", json=_partida("2026-01-20")).json()
    respuesta = _cerrar(cliente_contador, 1)
    assert respuesta.status_code == 409
    assert "1 partida(s) en borrador, en revisión o devueltas" in respuesta.json()["detail"]
    assert cliente_contador.post(f"{API}/partidas/{borrador['id']}/enviar-a-revision").status_code == 200
    assert _cerrar(cliente_contador, 1).status_code == 409
    assert cliente_contador.get(URL).json() == []


def test_los_meses_se_cierran_en_orden_y_solo_terminados(cliente_contador):
    respuesta = _cerrar(cliente_contador, 2)
    assert respuesta.status_code == 409
    assert "cierre primero enero de 2026" in respuesta.json()["detail"]
    assert _cerrar(cliente_contador, 1).status_code == 201
    repetido = _cerrar(cliente_contador, 1)
    assert repetido.status_code == 409 and "ya está cerrado" in repetido.json()["detail"]
    salto = _cerrar(cliente_contador, 3)
    assert salto.status_code == 409 and "cierre primero febrero de 2026" in salto.json()["detail"]

    hoy = date.today()
    en_curso = _cerrar(cliente_contador, hoy.month, hoy.year)
    assert en_curso.status_code == 400 and "sigue en curso" in en_curso.json()["detail"]


def test_un_mes_cerrado_no_acepta_partidas_reversiones_ni_documentos(cliente_contador):
    gerente = TestClient(app, headers=_token(TestClient(app), "gerente.financiero@empresa.gt"))
    # Una partida manual de febrero, contabilizada por otra persona, para revertirla después.
    manual = cliente_contador.post(f"{API}/partidas", json=_partida("2026-02-10")).json()
    assert cliente_contador.post(f"{API}/partidas/{manual['id']}/enviar-a-revision").status_code == 200
    assert gerente.post(f"{API}/partidas/{manual['id']}/contabilizar").status_code == 200
    # Un borrador de marzo que luego se intentará mover a enero.
    marzo = cliente_contador.post(f"{API}/partidas", json=_partida("2026-03-02")).json()
    assert _cerrar(cliente_contador, 1).status_code == 201

    nueva = cliente_contador.post(f"{API}/partidas", json=_partida("2026-01-31"))
    assert nueva.status_code == 409
    assert "cerrado hasta el 31/01/2026" in nueva.json()["detail"]
    corregida = cliente_contador.put(f"{API}/partidas/{marzo['id']}", json=_partida("2026-01-15"))
    assert corregida.status_code == 409
    reversion = cliente_contador.post(
        f"{API}/partidas/{manual['id']}/revertir", json={"fecha": "2026-02-10", "motivo": "Error"}
    )
    assert reversion.status_code == 201  # febrero sigue abierto
    with SessionLocal() as db:
        # Un documento de otro módulo con fecha de enero: el motor no le da partida.
        with pytest.raises(service.ErrorNegocio, match="cerrado hasta"):
            _movimiento(db, date(2026, 1, 31), "10", 3)
        _movimiento(db, date(2026, 2, 1), "10", 4)  # el primer día abierto sí
        db.commit()
        with pytest.raises(service.ErrorNegocio, match="cerrado hasta"):
            service.revertir_automatica(db, "prueba", 1, date(2026, 1, 31), "Anulación")
        # La reversión de un documento de enero entra con fecha de un mes abierto.
        service.revertir_automatica(db, "prueba", 1, date(2026, 2, 1), "Anulación")
        db.commit()


def test_un_borrador_no_se_contabiliza_dentro_de_un_mes_cerrado(cliente_contador):
    """Si un borrador quedara en un mes cerrado, contabilizarlo se rechaza (defensa del motor)."""
    assert _cerrar(cliente_contador, 1).status_code == 201
    with SessionLocal() as db:
        borrador = service.crear_borrador(db, PartidaEntrada(**_partida("2026-02-10")))
        db.execute(text("UPDATE partida SET fecha = '2026-01-20' WHERE id = :id"), {"id": borrador.id})
        db.commit()
        service.enviar_a_revision(db, borrador.id)
        with pytest.raises(service.ErrorNegocio, match="cerrado hasta"):
            service.contabilizar(db, borrador.id)


def test_permisos():
    assert TestClient(app).post(URL, json={"anio": 2026, "mes": 1}).status_code == 401
    for correo in ("auxiliar@empresa.gt", "gerente.financiero@empresa.gt", "gerencia@empresa.gt"):
        otro = TestClient(app, headers=_token(TestClient(app), correo))
        assert otro.post(URL, json={"anio": 2026, "mes": 1}).status_code == 403
        assert otro.get(URL).status_code == 200
