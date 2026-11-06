"""Catálogo semilla: `python -m app.modulos.configuracion.semilla`.

BORRADOR para la compra en USD, la importación y las partidas manuales; el contador lo valida
(sesión del 04/11). El padre de cada cuenta es su código sin el último segmento ("1.1.01.02" → "1.1.01").
"""

from sqlalchemy import select

from app.comun.db import SessionLocal
from app.modulos.configuracion import service
from app.modulos.configuracion.models import Cuenta

D, A = "deudora", "acreedora"  # naturaleza
_VIN = {"vin": service.VIN_OBLIGATORIO}
_ADMIN = {"linea_defecto": "administracion"}
_OPC = {"vin": service.VIN_OPCIONAL}


def _linea(linea: str, **extra) -> dict:
    """Cuenta que exige línea de negocio y trae una por defecto."""
    return {"linea_obligatoria": True, "linea_defecto": linea, **extra}


# (código, nombre, tipo, naturaleza, es_detalle, dimensiones y moneda)
CATALOGO = (
    ("1", "Activo", "activo", D, False, {}),
    ("1.1", "Activo corriente", "activo", D, False, {}),
    ("1.1.01", "Caja y bancos", "activo", D, False, {}),
    ("1.1.01.01", "Caja general", "activo", D, True, _ADMIN),
    ("1.1.01.02", "Bancos en quetzales", "activo", D, True, _ADMIN),
    ("1.1.01.03", "Bancos en dólares", "activo", D, True, {"monetaria_usd": True, **_ADMIN}),
    ("1.1.02", "Cuentas por cobrar", "activo", D, False, {}),
    ("1.1.02.01", "Clientes", "activo", D, True, {"linea_obligatoria": True}),
    ("1.1.03", "Impuestos por recuperar", "activo", D, False, {}),
    ("1.1.03.01", "IVA crédito fiscal", "activo", D, True, {}),
    ("1.1.03.02", "IVA pagado en importación", "activo", D, True, _OPC),
    ("1.1.04", "Inventarios", "activo", D, False, {}),
    ("1.1.04.01", "Vehículos en tránsito", "activo", D, True, _VIN),
    ("1.1.04.02", "Vehículos para la venta", "activo", D, True, {"linea_defecto": "venta", **_VIN}),
    ("1.1.04.03", "Repuestos e insumos de taller", "activo", D, True, {"linea_defecto": "taller"}),
    ("1.2", "Activo no corriente", "activo", D, False, {}),
    ("1.2.01", "Vehículos de flota para alquiler", "activo", D, True, {"linea_defecto": "alquiler", **_VIN}),
    ("2", "Pasivo", "pasivo", A, False, {}),
    ("2.1", "Pasivo corriente", "pasivo", A, False, {}),
    ("2.1.01", "Cuentas por pagar", "pasivo", A, False, {}),
    ("2.1.01.01", "Proveedores del exterior", "pasivo", A, True, {"monetaria_usd": True, **_OPC}),
    ("2.1.01.02", "Proveedores locales", "pasivo", A, True, _OPC),
    ("2.1.02", "Impuestos por pagar", "pasivo", A, False, {}),
    ("2.1.02.01", "IVA débito fiscal", "pasivo", A, True, {}),
    ("3", "Patrimonio", "patrimonio", A, False, {}),
    ("3.1", "Capital social", "patrimonio", A, True, _ADMIN),
    ("3.2", "Resultados acumulados", "patrimonio", A, True, _ADMIN),
    ("4", "Ingresos", "ingreso", A, False, {}),
    ("4.1", "Ingresos por alquiler", "ingreso", A, True, _linea("alquiler", **_VIN)),
    ("4.2", "Ingresos por venta de vehículos", "ingreso", A, True, _linea("venta", **_VIN)),
    ("4.3", "Ingresos por servicios de taller", "ingreso", A, True, _linea("taller")),
    ("5", "Costos", "costo", D, False, {}),
    ("5.1", "Costo de vehículos vendidos", "costo", D, True, _linea("venta", **_VIN)),
    ("6", "Gastos", "gasto", D, False, {}),
    ("6.1", "Gastos de administración", "gasto", D, False, {}),
    ("6.1.01", "Sueldos y salarios", "gasto", D, True, _linea("administracion")),
    ("6.1.02", "Servicios y suministros", "gasto", D, True, _linea("administracion")),
)  # fmt: skip


def crear_catalogo_inicial(db) -> int:
    """Crea las cuentas que falten (por código) y devuelve cuántas creó; no toca las existentes."""
    ids = dict(db.execute(select(Cuenta.codigo, Cuenta.id)).all())
    creadas = 0
    for codigo, nombre, tipo, naturaleza, es_detalle, extra in CATALOGO:
        if codigo not in ids:
            padre = codigo.rpartition(".")[0]
            cuenta = service.crear_cuenta(
                db, codigo, nombre, tipo, naturaleza, ids.get(padre), es_detalle, **extra
            )
            ids[codigo] = cuenta.id
            creadas += 1
    return creadas


if __name__ == "__main__":
    with SessionLocal() as sesion:
        print(f"Cuentas creadas: {crear_catalogo_inicial(sesion)}")
