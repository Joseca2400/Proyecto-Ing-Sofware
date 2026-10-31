"""HU-1.11: auditoría automática en la capa de persistencia (acuerdo 5 de K1).

Cada alta, cambio o baja de las entidades del alcance queda en la bitácora con actor, fecha,
entidad, VIN cuando corresponde y los valores anteriores y nuevos. Nunca guarda contraseñas,
hashes ni tokens. Se escribe en la misma transacción que el cambio: si el cambio se revierte,
su registro también.
"""

import json
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import event, inspect, insert, select
from sqlalchemy.orm import Session

from app.models import (
    Bitacora,
    Cliente,
    Cobro,
    Contrato,
    Cuenta,
    DocumentoPorPagar,
    Factura,
    GastoImportacion,
    LineaPartida,
    ManoObra,
    OrdenTrabajo,
    Partida,
    Proveedor,
    TipoCambio,
    Unidad,
    Usuario,
)

AUDITADAS = (Usuario, Cuenta, TipoCambio, Unidad, Partida, LineaPartida, Proveedor, DocumentoPorPagar,
             GastoImportacion, OrdenTrabajo, ManoObra, Cliente, Contrato, Factura, Cobro)
SECRETOS = {"password_hash", "token_hash"}


def _valor(v):
    if isinstance(v, Decimal):
        return str(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _columnas(obj) -> list[str]:
    return [c.key for c in inspect(obj).mapper.column_attrs if c.key not in SECRETOS]


def _vin(conn, obj) -> str | None:
    if isinstance(obj, Unidad):
        return obj.vin
    unidad_id = getattr(obj, "unidad_id", None)
    if unidad_id:
        return conn.execute(select(Unidad.vin).where(Unidad.id == unidad_id)).scalar()
    return None


@event.listens_for(Session, "after_flush")
def _auditar(session: Session, _ctx) -> None:
    filas = []
    conn = session.connection()
    # El actor lo fija la dependencia de sesión en la misma Session de la petición.
    actor = session.info.get("actor", "SISTEMA")
    ahora = datetime.now(timezone.utc)

    for obj in session.new:
        if isinstance(obj, AUDITADAS):
            nuevos = {k: _valor(getattr(obj, k)) for k in _columnas(obj)}
            filas.append(dict(fecha=ahora, usuario=actor, accion="CREAR", entidad=type(obj).__name__,
                              entidad_id=obj.id, vin=_vin(conn, obj), valores_anteriores=None,
                              valores_nuevos=json.dumps(nuevos, ensure_ascii=False)))

    for obj in session.dirty:
        if not isinstance(obj, AUDITADAS) or not session.is_modified(obj, include_collections=False):
            continue
        estado = inspect(obj)
        antes, despues = {}, {}
        for k in _columnas(obj):
            hist = estado.attrs[k].history
            if hist.has_changes():
                antes[k] = _valor(hist.deleted[0]) if hist.deleted else None
                despues[k] = _valor(hist.added[0]) if hist.added else None
        if despues:
            filas.append(dict(fecha=ahora, usuario=actor, accion="MODIFICAR", entidad=type(obj).__name__,
                              entidad_id=obj.id, vin=_vin(conn, obj),
                              valores_anteriores=json.dumps(antes, ensure_ascii=False),
                              valores_nuevos=json.dumps(despues, ensure_ascii=False)))

    for obj in session.deleted:
        if isinstance(obj, AUDITADAS):
            antes = {k: _valor(getattr(obj, k)) for k in _columnas(obj)}
            filas.append(dict(fecha=ahora, usuario=actor, accion="ELIMINAR", entidad=type(obj).__name__,
                              entidad_id=obj.id, vin=_vin(conn, obj),
                              valores_anteriores=json.dumps(antes, ensure_ascii=False), valores_nuevos=None))

    if filas:
        conn.execute(insert(Bitacora.__table__), filas)
