"""E1 Configuración, multimoneda y seguridad · E2 Contabilidad general."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import REGISTRAN, REVISAN, TODOS, requiere, sesion_actual, usuario_actual
from app.models import Bitacora, Cuenta, Partida, Rol, TipoCambio, Unidad, Usuario
from app import seguridad
from app.schemas import (
    LoginIn,
    LoginOut,
    BitacoraOut,
    CuentaIn,
    CuentaOut,
    DevolverIn,
    LineaPartidaOut,
    PartidaIn,
    PartidaOut,
    TipoCambioIn,
    TipoCambioOut,
    UsuarioIn,
    UsuarioOut,
)
from app.services import contabilidad as cont
from app.services.base import Conflicto, obtener, registrar_bitacora
from app.services.ciclo import unidad_por_vin

router = APIRouter()


def partida_out(p: Partida) -> PartidaOut:
    return PartidaOut(
        id=p.id, numero=p.numero, fecha=p.fecha, concepto=p.concepto, estado=p.estado, automatica=p.automatica,
        origen_tipo=p.origen_tipo, origen_id=p.origen_id, registrada_por=p.registrada_por,
        contabilizada_por=p.contabilizada_por, comentario_revision=p.comentario_revision,
        total_debe=sum(l.debe for l in p.lineas), total_haber=sum(l.haber for l in p.lineas),
        lineas=[LineaPartidaOut(
            cuenta=l.cuenta.codigo, nombre_cuenta=l.cuenta.nombre, debe=l.debe, haber=l.haber, moneda=l.moneda,
            monto_original=l.monto_original, tipo_cambio=l.tipo_cambio, linea_negocio=l.linea_negocio,
            vin=l.unidad.vin if l.unidad else None, detalle=l.detalle,
        ) for l in p.lineas],
    )


def _unidad_id(db: Session, vin: str | None) -> int | None:
    return unidad_por_vin(db, vin).id if vin else None


# ======================================================================= Sesión (HU-1.09)

@router.post("/auth/login", response_model=LoginOut, tags=["E1 · Seguridad"],
             summary="HU-1.09 Iniciar sesión con usuario y contraseña")
def login(datos: LoginIn, db: Session = Depends(get_db)):
    token, u, expira = seguridad.iniciar_sesion(db, datos.usuario, datos.password)
    db.info["actor"] = u.usuario
    registrar_bitacora(db, u.usuario, "INICIAR_SESION", "Usuario", u.id)
    db.commit()
    return LoginOut(token=token, expira_en=expira, usuario=UsuarioOut.model_validate(u))


@router.post("/auth/logout", status_code=204, tags=["E1 · Seguridad"], summary="Cerrar sesión")
def logout(s=Depends(sesion_actual), db: Session = Depends(get_db)):
    usuario, sesion = s
    registrar_bitacora(db, usuario.usuario, "CERRAR_SESION", "Usuario", usuario.id)
    seguridad.cerrar_sesion(db, sesion)


# ======================================================================= Usuarios (HU-1.09)

@router.get("/yo", response_model=UsuarioOut, tags=["E1 · Seguridad"], summary="Usuario actual")
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario


@router.get("/usuarios", response_model=list[UsuarioOut], tags=["E1 · Seguridad"])
def listar_usuarios(db: Session = Depends(get_db), _=Depends(requiere(Rol.GERENTE_FINANCIERO))):
    return list(db.scalars(select(Usuario).order_by(Usuario.id)))


@router.post("/usuarios", response_model=UsuarioOut, status_code=201, tags=["E1 · Seguridad"],
             summary="HU-1.09 Crear usuario con rol (sólo gerente financiero)")
def crear_usuario(datos: UsuarioIn, db: Session = Depends(get_db),
                  quien: Usuario = Depends(requiere(Rol.GERENTE_FINANCIERO))):
    if db.scalar(select(Usuario).where(Usuario.usuario == datos.usuario)):
        raise Conflicto(f"El usuario '{datos.usuario}' ya existe")
    seguridad.validar_complejidad(datos.password)
    u = Usuario(usuario=datos.usuario, nombre=datos.nombre, rol=datos.rol,
                password_hash=seguridad.hash_password(datos.password))
    db.add(u)
    db.flush()
    db.commit()
    return u


@router.get("/bitacora", response_model=list[BitacoraOut], tags=["E1 · Seguridad"],
            summary="HU-1.11 Consultar la bitácora (no se puede editar ni borrar)")
def bitacora(usuario: str | None = None, vin: str | None = None, entidad: str | None = None,
             db: Session = Depends(get_db), _=Depends(requiere(*REVISAN))):
    stmt = select(Bitacora).order_by(Bitacora.id.desc())
    if usuario:
        stmt = stmt.where(Bitacora.usuario == usuario)
    if vin:
        stmt = stmt.where(Bitacora.vin == vin.upper())
    if entidad:
        stmt = stmt.where(Bitacora.entidad == entidad)
    return list(db.scalars(stmt.limit(500)))


# ======================================================================= Catálogo (HU-1.02, HU-1.04)

@router.get("/cuentas", response_model=list[CuentaOut], tags=["E1 · Catálogo"])
def listar_cuentas(db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return list(db.scalars(select(Cuenta).order_by(Cuenta.codigo)))


@router.get("/cuentas/arbol", tags=["E1 · Catálogo"], summary="HU-1.02 Catálogo en forma jerárquica")
def arbol_cuentas(db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    cuentas = list(db.scalars(select(Cuenta).order_by(Cuenta.codigo)))
    nodos = {c.codigo: {**CuentaOut.model_validate(c).model_dump(), "hijas": []} for c in cuentas}
    raiz = []
    for c in cuentas:
        partes = c.codigo.split(".")
        padre = next((".".join(partes[:i]) for i in range(len(partes) - 1, 0, -1)
                      if ".".join(partes[:i]) in nodos), None)
        (nodos[padre]["hijas"] if padre else raiz).append(nodos[c.codigo])
    return raiz


@router.post("/cuentas", response_model=CuentaOut, status_code=201, tags=["E1 · Catálogo"],
             summary="HU-1.02 Crear cuenta con sus reglas de línea y VIN (HU-1.04)")
def crear_cuenta(datos: CuentaIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REVISAN))):
    if db.scalar(select(Cuenta).where(Cuenta.codigo == datos.codigo)):
        raise Conflicto(f"El código {datos.codigo} ya existe")
    padre = datos.codigo.rsplit(".", 1)[0] if "." in datos.codigo else None
    if padre and not db.scalar(select(Cuenta).where(Cuenta.codigo == padre)) and \
            not db.scalar(select(Cuenta).where(Cuenta.codigo == padre.split(".")[0])):
        raise Conflicto(f"No existe la cuenta de agrupación {padre}")
    c = Cuenta(**datos.model_dump())
    db.add(c)
    db.flush()
    db.commit()
    return c


# ======================================================================= Tipo de cambio (HU-1.06)

@router.get("/tipos-cambio", response_model=list[TipoCambioOut], tags=["E1 · Multimoneda"])
def listar_tc(db: Session = Depends(get_db), _=Depends(requiere(*TODOS))):
    return list(db.scalars(select(TipoCambio).order_by(TipoCambio.fecha.desc())))


@router.post("/tipos-cambio", response_model=TipoCambioOut, status_code=201, tags=["E1 · Multimoneda"],
             summary="HU-1.06 Registrar el tipo de cambio de referencia del Banguat (carga manual)")
def registrar_tc(datos: TipoCambioIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REVISAN))):
    return cont.registrar_tipo_cambio(db, datos.fecha, datos.valor, quien.usuario)


# ======================================================================= Partidas (HU-2.01, 2.02)

@router.post("/partidas", response_model=PartidaOut, status_code=201, tags=["E2 · Partidas"],
             summary="HU-2.01 Registrar partida manual (queda en borrador)")
def crear_partida(datos: PartidaIn, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    lineas = [cont.LineaIn(cuenta=l.cuenta, lado=l.lado, monto=l.monto, moneda=l.moneda,
                           linea_negocio=l.linea_negocio, unidad_id=_unidad_id(db, l.vin),
                           detalle=l.detalle, tipo_cambio=l.tipo_cambio) for l in datos.lineas]
    p = cont.crear_partida_manual(db, datos.fecha, datos.concepto, lineas, quien.usuario,
                                  datos.justificacion_tipo_cambio)
    return partida_out(p)


@router.put("/partidas/{partida_id}", response_model=PartidaOut, tags=["E2 · Partidas"],
            summary="Corregir una partida en borrador o devuelta (sólo quien la registró)")
def editar_partida(partida_id: int, datos: PartidaIn, db: Session = Depends(get_db),
                   quien: Usuario = Depends(requiere(*REGISTRAN))):
    lineas = [cont.LineaIn(cuenta=l.cuenta, lado=l.lado, monto=l.monto, moneda=l.moneda,
                           linea_negocio=l.linea_negocio, unidad_id=_unidad_id(db, l.vin),
                           detalle=l.detalle, tipo_cambio=l.tipo_cambio) for l in datos.lineas]
    return partida_out(cont.editar_partida(db, partida_id, datos.fecha, datos.concepto, lineas,
                                           quien.usuario, datos.justificacion_tipo_cambio))


@router.get("/partidas", response_model=list[PartidaOut], tags=["E2 · Partidas"])
def listar_partidas(estado: str | None = Query(default=None, description="BORRADOR, EN_REVISION, CONTABILIZADA, DEVUELTA"),
                    db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    stmt = select(Partida).order_by(Partida.id.desc())
    if estado:
        stmt = stmt.where(Partida.estado == estado)
    return [partida_out(p) for p in db.scalars(stmt.limit(200))]


@router.get("/partidas/{partida_id}", response_model=PartidaOut, tags=["E2 · Partidas"])
def obtener_partida(partida_id: int, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return partida_out(obtener(db, Partida, partida_id, "La partida"))


@router.post("/partidas/{partida_id}/enviar", response_model=PartidaOut, tags=["E2 · Partidas"],
             summary="Enviar a revisión (valida que cuadre)")
def enviar(partida_id: int, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REGISTRAN))):
    return partida_out(cont.enviar_a_revision(db, partida_id, quien.usuario))


@router.post("/partidas/{partida_id}/contabilizar", response_model=PartidaOut, tags=["E2 · Partidas"],
             summary="HU-2.02 Contabilizar (quien registró no puede hacerlo, HU-1.10)")
def contabilizar(partida_id: int, db: Session = Depends(get_db), quien: Usuario = Depends(requiere(*REVISAN))):
    return partida_out(cont.contabilizar(db, partida_id, quien))


@router.post("/partidas/{partida_id}/devolver", response_model=PartidaOut, tags=["E2 · Partidas"])
def devolver(partida_id: int, datos: DevolverIn, db: Session = Depends(get_db),
             quien: Usuario = Depends(requiere(*REVISAN))):
    return partida_out(cont.devolver(db, partida_id, quien, datos.comentario))


# ======================================================================= Consultas (HU-2.16)

@router.get("/contabilidad/balance", tags=["E2 · Consultas"], summary="HU-2.16 Balance de comprobación")
def balance(desde: date | None = None, hasta: date | None = None, linea_negocio: str | None = None,
            vin: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return cont.balance_comprobacion(db, desde, hasta, linea_negocio, _unidad_id(db, vin))


@router.get("/contabilidad/mayor/{codigo}", tags=["E2 · Consultas"], summary="HU-2.16 Mayor de una cuenta")
def mayor(codigo: str, desde: date | None = None, hasta: date | None = None, linea_negocio: str | None = None,
          vin: str | None = None, db: Session = Depends(get_db), _=Depends(requiere(*REGISTRAN))):
    return cont.mayor(db, codigo, desde, hasta, linea_negocio, _unidad_id(db, vin))
