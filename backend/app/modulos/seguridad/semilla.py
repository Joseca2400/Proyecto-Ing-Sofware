"""Cuentas iniciales, una por rol: `CLAVE_INICIAL=... python -m app.modulos.seguridad.semilla`."""

from sqlalchemy import select

from app.comun import config
from app.comun.db import SessionLocal
from app.modulos.seguridad import service
from app.modulos.seguridad.models import Usuario

CUENTAS = (
    ("auxiliar@empresa.gt", "Auxiliar contable", service.AUXILIAR_CONTABLE),
    ("contador@empresa.gt", "Contador", service.CONTADOR),
    ("gerente.financiero@empresa.gt", "Gerente financiero", service.GERENTE_FINANCIERO),
    ("gerencia@empresa.gt", "Gerencia", service.GERENCIA),
)


def crear_cuentas_iniciales(db, clave: str) -> int:
    """Crea las que falten y devuelve cuántas creó; no toca las existentes."""
    creadas = 0
    for correo, nombre, rol in CUENTAS:
        if db.scalar(select(Usuario).where(Usuario.correo == correo)) is None:
            service.crear_usuario(db, correo, nombre, rol, clave)
            creadas += 1
    db.commit()
    return creadas


if __name__ == "__main__":
    if not config.CLAVE_INICIAL:
        raise SystemExit("Define CLAVE_INICIAL para crear las cuentas iniciales")
    with SessionLocal() as sesion:
        print(f"Cuentas creadas: {crear_cuentas_iniciales(sesion, config.CLAVE_INICIAL)}")
