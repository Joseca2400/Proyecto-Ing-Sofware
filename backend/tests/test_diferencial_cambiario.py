"""HU-2.09: diferencial cambiario realizado al pagar o cobrar un saldo en USD (pieza del motor)."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.configuracion.models import Cuenta
from app.modulos.configuracion.semilla import crear_catalogo_inicial
from app.modulos.contabilidad import service
from app.modulos.contabilidad.schemas import LineaAutomatica, LineaEntrada

FECHA = date(2026, 1, 15)  # tipo de cambio del día: 7.75


@pytest.fixture(scope="module", autouse=True)
def datos():
    with SessionLocal() as db:
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


def _id(db, codigo: str) -> int:
    return db.query(Cuenta).filter_by(codigo=codigo).one().id


@pytest.mark.parametrize(
    ("monto", "libros", "liquidacion", "saldo", "esperado", "cuenta", "lado"),
    [
        ("1000", "7.70", "7.75", "por_pagar", "-50", "6.3", "debe"),  # pagar más caro: pérdida
        ("1000", "7.70", "7.65", "por_pagar", "50", "4.4", "haber"),
        ("1000", "7.70", "7.75", "por_cobrar", "50", "4.4", "haber"),  # cobrar más caro: ganancia
        ("1000", "7.70", "7.65", "por_cobrar", "-50", "6.3", "debe"),
        ("400", "7.70", "7.75", "por_pagar", "-20", "6.3", "debe"),  # parcial: 40 % del efecto
        ("1000", "7.74", "7.75", "por_pagar", "-10", "6.3", "debe"),  # ya revaluado a 7.74
    ],
)
def test_ganancia_o_perdida_segun_el_saldo_y_la_tasa(
    db, monto, libros, liquidacion, saldo, esperado, cuenta, lado
):
    diferencial, linea = service.diferencial_cambiario(db, monto, libros, liquidacion, saldo)
    assert diferencial == Decimal(esperado)
    assert (linea.cuenta_id, linea.lado, Decimal(linea.monto)) == (
        _id(db, cuenta),
        lado,
        abs(Decimal(esperado)),
    )


def test_sin_diferencia_no_hay_linea(db):
    assert service.diferencial_cambiario(db, "250.50", "7.75", "7.75", "por_pagar") == (0, None)


def test_rechaza_montos_y_tasas_no_positivos(db):
    with pytest.raises(ErrorNegocio, match="mayores que cero"):
        service.diferencial_cambiario(db, "0", "7.70", "7.75", "por_pagar")
    with pytest.raises(TypeError):
        service.diferencial_cambiario(db, 1000.0, "7.70", "7.75", "por_pagar")  # type: ignore[arg-type]


def test_la_partida_del_pago_en_usd_cuadra_al_centavo(db):
    """Pago parcial de una factura llevada a 7.70123456, con el tipo de cambio del día (7.75)."""
    monto, libros = "1234.57", Decimal("7.70123456")
    diferencial, linea = service.diferencial_cambiario(db, monto, libros, "7.75", "por_pagar")
    partida = service.registrar_automatica(
        db,
        FECHA,
        "Pago a proveedor del exterior",
        [
            LineaAutomatica(
                cuenta_id=_id(db, "2.1.01.01"), lado="debe", monto=monto, moneda="USD", tipo_cambio=libros
            ),
            LineaEntrada(cuenta_id=_id(db, "1.1.01.03"), lado="haber", monto=monto, moneda="USD"),
            linea,
        ],
        "pago_prueba",
        1,
    )
    proveedor, banco, perdida = partida.lineas
    assert (proveedor.tipo_cambio, banco.tipo_cambio) == (libros, Decimal("7.75"))
    assert perdida.debe == banco.haber - proveedor.debe == -diferencial > 0
    assert service.totales(partida)[0] == service.totales(partida)[1]
    db.rollback()


def test_la_tasa_propia_de_una_linea_debe_ser_valida(db):
    lineas = [
        LineaAutomatica(
            cuenta_id=_id(db, "2.1.01.01"), lado="debe", monto="10", moneda="USD", tipo_cambio=tasa
        )
        for tasa in (Decimal("0"), Decimal("7.123456789"))
    ]
    for linea in lineas:
        with pytest.raises(ErrorNegocio, match="tipo de cambio debe ser positivo"):
            service.registrar_automatica(db, FECHA, "x", [linea], "pago_prueba", 2)
