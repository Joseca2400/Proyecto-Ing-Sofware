"""HU-5.02 (versión delgada): tarifa horaria de costo con vigencia."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.comun.db import SessionLocal
from app.comun.errores import ErrorNegocio
from app.modulos.taller import service
from tests.conftest import CLAVE_PRUEBAS

URL = "/api/v1/taller/tarifas"


@pytest.fixture(autouse=True)
def sin_tarifas(sesion_contador):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE tarifa_mano_obra RESTART IDENTITY CASCADE"))
        db.commit()


def _tarifa(cliente, valor="45.00", desde="2026-11-01"):
    return cliente.post(URL, json={"tarifa_hora": valor, "vigente_desde": desde})


def test_crea_y_lista_tarifas_de_la_mas_reciente_a_la_mas_antigua(cliente_contador):
    assert _tarifa(cliente_contador, "45.00", "2026-11-01").status_code == 201
    creada = _tarifa(cliente_contador, "52.50", "2026-12-01")
    assert creada.status_code == 201
    assert creada.json()["tarifa_hora"] == "52.500000"
    lista = cliente_contador.get(URL).json()
    assert [t["vigente_desde"] for t in lista] == ["2026-12-01", "2026-11-01"]


def test_el_cambio_aplica_solo_desde_su_vigencia():
    with SessionLocal() as db:
        db.execute(
            text(
                "INSERT INTO tarifa_mano_obra (tarifa_hora, vigente_desde)"
                " VALUES (45, '2026-11-01'), (60, '2026-12-01')"
            )
        )
        db.commit()
        assert service.tarifa_costo_vigente(db, date(2026, 11, 30)) == Decimal("45")
        assert service.tarifa_costo_vigente(db, date(2026, 12, 1)) == Decimal("60")
        assert service.tarifa_costo_vigente(db, date(2027, 3, 1)) == Decimal("60")
        with pytest.raises(ErrorNegocio, match="No hay tarifa"):
            service.tarifa_costo_vigente(db, date(2026, 10, 31))


def test_rechaza_tarifa_invalida_o_repetida(cliente_contador):
    for valor in ("0", "-5", "abc", "1.1234567", "NaN"):
        assert _tarifa(cliente_contador, valor).status_code == 400, valor
    assert _tarifa(cliente_contador).status_code == 201
    repetida = _tarifa(cliente_contador, "50.00")
    assert repetida.status_code == 409


def _token(cliente, correo):
    r = cliente.post("/api/v1/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS})
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_permisos(cliente, sesion_contador):
    assert cliente.get(URL).status_code == 401
    assert cliente.post(URL, json={}).status_code == 401
    auxiliar = _token(cliente, "auxiliar@empresa.gt")
    assert cliente.get(URL, headers=auxiliar).status_code == 200  # cualquier usuario con sesión lee
    cuerpo = {"tarifa_hora": "45", "vigente_desde": "2026-11-01"}
    assert cliente.post(URL, headers=auxiliar, json=cuerpo).status_code == 403
