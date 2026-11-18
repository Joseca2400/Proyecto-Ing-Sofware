"""HU-3.01 (versión delgada): alta de la unidad como activo fijo de la flota."""

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.main import app
from app.modulos.contabilidad import service as contabilidad
from app.modulos.contabilidad.schemas import LineaEntrada
from app.modulos.unidades import service as unidades
from tests.test_hoja_costo import API, OTRO_VIN, TOTAL, VIN, base_limpia, ciclo_completo  # noqa: F401
from tests.test_hoja_costo import cliente as cliente  # noqa: F401
from tests.test_taller_ordenes import _token

FECHA_ALTA = "2026-11-15"


def _alta(cliente, vin: str = VIN, fecha: str = FECHA_ALTA):
    return cliente.post(f"{API}/unidades/{vin}/alta-flota", json={"fecha": fecha})


def _partida_alta() -> list[tuple]:
    with SessionLocal() as db:
        filas = db.execute(
            text(
                """
                SELECT c.codigo, l.debe, l.haber, l.linea_negocio, l.vin
                FROM linea_partida l
                JOIN partida p ON p.id = l.partida_id
                JOIN cuentas c ON c.id = l.cuenta_id
                WHERE p.documento_tipo = 'alta_flota' AND p.estado = 'contabilizada'
                ORDER BY l.numero_linea
                """
            )
        )
        return [tuple(fila) for fila in filas]


def _estado(cliente, vin: str = VIN) -> str:
    return cliente.get(f"{API}/unidades/{vin}").json()["estado"]


def _altas() -> int:
    with SessionLocal() as db:
        return db.scalar(text("SELECT count(*) FROM alta_flota"))


def test_alta_traslada_el_costo_a_la_flota_con_el_vin(cliente):
    ciclo_completo(cliente)
    candidatas = cliente.get(f"{API}/unidades/alta-flota/candidatas").json()
    assert [(c["vin"], Decimal(c["costo"]), c["cuadra"], c["orden_abierta"]) for c in candidatas] == [
        (VIN, TOTAL, True, False)
    ]

    respuesta = _alta(cliente)
    assert respuesta.status_code == 201, respuesta.text
    alta = respuesta.json()
    assert (alta["vin"], alta["fecha"], Decimal(alta["costo"])) == (VIN, FECHA_ALTA, TOTAL)
    assert alta["usuario_id"] is not None
    assert _partida_alta() == [
        ("1.2.01", TOTAL, Decimal(0), "alquiler", VIN),
        ("1.1.04.01", Decimal(0), TOTAL, "alquiler", VIN),
    ]
    assert _estado(cliente) == "en_flota"
    ultimo = cliente.get(f"{API}/unidades/{VIN}/historial").json()[-1]
    assert (ultimo["estado_anterior"], ultimo["documento"]) == ("lista", f"Alta en flota {alta['id']}")

    # Unidades en proceso vuelve a cero para el VIN; la hoja cuadra contra el costo congelado.
    with SessionLocal() as db:
        en_proceso = contabilidad.cuenta_regla(db, "compra_unidad", "unidad_en_transito")
        assert contabilidad.saldo_cuenta(db, en_proceso, vin=VIN) == 0
        assert unidades.costo_de_alta(db, VIN) == TOTAL
    hoja = cliente.get(f"{API}/compras/hoja-costo/{VIN}").json()
    assert (hoja["cuadra"], Decimal(hoja["costo_alta_gtq"])) == (True, TOTAL)
    assert cliente.get(f"{API}/unidades/alta-flota/candidatas").json() == []


def test_no_da_de_alta_dos_veces_ni_una_unidad_que_no_esta_lista(cliente):
    ciclo_completo(cliente)
    assert _alta(cliente).status_code == 201
    segunda = _alta(cliente)
    assert segunda.status_code == 409
    assert "Solo una unidad lista" in segunda.json()["detail"]

    unidad = {"vin": OTRO_VIN, "marca": "Honda", "linea": "Fit", "modelo": 2010, "color": "Azul"}
    assert cliente.post(f"{API}/unidades", json={**unidad, "tipo_vehiculo": "sedan"}).status_code == 201
    assert _alta(cliente, OTRO_VIN).status_code == 409
    assert _altas() == 1


def test_rechaza_orden_abierta_costo_cero_y_fecha_futura(cliente):
    unidad = {"vin": OTRO_VIN, "marca": "Honda", "linea": "Fit", "modelo": 2010, "color": "Azul"}
    cuerpo = {**unidad, "tipo_vehiculo": "sedan", "estado": "lista"}
    assert cliente.post(f"{API}/unidades", json=cuerpo).status_code == 201
    cero = _alta(cliente, OTRO_VIN)
    assert cero.status_code == 409
    assert "en cero" in cero.json()["detail"]
    assert _alta(cliente, OTRO_VIN, "2099-01-01").status_code == 400

    with SessionLocal() as db:  # una orden abierta que quedó colgada (no pasa por la regla de apertura)
        db.execute(
            text(
                "INSERT INTO orden_trabajo (vin, tipo, estado, fecha_apertura, kilometraje, descripcion,"
                " responsable) VALUES (:vin, 'reacondicionamiento', 'abierta', '2026-11-10', 0, 'x', 'y')"
            ),
            {"vin": OTRO_VIN},
        )
        db.commit()
    abierta = _alta(cliente, OTRO_VIN)
    assert abierta.status_code == 409
    assert "orden de taller abierta" in abierta.json()["detail"]
    assert _altas() == 0


def test_no_da_de_alta_si_la_hoja_no_cuadra(cliente):
    ciclo_completo(cliente)
    with SessionLocal() as db:
        contabilidad.registrar_automatica(
            db,
            fecha=date(2026, 11, 12),
            concepto="Cargo sin documento de la hoja",
            lineas=[
                LineaEntrada(
                    cuenta_id=contabilidad.cuenta_regla(db, "compra_unidad", "unidad_en_transito"),
                    lado="debe",
                    monto="50.00",
                    vin=VIN,
                ),
                LineaEntrada(
                    cuenta_id=contabilidad.cuenta_regla(db, "factura_compra", "por_pagar_gtq"),
                    lado="haber",
                    monto="50.00",
                ),
            ],
            documento_tipo="prueba",
            documento_id=1,
        )
        db.commit()
    respuesta = _alta(cliente)
    assert respuesta.status_code == 409
    assert "no cuadra" in respuesta.json()["detail"]
    assert (_estado(cliente), _altas(), _partida_alta()) == ("lista", 0, [])


def test_si_la_partida_falla_no_queda_nada(cliente, monkeypatch):
    ciclo_completo(cliente)

    def falla(*args, **kwargs):
        raise ErrorNegocio("La partida no cuadra", 400)

    monkeypatch.setattr(unidades.contabilidad, "registrar_automatica", falla)
    assert _alta(cliente).status_code == 400
    assert (_estado(cliente), _altas()) == ("lista", 0)
    assert len(cliente.get(f"{API}/unidades/{VIN}/historial").json()) == 4


def test_sin_regla_contable_no_se_guarda_nada(cliente):
    ciclo_completo(cliente)
    with SessionLocal() as db:
        db.execute(
            text("UPDATE regla_contabilizacion SET cuenta_codigo = NULL WHERE documento_tipo = 'alta_flota'")
        )
        db.commit()
    try:
        respuesta = _alta(cliente)
        assert respuesta.status_code == 409
        assert "alta_flota · activo_flota" in respuesta.json()["detail"]
    finally:
        with SessionLocal() as db:
            for concepto, codigo in (("activo_flota", "1.2.01"), ("unidad_en_proceso", "1.1.04.01")):
                db.execute(
                    text(
                        "UPDATE regla_contabilizacion SET cuenta_codigo = :c"
                        " WHERE documento_tipo = 'alta_flota' AND concepto = :k"
                    ),
                    {"c": codigo, "k": concepto},
                )
            db.commit()
    assert (_estado(cliente), _altas(), _partida_alta()) == ("lista", 0, [])


def test_una_unidad_lista_no_pasa_a_flota_a_mano(cliente):
    ciclo_completo(cliente)
    a_mano = cliente.post(f"{API}/unidades/{VIN}/estado", json={"estado": "en_flota", "documento": "A mano"})
    assert a_mano.status_code == 409
    assert "alta como activo fijo" in a_mano.json()["detail"]
    assert _estado(cliente) == "lista"


def test_permisos(cliente):
    ciclo_completo(cliente)
    anonimo = TestClient(app)
    assert anonimo.post(f"{API}/unidades/{VIN}/alta-flota", json={"fecha": FECHA_ALTA}).status_code == 401
    assert anonimo.get(f"{API}/unidades/alta-flota/candidatas").status_code == 401
    for correo in ("auxiliar@empresa.gt", "gerente.financiero@empresa.gt", "gerencia@empresa.gt"):
        cabecera = _token(anonimo, correo)
        assert (
            anonimo.post(
                f"{API}/unidades/{VIN}/alta-flota", json={"fecha": FECHA_ALTA}, headers=cabecera
            ).status_code
            == 403
        )
    auxiliar = _token(anonimo, "auxiliar@empresa.gt")
    assert anonimo.get(f"{API}/unidades/alta-flota/candidatas", headers=auxiliar).status_code == 403
    assert _estado(cliente) == "lista"
