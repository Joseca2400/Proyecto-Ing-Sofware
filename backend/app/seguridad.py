"""HU-1.09: contraseñas con hash, sesiones con token y reglas mínimas de contraseña.

Usa sólo la biblioteca estándar (PBKDF2-SHA256), sin dependencias que compilar.
Bloqueo por intentos e inactividad quedan diferidos al Sprint 2 (Sprint1.md, sección 11).
"""

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import config
from app.models import SesionUsuario, Usuario
from app.services.base import ErrorNegocio


def hash_password(password: str) -> str:
    sal = secrets.token_hex(16)
    n = config.ITERACIONES_HASH
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), n).hex()
    return f"pbkdf2_sha256${n}${sal}${digest}"


def verificar_password(password: str, almacenado: str) -> bool:
    try:
        _, n, sal, digest = almacenado.split("$")
        calculado = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(sal), int(n)).hex()
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(calculado, digest)


def validar_complejidad(password: str) -> None:
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise ErrorNegocio("La contraseña debe tener al menos 8 caracteres, con letras y números")


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def iniciar_sesion(db: Session, usuario: str, password: str) -> tuple[str, Usuario, datetime]:
    u = db.scalar(select(Usuario).where(Usuario.usuario == usuario))
    # Mismo mensaje para usuario inexistente o contraseña incorrecta.
    if u is None or not u.activo or not verificar_password(password, u.password_hash):
        raise ErrorNegocio("Usuario o contraseña incorrectos", 401)
    token = secrets.token_urlsafe(32)
    expira = datetime.now(timezone.utc) + timedelta(hours=config.HORAS_SESION)
    db.add(SesionUsuario(usuario_id=u.id, token_hash=_hash_token(token), expira_en=expira))
    db.commit()
    return token, u, expira


def usuario_de_token(db: Session, token: str) -> tuple[Usuario, SesionUsuario] | None:
    sesion = db.scalar(select(SesionUsuario).where(SesionUsuario.token_hash == _hash_token(token)))
    if sesion is None or sesion.cerrada:
        return None
    expira = sesion.expira_en if sesion.expira_en.tzinfo else sesion.expira_en.replace(tzinfo=timezone.utc)
    if expira < datetime.now(timezone.utc) or not sesion.usuario.activo:
        return None
    return sesion.usuario, sesion


def cerrar_sesion(db: Session, sesion: SesionUsuario) -> None:
    sesion.cerrada = True
    db.commit()
