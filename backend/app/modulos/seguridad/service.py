"""Sesión y permisos. Único lugar donde se decide quién puede qué (regla 4 de CLAUDE.md)."""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.comun import config
from app.comun.db import get_db
from app.comun.errores import ErrorNegocio
from app.modulos.seguridad.models import Sesion, Usuario

AUXILIAR_CONTABLE = "auxiliar_contable"
CONTADOR = "contador"
GERENTE_FINANCIERO = "gerente_financiero"
GERENCIA = "gerencia"
ROLES = (AUXILIAR_CONTABLE, CONTADOR, GERENTE_FINANCIERO, GERENCIA)

CLAVE_MINIMA = 12

# Costo para hashes nuevos; cada hash guarda el suyo, así que subirlo no invalida los existentes.
_N, _R, _P = 2**15, 8, 1
_MEMORIA = 128 * 1024 * 1024  # scrypt falla si n*r*128 B supera el límite por defecto (32 MiB)


def hashear_clave(clave: str) -> str:
    sal = secrets.token_bytes(16)
    derivada = hashlib.scrypt(clave.encode(), salt=sal, n=_N, r=_R, p=_P, maxmem=_MEMORIA)
    return f"scrypt${_N}${_R}${_P}${sal.hex()}${derivada.hex()}"


def _clave_correcta(clave: str, guardada: str) -> bool:
    _, n, r, p, sal, esperada = guardada.split("$")
    derivada = hashlib.scrypt(
        clave.encode(), salt=bytes.fromhex(sal), n=int(n), r=int(r), p=int(p), maxmem=_MEMORIA
    )
    return hmac.compare_digest(derivada.hex(), esperada)


# Se compara contra este hash cuando el correo no sirve, para que tarde lo mismo que uno real.
_HASH_FALSO = hashear_clave("clave-que-nadie-usa")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def crear_usuario(db: Session, correo: str, nombre: str, rol: str, clave: str) -> Usuario:
    if rol not in ROLES:
        raise ErrorNegocio(f"Rol desconocido: {rol}")
    if len(clave) < CLAVE_MINIMA:
        raise ErrorNegocio(f"La contraseña debe tener al menos {CLAVE_MINIMA} caracteres")
    usuario = Usuario(correo=correo.lower(), nombre=nombre, rol=rol, clave_hash=hashear_clave(clave))
    db.add(usuario)
    db.flush()
    return usuario


def iniciar_sesion(db: Session, correo: str, clave: str) -> tuple[str, Usuario]:
    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo.lower()))
    # Mismo mensaje y tiempo si el usuario no existe, está de baja o la clave es errónea: no revela correos.
    sirve = usuario is not None and usuario.activo
    correcta = _clave_correcta(clave, usuario.clave_hash if sirve else _HASH_FALSO)
    if not (sirve and correcta):
        raise ErrorNegocio("Correo o contraseña incorrectos", 401)
    ahora = datetime.now(UTC)
    db.execute(delete(Sesion).where(Sesion.expira_en < ahora))  # limpieza de sesiones vencidas
    token = secrets.token_urlsafe(32)
    expira = ahora + timedelta(minutes=config.SESION_MINUTOS)
    db.add(Sesion(token_hash=_hash_token(token), usuario_id=usuario.id, expira_en=expira))
    db.commit()
    return token, usuario


def cerrar_sesion(db: Session, token: str) -> None:
    db.execute(delete(Sesion).where(Sesion.token_hash == _hash_token(token)))
    db.commit()


def token_del_encabezado(autorizacion: str | None) -> str:
    esquema, _, token = (autorizacion or "").partition(" ")
    if esquema.lower() != "bearer" or not token:
        raise ErrorNegocio("Falta iniciar sesión", 401)
    return token


def usuario_actual(
    autorizacion: str | None = Header(default=None, alias="Authorization"), db: Session = Depends(get_db)
) -> Usuario:
    """Dependencia de FastAPI: el usuario de la sesión vigente, o 401."""
    sesion = db.get(Sesion, _hash_token(token_del_encabezado(autorizacion)))
    if sesion is None or sesion.expira_en < datetime.now(UTC):
        raise ErrorNegocio("La sesión expiró o no es válida", 401)
    usuario = db.get(Usuario, sesion.usuario_id)
    if usuario is None or not usuario.activo:
        raise ErrorNegocio("La sesión expiró o no es válida", 401)
    return usuario


def requiere_rol(*roles: str):
    """Dependencia de FastAPI para proteger rutas: `Depends(requiere_rol(CONTADOR, GERENTE_FINANCIERO))`."""

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise ErrorNegocio("Tu rol no tiene permiso para esta operación", 403)
        return usuario

    return verificar
