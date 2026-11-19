"""Sesión y permisos. Único lugar donde se decide quién puede qué (regla 4 de CLAUDE.md).

HU-1.09 incluido: alta, suspensión, reactivación y baja de usuarios por el gerente financiero,
contraseñas con mayúscula, minúscula y dígito, bloqueo temporal tras varios intentos fallidos y
cierre de sesión por inactividad (SESION_MINUTOS, renovada con la actividad).
Diferido: rol operativo adicional (pregunta 1 de las épicas, decisión pendiente), cambio de
contraseña por el propio usuario y restablecerla por el administrador, y cambio de rol.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Header
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.comun import config
from app.comun.auditoria import consultar_bitacora  # noqa: F401  contrato de consulta para el router
from app.comun.db import fijar_actor, get_db
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


MENSAJE_LOGIN = (
    "Correo o contraseña incorrectos. Tras varios intentos fallidos la cuenta se bloquea unos minutos."
)


def crear_usuario(db: Session, correo: str, nombre: str, rol: str, clave: str) -> Usuario:
    correo = correo.strip().lower()
    if "@" not in correo:
        raise ErrorNegocio("El correo no tiene un formato válido")
    if not nombre.strip():
        raise ErrorNegocio("El nombre es obligatorio")
    if rol not in ROLES:
        raise ErrorNegocio(f"Rol desconocido: {rol}")
    if len(clave) < CLAVE_MINIMA:
        raise ErrorNegocio(f"La contraseña debe tener al menos {CLAVE_MINIMA} caracteres")
    if not (
        any(c.isupper() for c in clave)
        and any(c.islower() for c in clave)
        and any(c.isdigit() for c in clave)
    ):
        raise ErrorNegocio("La contraseña debe incluir al menos una mayúscula, una minúscula y un dígito")
    if db.scalar(select(Usuario.id).where(Usuario.correo == correo)) is not None:
        raise ErrorNegocio("Ya existe un usuario con ese correo", 409)
    usuario = Usuario(correo=correo, nombre=nombre.strip(), rol=rol, clave_hash=hashear_clave(clave))
    db.add(usuario)
    db.flush()
    return usuario


def iniciar_sesion(db: Session, correo: str, clave: str) -> tuple[str, Usuario]:
    # Con candado: intentos simultáneos contra una cuenta se cuentan uno por uno, no en paralelo.
    usuario = db.scalar(select(Usuario).where(Usuario.correo == correo.lower()).with_for_update())
    ahora = datetime.now(UTC)
    # Mismo mensaje y tiempo si el usuario no existe, está suspendido, de baja o bloqueado: no revela correos.
    sirve = usuario is not None and usuario.activo
    bloqueado = sirve and usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora
    correcta = _clave_correcta(clave, usuario.clave_hash if sirve else _HASH_FALSO)
    if not (sirve and correcta and not bloqueado):
        if sirve and not bloqueado:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= config.INTENTOS_MAXIMOS:
                usuario.bloqueado_hasta = ahora + timedelta(minutes=config.BLOQUEO_MINUTOS)
                usuario.intentos_fallidos = 0
            db.commit()  # el intento cuenta aunque la respuesta sea un error
        raise ErrorNegocio(MENSAJE_LOGIN, 401)
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
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
    ahora = datetime.now(UTC)
    if sesion.expira_en < ahora + timedelta(minutes=config.SESION_MINUTOS - 1):
        # Cierre por inactividad: la actividad renueva la sesión (sin escribir en cada petición).
        sesion.expira_en = ahora + timedelta(minutes=config.SESION_MINUTOS)
        db.commit()  # antes de fijar_actor: set_config es local a la transacción
    fijar_actor(db, usuario.id)
    return usuario


def requiere_rol(*roles: str):
    """Dependencia de FastAPI para proteger rutas: `Depends(requiere_rol(CONTADOR, GERENTE_FINANCIERO))`."""

    def verificar(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise ErrorNegocio("Tu rol no tiene permiso para esta operación", 403)
        return usuario

    return verificar


def estado_usuario(usuario: Usuario) -> str:
    if usuario.baja_en is not None:
        return "baja"
    if not usuario.activo:
        return "suspendido"
    if usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > datetime.now(UTC):
        return "bloqueado"
    return "activo"


def listar_usuarios(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).order_by(Usuario.id)))


def alta_usuario(db: Session, correo: str, nombre: str, rol: str, clave: str) -> Usuario:
    usuario = crear_usuario(db, correo, nombre, rol, clave)
    db.commit()
    return usuario


def _usuario_a_administrar(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise ErrorNegocio("Usuario no encontrado", 404)
    return usuario


def _retirar(db: Session, actor_id: int, usuario_id: int, definitivo: bool) -> Usuario:
    usuario = _usuario_a_administrar(db, usuario_id)
    if usuario.id == actor_id:
        raise ErrorNegocio("No puedes suspenderte ni darte de baja a ti mismo", 409)
    if usuario.baja_en is not None:
        raise ErrorNegocio("El usuario ya está de baja", 409)
    usuario.activo = False
    if definitivo:
        usuario.baja_en = datetime.now(UTC)
    db.execute(delete(Sesion).where(Sesion.usuario_id == usuario.id))
    db.commit()
    return usuario


def suspender_usuario(db: Session, actor_id: int, usuario_id: int) -> Usuario:
    return _retirar(db, actor_id, usuario_id, definitivo=False)


def dar_de_baja_usuario(db: Session, actor_id: int, usuario_id: int) -> Usuario:
    return _retirar(db, actor_id, usuario_id, definitivo=True)


def reactivar_usuario(db: Session, actor_id: int, usuario_id: int) -> Usuario:
    usuario = _usuario_a_administrar(db, usuario_id)
    if usuario.baja_en is not None:
        raise ErrorNegocio("Un usuario de baja no se reactiva", 409)
    usuario.activo = True
    usuario.bloqueado_hasta = None
    usuario.intentos_fallidos = 0
    db.commit()
    return usuario
