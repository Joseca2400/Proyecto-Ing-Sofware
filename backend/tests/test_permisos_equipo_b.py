"""HU-1.09 en las rutas del equipo B: sin sesión responden 401 y con un rol sin permiso, 403."""

import pytest

from tests.conftest import CLAVE_PRUEBAS

API = "/api/v1"
AUXILIAR, GERENCIA = "auxiliar@empresa.gt", "gerencia@empresa.gt"


@pytest.mark.parametrize(
    "ruta",
    [
        "/compras/proveedores",
        "/compras/facturas",
        "/compras/gastos-importacion",
        "/compras/compras-unidades",
        "/compras/cuentas-por-pagar",
        "/compras/programaciones-pago",
        "/compras/pagos-por-ejecutar",
        "/compras/pagos",
        "/unidades",
        "/unidades/catalogos",
        "/configuracion/tipos-cambio",
        "/configuracion/transacciones-usd",
    ],
)
def test_sin_sesion_no_se_consulta(cliente, ruta):
    assert cliente.get(API + ruta).status_code == 401


@pytest.mark.parametrize(
    ("correo", "metodo", "ruta"),
    [
        (AUXILIAR, "post", "/compras/proveedores"),
        (AUXILIAR, "post", "/compras/facturas"),
        (GERENCIA, "post", "/compras/gastos-importacion"),
        (GERENCIA, "post", "/compras/compras-unidades"),
        (GERENCIA, "post", "/compras/programaciones-pago"),
        (AUXILIAR, "post", "/compras/programaciones-pago/1/pagos/1/decision"),
        (GERENCIA, "post", "/compras/pagos"),
        (AUXILIAR, "post", "/compras/pagos/1/anulacion"),
        (GERENCIA, "post", "/unidades"),
        (GERENCIA, "post", "/unidades/1HGCM82633A004352/estado"),
        (AUXILIAR, "get", "/unidades/etapas-importacion"),
        (AUXILIAR, "post", "/configuracion/tipos-cambio"),
        (AUXILIAR, "post", "/configuracion/transacciones-usd"),
    ],
)
def test_un_rol_sin_permiso_recibe_403(cliente, sesion_contador, correo, metodo, ruta):
    # `sesion_contador` garantiza que las cuentas iniciales existen.
    token = cliente.post(f"{API}/seguridad/login", json={"correo": correo, "clave": CLAVE_PRUEBAS}).json()[
        "token"
    ]
    respuesta = cliente.request(metodo, API + ruta, headers={"Authorization": f"Bearer {token}"}, json={})
    assert respuesta.status_code == 403
