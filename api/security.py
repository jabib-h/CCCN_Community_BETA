"""Contraseñas (Argon2), JWT y rate limiting.

La firma asimétrica Ed25519 (assertions Open Badges / VC) llega con la absorción del
Badge System — ver docs/MIGRACION_BADGES.md; se copia tal cual desde ese repo.
"""
import hashlib
import time
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from sqlalchemy import text

from . import config
from .db import engine, utcnow

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_token(*, user_id: int, role: str, email: str) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id), "role": role, "email": email,
        "iat": now, "exp": now + timedelta(minutes=config.JWT_TTL_MINUTES),
        "iss": config.BASE_URL,
    }
    return jwt.encode(payload, config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, config.JWT_SECRET, algorithms=["HS256"], issuer=config.BASE_URL)


def hash_opaque_token(token: str) -> str:
    """Los tokens de un solo uso se guardan hasheados: una fuga de la BD no los revela."""
    return hashlib.sha256(token.encode()).hexdigest()


# ---------- Rate limiting ----------
# Contador en BD (ventana fija de 60s), no en memoria: el proceso corre serverless en
# beta (Vercel) y puede escalar horizontal en producción (Azure) — ninguno de los dos
# comparte memoria entre instancias/invocaciones.
# ponytail: ventana fija (no deslizante) permite hasta 2x el límite en el borde de la
# ventana, y las filas de claves que dejan de pegar quedan sin purgar. Aceptable para
# el volumen actual (login + ARCO); si crece, cronjob DELETE WHERE bucket < now-1.
class RateLimiter:
    def allow(self, key: str, max_per_minute: int) -> bool:
        bucket = int(time.time() // 60)
        with engine.begin() as conn:
            conn.execute(text(
                "DELETE FROM rate_limit_hits WHERE rl_key = :k AND bucket < :b"
            ), {"k": key, "b": bucket})
            row = conn.execute(text(
                "INSERT INTO rate_limit_hits (rl_key, bucket, count) VALUES (:k, :b, 1) "
                "ON CONFLICT (rl_key, bucket) DO UPDATE SET count = rate_limit_hits.count + 1 "
                "RETURNING count"
            ), {"k": key, "b": bucket}).fetchone()
        return row[0] <= max_per_minute


rate_limiter = RateLimiter()
