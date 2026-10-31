import os
import tempfile

# La app crea su base al iniciar; en pruebas se apunta a un archivo temporal.
os.environ.setdefault("SISTEMA_DB_URL", f"sqlite:///{tempfile.mkdtemp()}/arranque.db")  # base nueva en cada corrida
os.environ.setdefault("SISTEMA_ITERACIONES_HASH", "1000")   # hash más rápido sólo en pruebas
os.environ.setdefault("SISTEMA_MODULOS_INGRESO", "true")    # las pruebas cubren también el adelanto

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.base import digito_verificador_vin, sembrar_datos_iniciales  # noqa: E402

API = "/api/v1"
PASSWORD = "Demo2026!"
# Encabezados por rol; el fixture `client` los llena con el token de una sesión real.
AUX: dict = {}
CONTADOR: dict = {}
GERENTE: dict = {}
GERENCIA: dict = {}

F1 = "2026-10-01"   # compra
F2 = "2026-10-05"   # gastos e importación
F3 = "2026-10-12"   # taller y alta
F4 = "2026-10-20"   # facturación
F5 = "2026-10-27"   # cobro
TIPOS_CAMBIO = {F1: 7.70, F2: 7.72, F3: 7.71, F4: 7.73, F5: 7.75}


def vin(n: int) -> str:
    """VIN válido de prueba con su dígito verificador."""
    base = f"1HGCM826X3A{n:06d}"
    return base[:8] + digito_verificador_vin(base) + base[9:]


@pytest.fixture()
def sesiones():
    """Fábrica de sesiones de la base en memoria de cada prueba."""
    return {}


@pytest.fixture()
def client(sesiones):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    Sesion = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    sesiones["fabrica"] = Sesion
    with Sesion() as db:
        sembrar_datos_iniciales(db)

    def _get_db():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    with TestClient(app) as c:
        for encabezado, usuario in ((AUX, "aux"), (CONTADOR, "contador"), (GERENTE, "gerente"),
                                    (GERENCIA, "gerencia")):
            r = c.post(f"{API}/auth/login", json={"usuario": usuario, "password": PASSWORD})
            assert r.status_code == 200, r.text
            encabezado.clear()
            encabezado["Authorization"] = f"Bearer {r.json()['token']}"
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def tc(client):
    for fecha, valor in TIPOS_CAMBIO.items():
        r = client.post(f"{API}/tipos-cambio", json={"fecha": fecha, "valor": valor}, headers=CONTADOR)
        assert r.status_code == 201, r.text


@pytest.fixture()
def proveedores(client):
    def crear(datos):
        r = client.post(f"{API}/proveedores", json=datos, headers=AUX)
        assert r.status_code == 201, r.text
        return r.json()
    return {
        "subasta": crear({"nombre": "Copart Inc.", "tipo": "EXTERIOR", "rubro": "SUBASTA", "moneda": "USD"}),
        "naviera": crear({"nombre": "Seaboard Marine", "tipo": "EXTERIOR", "rubro": "NAVIERA", "moneda": "USD"}),
        "aduana": crear({"nombre": "Agencia Aduanal Quetzal", "tipo": "LOCAL", "nit": "1234567-9",
                         "rubro": "AGENTE_ADUANAL", "moneda": "GTQ"}),
        "sat": crear({"nombre": "SAT", "tipo": "LOCAL", "nit": "1669394-9", "rubro": "SAT", "moneda": "GTQ"}),
    }


@pytest.fixture()
def comprar(client, tc, proveedores):
    def _comprar(n=1, precio=8000, cargos=500):
        r = client.post(f"{API}/compras", headers=AUX, json={
            "proveedor_id": proveedores["subasta"]["id"], "fecha": F1, "numero_lote": f"LOT-{n}",
            "vin": vin(n), "marca": "Honda", "linea": "Accord", "modelo_anio": 2019,
            "precio_usd": precio, "cargos_usd": cargos,
        })
        assert r.status_code == 201, r.text
        return r.json()["unidad"]
    return _comprar


@pytest.fixture()
def unidad_en_flota(client, comprar, proveedores):
    """Compra USD 8,500 (Q65,450) + flete USD 900 (Q6,948) + DAI Q3,000 + taller 10 h (Q750) → alta."""
    def _crear(n=1):
        u = comprar(n)
        uid = u["id"]
        gasto(client, uid, proveedores["naviera"]["id"], "FLETE", "USD", 900)
        client.post(f"{API}/unidades/{uid}/estado", json={"estado": "EN_ADUANA", "documento": "Arribo"}, headers=AUX)
        gasto(client, uid, proveedores["sat"]["id"], "DAI", "GTQ", 3000)
        orden = client.post(f"{API}/ordenes", headers=AUX, json={
            "unidad_id": uid, "tipo": "REACONDICIONAMIENTO", "descripcion": "Pintura y frenos",
            "responsable": "Jefe de taller", "fecha": F3}).json()
        client.post(f"{API}/ordenes/{orden['id']}/mano-obra", headers=AUX, json={
            "mecanico": "Pedro", "fecha": F3, "horas": 10, "descripcion": "Frenos"})
        client.post(f"{API}/ordenes/{orden['id']}/cerrar", json={"fecha": F3}, headers=CONTADOR)
        client.post(f"{API}/unidades/{uid}/estado", json={"estado": "LISTA", "documento": "Inspección"}, headers=AUX)
        r = client.post(f"{API}/unidades/{uid}/alta-flota", json={"fecha": F3, "vida_util_meses": 48,
                                                                   "valor_residual": 20000}, headers=CONTADOR)
        assert r.status_code == 200, r.text
        return r.json()
    return _crear


def gasto(client, unidad_id, proveedor_id, concepto, moneda, monto, fecha=F2):
    r = client.post(f"{API}/gastos-importacion", headers=AUX, json={
        "unidad_id": unidad_id, "proveedor_id": proveedor_id, "concepto": concepto,
        "fecha": fecha, "moneda": moneda, "monto": monto})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def cliente(client):
    r = client.post(f"{API}/clientes", headers=AUX, json={
        "tipo": "EMPRESA", "nombre": "Turismo Maya, S.A.", "nit": "1234567-9"})
    assert r.status_code == 201, r.text
    return r.json()


def saldo(client, codigo, vin_=None):
    params = {"vin": vin_} if vin_ else {}
    return client.get(f"{API}/contabilidad/mayor/{codigo}", params=params, headers=CONTADOR).json()["saldo_final"]
