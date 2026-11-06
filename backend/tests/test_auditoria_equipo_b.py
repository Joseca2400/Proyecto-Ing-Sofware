"""HU-1.11 en las tablas del equipo B: sin sesión (las rutas aún están abiertas) la bitácora
registra el cambio con el actor vacío y no falla."""

from sqlalchemy import select, text

from app.comun.auditoria import RegistroBitacora
from app.comun.db import SessionLocal

VIN = "1HGCM82633A004352"
PROVEEDOR = {
    "tipo": "local",
    "nombre": "Repuestos El Volante, S.A.",
    "nit": "1234567-9",
    "regimen": "general",
    "rubro": "repuestos",
    "moneda_habitual": "GTQ",
    "dias_credito": 30,
}


def _ultimo_registro() -> int:
    """La bitácora no se borra y los ids de negocio se reinician: solo cuenta lo nuevo."""
    with SessionLocal() as db:
        return db.scalar(text("SELECT coalesce(max(id), 0) FROM bitacora"))


def _registros(desde: int, entidad: str, registro_id: int) -> list[RegistroBitacora]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(RegistroBitacora)
                .where(
                    RegistroBitacora.id > desde,
                    RegistroBitacora.entidad == entidad,
                    RegistroBitacora.registro_id == str(registro_id),
                )
                .order_by(RegistroBitacora.id)
            )
        )


def test_tipo_cambio_y_transaccion_usd_se_auditan_sin_actor(cliente):
    with SessionLocal() as db:
        db.execute(text("DELETE FROM transaccion_usd"))
        db.execute(text("DELETE FROM tipo_cambio"))
        db.commit()
    desde = _ultimo_registro()

    tipo = cliente.post("/api/v1/configuracion/tipos-cambio", json={"fecha": "2026-01-02", "valor": "7.75"})
    assert tipo.status_code == 201
    transaccion = cliente.post(
        "/api/v1/configuracion/transacciones-usd", json={"fecha": "2026-01-02", "monto_usd": "100.00"}
    )
    assert transaccion.status_code == 201

    [alta_tipo] = _registros(desde, "tipo_cambio", tipo.json()["id"])
    assert alta_tipo.accion == "crear"
    assert alta_tipo.usuario_id is None
    assert alta_tipo.nuevos["origen"] == "manual"

    [alta_transaccion] = _registros(desde, "transaccion_usd", transaccion.json()["id"])
    assert alta_transaccion.usuario_id is None
    assert alta_transaccion.nuevos["monto_gtq"] == 775


def test_factura_de_compra_se_audita_con_el_vin_de_la_linea(cliente):
    with SessionLocal() as db:
        db.execute(text("TRUNCATE proveedor, unidad RESTART IDENTITY CASCADE"))
        db.commit()
    unidad = {"vin": VIN, "marca": "Honda", "linea": "Accord", "modelo": 2003, "color": "Gris"}
    assert cliente.post("/api/v1/unidades", json={**unidad, "tipo_vehiculo": "sedan"}).status_code == 201
    desde = _ultimo_registro()

    proveedor = cliente.post("/api/v1/compras/proveedores", json=PROVEEDOR)
    assert proveedor.status_code == 201
    factura = cliente.post(
        "/api/v1/compras/facturas",
        json={
            "proveedor_id": proveedor.json()["id"],
            "serie": "1A2B3C4D",
            "numero": "305419896",
            "autorizacion": "1A2B3C4D-1234-4ABC-9DEF-0123456789AB",
            "fecha": "2026-10-15",
            "lineas": [
                {
                    "descripcion": "Juego de pastillas de freno",
                    "cuenta": "5.1.02",
                    "linea_negocio": "taller",
                    "vin": VIN,
                    "base": "1000.00",
                    "iva": "120.00",
                }
            ],
        },
    )
    assert factura.status_code == 201
    cuerpo = factura.json()

    [alta_proveedor] = _registros(desde, "proveedor", proveedor.json()["id"])
    assert alta_proveedor.usuario_id is None
    assert alta_proveedor.nuevos["nit"] == "12345679"  # se guarda normalizado

    [alta_factura] = _registros(desde, "factura_compra", cuerpo["id"])
    assert alta_factura.usuario_id is None

    with SessionLocal() as db:
        linea_id = db.scalar(
            text("SELECT id FROM linea_factura_compra WHERE factura_id = :id"), {"id": cuerpo["id"]}
        )
        cxp_id = db.scalar(
            text("SELECT id FROM cuenta_por_pagar WHERE factura_compra_id = :id"), {"id": cuerpo["id"]}
        )

    [alta_linea] = _registros(desde, "linea_factura_compra", linea_id)
    assert alta_linea.vin == VIN
    assert alta_linea.nuevos["vin"] == VIN

    [alta_cxp] = _registros(desde, "cuenta_por_pagar", cxp_id)
    assert alta_cxp.usuario_id is None
