"""Autenticación del Hub: registro local con consentimiento informado, login y OAuth.

Reglas legales aplicadas (Ley 8968 / Panorama Legal §3.1):
- Consentimiento expreso, no preseleccionado, ANTES de crear la cuenta (art. 5).
- Menores de 18: autorregistro BLOQUEADO; la cuenta la gestiona el CCCN con
  consentimiento de la persona tutora (art. 196 bis Código Penal).
- Mensajes de error genéricos en auth: nunca distinguir "no existe" de "clave errónea".
"""
from datetime import date, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update

from .. import config
from ..auth import client_ip, get_current_user
from ..db import audit, engine, users, utcnow
from ..security import create_token, hash_password, rate_limiter, verify_password

router = APIRouter()

LEGAL_VERSION = "2026-07"

try:
    from authlib.integrations.starlette_client import OAuth
    _oauth = OAuth()
    if config.GOOGLE_CLIENT_ID:
        _oauth.register(
            "google",
            client_id=config.GOOGLE_CLIENT_ID, client_secret=config.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if config.MS_CLIENT_ID:
        _oauth.register(
            "microsoft",
            client_id=config.MS_CLIENT_ID, client_secret=config.MS_CLIENT_SECRET,
            server_metadata_url=f"https://login.microsoftonline.com/{config.MS_TENANT}/v2.0/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
except ImportError:  # Authlib no instalado: solo auth local
    _oauth = None


def _check_rate(request: Request):
    if not rate_limiter.allow(f"auth:{client_ip(request)}", config.RATE_LIMIT_AUTH):
        raise HTTPException(429, "Demasiados intentos; probá de nuevo en un minuto")


def _aware(dt):
    """Postgres devuelve datetimes con tz; SQLite no. Comparar sin esto revienta."""
    return dt.replace(tzinfo=timezone.utc) if dt is not None and dt.tzinfo is None else dt


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)
    nombre: str = Field(min_length=2, max_length=200)
    fecha_nacimiento: date
    accept_privacy: bool
    accept_tos: bool


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ConsentIn(BaseModel):
    accept_privacy: bool
    accept_tos: bool


def _age(born: date) -> int:
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


@router.post("/auth/register", status_code=201)
def register(body: RegisterIn, request: Request):
    _check_rate(request)
    if not (body.accept_privacy and body.accept_tos):
        raise HTTPException(422, "Debés aceptar la Política de Privacidad y los Términos de Uso "
                                 "(el consentimiento no puede presumirse)")
    if _age(body.fecha_nacimiento) < 18:
        raise HTTPException(403, "El autorregistro de personas menores de edad no está permitido. "
                                 f"La persona tutora debe gestionar la cuenta: {config.CONTACTO_DATOS}")
    now = utcnow()
    email = body.email.lower()
    with engine.begin() as conn:
        if conn.execute(select(users.c.id).where(users.c.email == email)).first():
            raise HTTPException(409, "Ya existe una cuenta con ese correo")
        result = conn.execute(users.insert().values(
            email=email, password_hash=hash_password(body.password),
            role="user", display_name=body.nombre.strip(), active=True,
            accepted_privacy_at=now, accepted_tos_at=now, legal_version=LEGAL_VERSION,
            created_at=now,
        ))
        uid = result.inserted_primary_key[0]
        audit(conn, actor_user_id=uid, actor_ip=client_ip(request),
              accion="registro", entidad="user", entidad_id=uid,
              detalle={"metodo": "local", "legal_version": LEGAL_VERSION})
    return {"token": create_token(user_id=uid, role="user", email=email)}


@router.post("/auth/login")
def login(body: LoginIn, request: Request):
    _check_rate(request)
    generic = HTTPException(401, "Correo o contraseña incorrectos")

    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.email == body.email.lower())).first()
    if row is None or not row.active or not row.password_hash:
        raise generic

    locked = _aware(row.locked_until)
    if locked and locked > utcnow():
        raise HTTPException(423, "Cuenta bloqueada temporalmente por intentos fallidos; probá más tarde")

    if not verify_password(body.password, row.password_hash):
        # El contador se confirma en su PROPIA transacción y la excepción se lanza FUERA:
        # dentro de `engine.begin()` el raise haría rollback y el bloqueo nunca ocurriría.
        fails = row.failed_logins + 1
        vals = {"failed_logins": fails}
        if fails >= config.LOGIN_MAX_FAILURES:
            vals["locked_until"] = utcnow() + timedelta(minutes=config.LOGIN_LOCKOUT_MINUTES)
            vals["failed_logins"] = 0
        with engine.begin() as conn:
            conn.execute(update(users).where(users.c.id == row.id).values(**vals))
            audit(conn, actor_user_id=row.id, actor_ip=client_ip(request),
                  accion="login_fallido", entidad="user", entidad_id=row.id,
                  detalle={"intentos": fails, "bloqueada": "locked_until" in vals})
        raise generic

    with engine.begin() as conn:
        conn.execute(update(users).where(users.c.id == row.id).values(
            failed_logins=0, locked_until=None, last_login=utcnow()))
        audit(conn, actor_user_id=row.id, actor_ip=client_ip(request),
              accion="login", entidad="user", entidad_id=row.id, detalle={"metodo": "local"})
    return {"token": create_token(user_id=row.id, role=row.role, email=row.email)}


@router.get("/auth/me")
def me(user: dict = Depends(get_current_user)):
    with engine.connect() as conn:
        row = conn.execute(select(users).where(users.c.id == user["id"])).first()
    return {"id": row.id, "email": row.email, "role": row.role, "display_name": row.display_name,
            "persona_id": row.persona_id, "sede": user["sede"],
            "needs_consent": row.accepted_privacy_at is None or row.accepted_tos_at is None,
            "legal_version": row.legal_version}


@router.post("/auth/consent")
def record_consent(body: ConsentIn, request: Request, user: dict = Depends(get_current_user)):
    """Las cuentas creadas vía OAuth registran acá su consentimiento expreso (primer acceso)."""
    if not (body.accept_privacy and body.accept_tos):
        raise HTTPException(422, "El consentimiento debe ser expreso para ambas políticas")
    now = utcnow()
    with engine.begin() as conn:
        conn.execute(update(users).where(users.c.id == user["id"]).values(
            accepted_privacy_at=now, accepted_tos_at=now, legal_version=LEGAL_VERSION))
        audit(conn, actor_user_id=user["id"], actor_ip=client_ip(request),
              accion="consentimiento", entidad="user", entidad_id=user["id"],
              detalle={"legal_version": LEGAL_VERSION})
    return {"ok": True, "legal_version": LEGAL_VERSION}


# ---------- OAuth ----------

def _provider_or_404(provider: str):
    if _oauth is None or provider not in ("google", "microsoft"):
        raise HTTPException(404, "Proveedor no disponible")
    client = _oauth.create_client(provider)
    if client is None:
        raise HTTPException(404, "Proveedor no configurado")
    return client


@router.get("/auth/oauth/{provider}/login")
async def oauth_login(provider: str, request: Request):
    client = _provider_or_404(provider)
    return await client.authorize_redirect(
        request, f"{config.BASE_URL}/api/v1/auth/oauth/{provider}/callback")


@router.get("/auth/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request):
    client = _provider_or_404(provider)
    try:
        token = await client.authorize_access_token(request)
    except Exception:
        raise HTTPException(401, "Autenticación OAuth fallida")
    info = token.get("userinfo") or {}
    email = (info.get("email") or "").lower()
    sub = info.get("sub") or ""
    if not email or not sub:
        raise HTTPException(401, "El proveedor no entregó un correo verificable")
    if info.get("email_verified") is False:
        raise HTTPException(401, "El correo de la cuenta no está verificado con el proveedor")
    nombre = info.get("name") or email.split("@")[0]

    with engine.begin() as conn:
        row = conn.execute(select(users).where(
            (users.c.oauth_provider == provider) & (users.c.oauth_sub == sub))).first()
        if row is None:
            row = conn.execute(select(users).where(users.c.email == email)).first()
            if row is not None:
                # Vincular identidad OAuth a cuenta local existente con el mismo correo verificado.
                conn.execute(update(users).where(users.c.id == row.id).values(
                    oauth_provider=provider, oauth_sub=sub))
            else:
                result = conn.execute(users.insert().values(
                    email=email, oauth_provider=provider, oauth_sub=sub,
                    role="user", display_name=nombre, active=True, created_at=utcnow()))
                row = conn.execute(select(users).where(
                    users.c.id == result.inserted_primary_key[0])).first()
        if not row.active:
            raise HTTPException(401, "Cuenta inactiva")
        conn.execute(update(users).where(users.c.id == row.id).values(last_login=utcnow()))
        audit(conn, actor_user_id=row.id, actor_ip=client_ip(request),
              accion="login", entidad="user", entidad_id=row.id, detalle={"metodo": provider})

    jwt_token = create_token(user_id=row.id, role=row.role, email=row.email)
    # El token viaja en el fragment (#): nunca en query string, que quedaría en logs y Referer.
    return RedirectResponse(url=f"{config.BASE_URL}/app/hub.html#token={jwt_token}")
