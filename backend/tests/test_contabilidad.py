"""Motor contable (HU-2.01, HU-2.02, HU-2.03): cuadre, correlativo, USD y partidas automáticas."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import Cuenta
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service
from app.modulos.contabilidad.models import Partida
from app.modulos.contabilidad.schemas import LineaEntrada, PartidaEntrada
from app.modulos.seguridad.semilla import CUENTAS, crear_cuentas_iniciales

CLAVE = "Prueba-2026!"
AUXILIAR, CONTADOR = CUENTAS[0][0], CUENTAS[1][0]
FECHA = date(2026, 1, 15)
VIN = "1HGCM82633A004352"
URL = "/api/v1/contabilidad/partidas"


@pytest.fixture(scope="module", autouse=True)
def datos():
    with SessionLocal() as db:
        crear_cuentas_iniciales(db, CLAVE)
        crear_catalogo_inicial(db)
        db.execute(
            text(
                "INSERT INTO tipo_cambio (fecha, valor, origen) VALUES (:f, 7.75, 'manual') "
                "ON CONFLICT (fecha) DO UPDATE SET valor = 7.75"
            ),
            {"f": FECHA},
        )
        db.commit()


@pytest.fixture
def db():
    with SessionLocal() as sesion:
        yield sesion


def _id(codigo: str) -> int:
    with SessionLocal() as db:
        return db.query(Cuenta).filter_by(codigo=codigo).one().id


def _linea(codigo, lado, monto, moneda="GTQ", **extra) -> LineaEntrada:
    return LineaEntrada(cuenta_id=_id(codigo), lado=lado, monto=monto, moneda=moneda, **extra)


def _datos(*lineas, concepto="Aporte inicial") -> PartidaEntrada:
    return PartidaEntrada(fecha=FECHA, concepto=concepto, lineas=list(lineas))


def _cuadrada(monto="100.00") -> PartidaEntrada:
    return _datos(_linea("1.1.01.01", "debe", monto), _linea("1.1.01.02", "haber", monto))


# ── HU-2.01: borrador, cuadre y USD ───────────────────────────────────────────


def test_el_borrador_descuadrado_se_guarda_pero_no_pasa_a_revision(db):
    partida = service.crear_borrador(
        db, _datos(_linea("1.1.01.01", "debe", "100.00"), _linea("1.1.01.02", "haber", "90.50"))
    )
    assert partida.estado == "borrador" and partida.numero is None
    with pytest.raises(ErrorNegocio, match=r"diferencia 9\.50"):
        service.enviar_a_revision(db, partida.id)
    assert db.get(Partida, partida.id).estado == "borrador"


def test_flujo_completo_con_correlativo_sin_saltos(db):
    primera = service.crear_borrador(db, _cuadrada())
    segunda = service.crear_borrador(db, _cuadrada("250.00"))
    for p in (primera, segunda):
        service.enviar_a_revision(db, p.id)
    a = service.contabilizar(db, primera.id, usuario_id=None)
    b = service.contabilizar(db, segunda.id, usuario_id=None)
    assert a.estado == b.estado == "contabilizada"
    assert b.numero == a.numero + 1
    with pytest.raises(ErrorNegocio, match="contabilizada"):
        service.contabilizar(db, a.id)
    with pytest.raises(ErrorNegocio, match="contabilizada"):
        service.corregir(db, a.id, _cuadrada())


def test_devuelta_se_corrige_y_se_reenvia_y_pide_comentario(db):
    partida = service.crear_borrador(db, _cuadrada())
    service.enviar_a_revision(db, partida.id)
    with pytest.raises(ErrorNegocio, match="comentario"):
        service.devolver(db, partida.id, "   ")
    assert service.devolver(db, partida.id, "Falta el soporte").estado == "devuelta"
    corregida = service.corregir(db, partida.id, _cuadrada("120.00"))
    assert corregida.lineas[0].debe == Decimal("120")
    reenviada = service.enviar_a_revision(db, partida.id)
    assert reenviada.estado == "en_revision" and reenviada.comentario is None


def test_linea_en_usd_guarda_original_tipo_de_cambio_y_equivalente(db):
    partida = service.crear_borrador(
        db,
        _datos(
            _linea("1.1.01.03", "debe", "1000.00", "USD"),
            _linea("2.1.01.01", "haber", "1000.00", "USD"),
        ),
    )
    linea = partida.lineas[0]
    assert (linea.monto_usd, linea.tipo_cambio, linea.debe) == (
        Decimal("1000"),
        Decimal("7.75"),
        Decimal("7750"),
    )
    assert service.enviar_a_revision(db, partida.id).estado == "en_revision"


def test_usd_exige_cuenta_monetaria_y_tipo_de_cambio_de_la_fecha(db):
    with pytest.raises(ErrorNegocio, match="no admite montos en USD"):
        service.crear_borrador(db, _datos(_linea("1.1.01.01", "debe", "10", "USD")))
    sin_tipo = PartidaEntrada(
        fecha=date(2026, 1, 14),
        concepto="x",
        lineas=[_linea("1.1.01.03", "debe", "10", "USD")],
    )
    with pytest.raises(ErrorNegocio, match="tipo de cambio"):
        service.crear_borrador(db, sin_tipo)


@pytest.mark.parametrize(
    ("monto", "mensaje"),
    [
        ("0", "mayor que cero"),
        ("-5", "mayor que cero"),
        ("abc", "no es un número"),
        ("1.1234567", "decimales"),
    ],
)
def test_montos_invalidos_se_rechazan(db, monto, mensaje):
    with pytest.raises(ErrorNegocio, match=mensaje):
        service.crear_borrador(db, _datos(_linea("1.1.01.01", "debe", monto)))


def test_las_dimensiones_de_la_cuenta_se_validan_por_linea(db):
    with pytest.raises(ErrorNegocio, match=r"Línea 2: .*exige el VIN"):
        service.crear_borrador(db, _datos(_linea("1.1.01.01", "debe", "5"), _linea("5.1", "haber", "5")))
    partida = service.crear_borrador(
        db, _datos(_linea("1.1.01.01", "debe", "5"), _linea("5.1", "haber", "5", vin=VIN.lower()))
    )
    assert partida.lineas[1].vin == VIN and partida.lineas[1].linea_negocio == "venta"


def test_sin_lineas_o_con_fecha_futura_se_rechaza(db):
    with pytest.raises(ErrorNegocio, match="al menos una línea"):
        service.crear_borrador(db, _datos())
    futura = PartidaEntrada(fecha=date(2999, 1, 1), concepto="x", lineas=[_linea("1.1.01.01", "debe", "1")])
    with pytest.raises(ErrorNegocio, match="futura"):
        service.crear_borrador(db, futura)


# ── HU-2.03: partida automática ───────────────────────────────────────────────


def _automatica(db, documento_id, datos=None):
    datos = datos or _cuadrada()
    return service.registrar_automatica(
        db, datos.fecha, datos.concepto, datos.lineas, "factura_compra", documento_id
    )


def test_la_automatica_nace_contabilizada_ligada_y_sin_confirmar(db):
    partida = _automatica(db, 9001)
    assert (partida.estado, partida.origen, partida.documento_id) == ("contabilizada", "automatica", "9001")
    assert partida.numero is not None
    db.rollback()  # el llamador revierte su documento: la partida se va con él
    assert db.query(Partida).filter_by(documento_id="9001").count() == 0


def test_una_partida_por_documento_y_no_se_genera_incompleta(db):
    _automatica(db, 9002)
    db.commit()
    with pytest.raises(ErrorNegocio, match="ya tiene su partida"):
        _automatica(db, 9002)
    db.rollback()
    descuadrada = _datos(_linea("1.1.01.01", "debe", "10"), _linea("1.1.01.02", "haber", "9"))
    with pytest.raises(ErrorNegocio, match="no cuadra"):
        _automatica(db, 9003, descuadrada)
    db.rollback()
    assert db.query(Partida).filter_by(documento_id="9003").count() == 0


# ── La base protege lo que el servicio promete ────────────────────────────────


def test_la_base_impide_modificar_una_partida_contabilizada(db):
    partida = _automatica(db, 9004)
    db.commit()
    for sentencia in (
        "UPDATE partida SET concepto = 'otro' WHERE id = :id",
        "DELETE FROM partida WHERE id = :id",
        "UPDATE linea_partida SET debe = 1 WHERE partida_id = :id AND debe > 0",
        "DELETE FROM linea_partida WHERE partida_id = :id",
    ):
        with pytest.raises(DBAPIError, match="contabilizada"):
            db.execute(text(sentencia), {"id": partida.id})
        db.rollback()


def test_la_base_no_contabiliza_una_partida_descuadrada(db):
    partida = service.crear_borrador(
        db, _datos(_linea("1.1.01.01", "debe", "100"), _linea("1.1.01.02", "haber", "90"))
    )
    with pytest.raises(DBAPIError, match="no cuadra"):
        db.execute(
            text("UPDATE partida SET estado = 'contabilizada', numero = 99999 WHERE id = :id"),
            {"id": partida.id},
        )
    db.rollback()


def test_el_cambio_de_estado_queda_en_la_bitacora(db):
    partida = service.crear_borrador(db, _cuadrada())
    service.enviar_a_revision(db, partida.id)
    acciones = db.execute(
        text(
            "SELECT accion, nuevos ->> 'estado' FROM bitacora "
            "WHERE entidad = 'partida' AND registro_id = :id ORDER BY id"
        ),
        {"id": str(partida.id)},
    ).all()
    assert acciones == [("crear", "borrador"), ("modificar", "en_revision")]


# ── API y permisos ────────────────────────────────────────────────────────────


def _entrar(cliente, correo):
    token = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE}).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def _cuerpo(monto="100.00"):
    return {
        "fecha": FECHA.isoformat(),
        "concepto": "Aporte inicial",
        "lineas": [
            {"cuenta_id": _id("1.1.01.01"), "lado": "debe", "monto": monto},
            {"cuenta_id": _id("1.1.01.02"), "lado": "haber", "monto": monto},
        ],
    }


def test_el_flujo_por_la_api_respeta_los_roles_y_envia_montos_como_texto(cliente):
    assert cliente.post(URL, json=_cuerpo()).status_code == 401
    auxiliar, contador = _entrar(cliente, AUXILIAR), _entrar(cliente, CONTADOR)

    creada = cliente.post(URL, json=_cuerpo(), headers=auxiliar)
    assert creada.status_code == 201
    partida = creada.json()
    assert partida["lineas"][0]["debe"] == "100.000000" and partida["creado_por"] is not None

    base = f"{URL}/{partida['id']}"
    assert cliente.post(f"{base}/enviar-a-revision", headers=auxiliar).status_code == 200
    assert cliente.post(f"{base}/contabilizar", headers=auxiliar).status_code == 403
    final = cliente.post(f"{base}/contabilizar", headers=contador).json()
    assert final["estado"] == "contabilizada" and final["numero"] >= 1

    assert cliente.post(URL, json={**_cuerpo(), "lineas": []}, headers=auxiliar).status_code == 400
    numerico = _cuerpo()
    numerico["lineas"][0]["monto"] = 100.0
    assert cliente.post(URL, json=numerico, headers=auxiliar).status_code == 422
    assert cliente.get(f"{base}", headers=contador).json()["numero"] == final["numero"]
