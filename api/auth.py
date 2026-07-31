"""Dependencias de autenticación, RBAC y acceso por módulo.

Scoping SIEMPRE server-side desde el JWT (Panorama Legal, Paso 4): jamás confiar en
rol, sede, user_id ni membresías que vengan del body o del query string.
"""
import jwt as pyjwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from .db import engine, membresias, personas, users, utcnow
from .modules import BY_SLUG, puede_entrar
from .security import decode_token

_bearer = HTTPBearer(auto_error=False)


def get_current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if creds is None:
        raise HTTPException(401, "No autenticado")
    try:
        payload = decode_token(creds.credentials)
    except pyjwt.PyJWTError:
        raise HTTPException(401, "Token inválido o expirado")
    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.id == int(payload["sub"]))).first()
        if row is None or not row.active:
            raise HTTPException(401, "Cuenta inactiva")
        sede = None
        if row.persona_id:
            p = conn.execute(select(personas.c.sede).where(personas.c.id == row.persona_id)).first()
            sede = p.sede if p else None
    # El rol se relee de la BD, no del token: revocar un rol no debe esperar a que expire el JWT.
    return {"id": row.id, "email": row.email, "role": row.role,
            "persona_id": row.persona_id, "display_name": row.display_name, "sede": sede}


def membresias_activas(user_id: int) -> set[str]:
    """Tipos de membresía vigentes hoy. Vencida o suspendida no cuenta."""
    now = utcnow()
    with engine.connect() as conn:
        rows = conn.execute(select(membresias.c.tipo, membresias.c.vence_at)
                            .where((membresias.c.user_id == user_id)
                                   & (membresias.c.estado == "activa"))).fetchall()
    activas = set()
    for r in rows:
        vence = r.vence_at
        if vence is not None and vence.tzinfo is None:
            from datetime import timezone
            vence = vence.replace(tzinfo=timezone.utc)
        if vence is None or vence > now:
            activas.add(r.tipo)
    return activas


def require_role(*roles: str):
    def dep(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise HTTPException(403, "Permisos insuficientes")
        return user
    return dep


def require_modulo(slug: str):
    """Puerta de entrada a un módulo. Devuelve el usuario para que el endpoint no
    tenga que volver a resolverlo."""
    def dep(user: dict = Depends(get_current_user)) -> dict:
        modulo = BY_SLUG.get(slug)
        if modulo is None:
            raise HTTPException(404, "Módulo no encontrado")
        if not puede_entrar(modulo, user["role"], membresias_activas(user["id"])):
            raise HTTPException(403, f"Este módulo requiere una membresía {modulo['requiere_membresia']} vigente")
        return user
    return dep


def client_ip(request: Request) -> str:
    # Detrás de Azure App Service el cliente real viene en X-Forwarded-For.
    fwd = request.headers.get("x-forwarded-for")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")
