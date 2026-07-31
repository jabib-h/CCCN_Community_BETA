"""Configuración central. Todo secreto viene del entorno — nunca hardcodeado
(Ley 8968 / Panorama Legal, Paso 1). En producción falta un secreto = arranque falla."""
import os
import secrets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "data" / "state"

ENV = os.environ.get("HUB_ENV", "dev")  # dev | beta | production
# "dev" es la única corrida que se permite conveniente (secretos y SQLite autogenerados
# en disco local). "beta" (Vercel) y "production" (Azure) corren en filesystem efímero o
# compartido entre instancias: exigen secretos y base de datos explícitos por entorno.
IS_PROD = ENV != "dev"

BASE_URL = os.environ.get("HUB_BASE_URL", "http://localhost:8700").rstrip("/")

DATABASE_URL = os.environ.get("HUB_DATABASE_URL", "")
if not DATABASE_URL:
    if IS_PROD:
        raise RuntimeError("HUB_DATABASE_URL es obligatoria fuera de dev (Postgres: Supabase en beta, Azure en producción).")
    DATABASE_URL = f"sqlite:///{PROJECT_ROOT / 'data' / 'hub_dev.db'}"


def _load_or_create_secret(env_var: str, filename: str) -> str:
    """En prod el secreto DEBE venir del entorno (Key Vault → App Settings).
    En dev se genera una vez y se persiste en data/state/ (gitignored)."""
    value = os.environ.get(env_var, "")
    if value:
        return value
    if IS_PROD:
        raise RuntimeError(f"{env_var} es obligatoria fuera de dev.")
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = STATE_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    value = secrets.token_urlsafe(48)
    path.write_text(value, encoding="utf-8")
    return value


JWT_SECRET = _load_or_create_secret("HUB_JWT_SECRET", "jwt_secret.key")
SESSION_SECRET = _load_or_create_secret("HUB_SESSION_SECRET", "session_secret.key")
JWT_TTL_MINUTES = int(os.environ.get("HUB_JWT_TTL_MINUTES", "60"))

# OAuth institucional y externo. Vacío = proveedor deshabilitado.
GOOGLE_CLIENT_ID = os.environ.get("HUB_GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("HUB_GOOGLE_CLIENT_SECRET", "")
MS_CLIENT_ID = os.environ.get("HUB_MS_CLIENT_ID", "")
MS_CLIENT_SECRET = os.environ.get("HUB_MS_CLIENT_SECRET", "")
MS_TENANT = os.environ.get("HUB_MS_TENANT", "common")

# Portal de libros electrónicos (SaaS de terceros — no se hospeda, se enlaza).
OVERDRIVE_URL = os.environ.get("HUB_OVERDRIVE_URL", "https://centrocultural.overdrive.com/")

MAIL_FROM = os.environ.get("HUB_MAIL_FROM", "hub@centrocultural.cr")
CONTACTO_DATOS = os.environ.get("HUB_CONTACTO_DATOS", "datos@centrocultural.cr")

# Rate limiting (por IP, ventana de 60 s).
RATE_LIMIT_PUBLIC = int(os.environ.get("HUB_RATE_LIMIT_PUBLIC", "60"))
RATE_LIMIT_AUTH = int(os.environ.get("HUB_RATE_LIMIT_AUTH", "10"))

LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_MINUTES = 15

# Circulación de biblioteca — reglas operativas, no secretos.
PRESTAMO_DIAS = int(os.environ.get("HUB_PRESTAMO_DIAS", "14"))
PRESTAMO_MAX_ACTIVOS = int(os.environ.get("HUB_PRESTAMO_MAX_ACTIVOS", "3"))
MULTA_DIARIA_CRC = int(os.environ.get("HUB_MULTA_DIARIA_CRC", "200"))

# Retención de bitácora de auditoría (días); purga vía tarea de mantenimiento.
AUDIT_RETENTION_DAYS = int(os.environ.get("HUB_AUDIT_RETENTION_DAYS", "1095"))  # 3 años
