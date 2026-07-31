"""Esquema y conexión únicos del Hub. SQLAlchemy Core (sin ORM) — portable Postgres (prod) / SQLite (tests/dev).

UNA base, UNA tabla de personas, UNA de usuarios: todos los módulos (Community of
Practice, Revista, Biblioteca, Badges, membresías) leen y escriben aquí. Ese es el
punto del Hub; si un módulo necesita su propia base, la decisión se discute antes.

Reglas duras EN la base, no en la app:
- `audit_log` append-only forzado con triggers (Panorama Legal, Paso 6).
- Unicidad donde la duplicación sería un error de negocio (no un préstamo doble del
  mismo ejemplar, no dos personas con el mismo SIS-ID).
- Dinero en enteros (céntimos). Nunca float: SQLite degrada Numeric a float y la
  aritmética de cobros no admite error de redondeo.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String,
    Table, Text, UniqueConstraint, create_engine, event, text,
)

from . import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"check_same_thread": False} if config.DATABASE_URL.startswith("sqlite") else {},
)

# SQLite necesita FKs activadas por conexión (en Postgres es no-op).
if config.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_fk(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

metadata = MetaData()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


# ======================================================================
# IDENTIDAD — el núcleo unificado
# ======================================================================

# `personas` es el registro de la persona física (existe aunque nunca abra una cuenta:
# un ejemplar se presta a una persona, una credencial se emite a una persona).
# `users` es la credencial de acceso al Hub. Una persona puede no tener usuario;
# un usuario siempre apunta a una persona una vez vinculado.
personas = Table(
    "personas", metadata,
    Column("id", Integer, primary_key=True),
    Column("kind", String(10), nullable=False),       # interno | externo
    Column("sis_id", String(50), unique=True),        # interno: mismo SIS-ID de Canvas/AIH
    Column("cedula", String(30)),                     # externo (opcional)
    Column("nombre", String(200), nullable=False),
    Column("email", String(255), nullable=False),
    Column("telefono", String(40)),
    Column("sede", String(60)),                       # scoping por sede (RBAC, Panorama Legal §3.3)
    Column("es_menor", Boolean, nullable=False, default=False),
    # Menores: toda publicación/préstamo queda bloqueado sin consentimiento del tutor
    # registrado por un administrador (art. 196 bis Código Penal).
    Column("tutor_consent_at", DateTime(timezone=True)),
    Column("tutor_consent_por", String(200)),
    # Perfil público (backpack de credenciales, autoría en la revista): NULL = privado.
    Column("public_slug", String(64), unique=True),
    Column("consent_publico_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("password_hash", String(255)),            # NULL para cuentas solo-OAuth
    Column("oauth_provider", String(20)),            # google | microsoft
    Column("oauth_sub", String(255)),
    # user  = persona de la comunidad
    # staff = opera un módulo (circulación, edición de contenidos) — sin acceso a config
    # admin = administra el Hub completo
    Column("role", String(20), nullable=False, default="user"),
    Column("display_name", String(200), nullable=False, default=""),
    Column("persona_id", Integer, ForeignKey("personas.id", ondelete="RESTRICT")),
    Column("active", Boolean, nullable=False, default=True),
    Column("failed_logins", Integer, nullable=False, default=0),
    Column("locked_until", DateTime(timezone=True)),
    # Consentimiento informado (Ley 8968 art. 5): cuándo aceptó qué versión.
    Column("accepted_privacy_at", DateTime(timezone=True)),
    Column("accepted_tos_at", DateTime(timezone=True)),
    Column("legal_version", String(20)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("last_login", DateTime(timezone=True)),
    UniqueConstraint("oauth_provider", "oauth_sub", name="uq_oauth_identity"),
)


# ======================================================================
# MEMBRESÍAS Y COBROS
# ======================================================================

# Una membresía habilita módulos (ver api/modules.py). Vencida ≠ borrada: el
# histórico se conserva, el acceso se decide por estado + vence_at.
membresias = Table(
    "membresias", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
    Column("tipo", String(30), nullable=False),       # biblioteca | docente | institucional | investigador
    Column("estado", String(15), nullable=False, default="activa"),  # activa|vencida|suspendida
    Column("inicia_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("vence_at", DateTime(timezone=True)),      # NULL = sin vencimiento
    Column("otorgada_por", Integer, ForeignKey("users.id")),
    Column("notas", Text),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    UniqueConstraint("user_id", "tipo", name="uq_membresia_por_tipo"),
)

# Libro mayor de cobros. Registra lo que se DEBE, no lo que se cobra: la integración
# con pasarela de pago es una decisión pendiente (ver ARQUITECTURA.md §Cobros).
# ponytail: montos en céntimos (entero). Si algún día hay multimoneda con conversión,
# agregar tasa y fecha de conversión — no cambiar el tipo.
cargos = Table(
    "cargos", metadata,
    Column("id", Integer, primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
    Column("concepto", String(30), nullable=False),   # membresia|multa|reposicion|inscripcion|publicacion
    Column("descripcion", String(255), nullable=False),
    Column("monto_centimos", Integer, nullable=False),
    Column("moneda", String(3), nullable=False, default="CRC"),
    Column("estado", String(15), nullable=False, default="pendiente"),  # pendiente|pagado|anulado
    Column("vence_at", DateTime(timezone=True)),
    Column("pagado_at", DateTime(timezone=True)),
    Column("referencia_pago", String(120)),           # id de la pasarela cuando exista
    Column("origen_tipo", String(20)),                # prestamo|membresia|reserva…
    Column("origen_id", String(64)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)


# ======================================================================
# CONTENIDO — Community of Practice + Revista académica
# ======================================================================

# Una sola tabla: charla, taller, artículo, blog y podcast son el mismo objeto
# (metadatos + un enlace + una regla de acceso). Lo que cambia es `modulo`/`tipo`.
# ponytail: si la revista incorpora revisión por pares, esa es una tabla aparte
# (`revisiones`) que apunta acá — no una segunda tabla de contenido.
recursos = Table(
    "recursos", metadata,
    Column("id", Integer, primary_key=True),
    Column("modulo", String(20), nullable=False),     # cop | revista
    Column("tipo", String(20), nullable=False),       # charla|taller|conferencia|vlog|articulo|blog|podcast
    Column("titulo", String(300), nullable=False),
    Column("resumen", Text, nullable=False, default=""),
    Column("autores", String(500), nullable=False, default=""),
    Column("idioma", String(5), nullable=False, default="es"),
    Column("url", String(500), nullable=False),       # video, audio o PDF alojado
    Column("portada_url", String(500)),
    Column("duracion_min", Integer),                  # audiovisual
    # Identificadores de publicación académica (revista). ISSN identifica la revista;
    # DOI identifica el artículo. ISBN solo aplica a libros/monografías.
    Column("doi", String(120), unique=True),
    Column("issn", String(20)),
    Column("isbn", String(20)),
    Column("volumen", String(20)),
    Column("numero", String(20)),
    Column("paginas", String(20)),
    Column("licencia", String(60), nullable=False, default="CC BY-NC-SA 4.0"),
    Column("palabras_clave", String(300), nullable=False, default=""),
    Column("acceso", String(15), nullable=False, default="autenticado"),  # publico|autenticado|membresia
    Column("estado", String(15), nullable=False, default="borrador"),     # borrador|publicado|retirado
    Column("publicado_at", DateTime(timezone=True)),
    Column("created_by", Integer, ForeignKey("users.id"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=utcnow),
)


# ======================================================================
# BIBLIOTECA — acervo físico, préstamos y espacios
# ======================================================================

items = Table(
    "items", metadata,
    Column("id", Integer, primary_key=True),
    Column("sede", String(60), nullable=False),
    Column("titulo", String(300), nullable=False),
    Column("autor", String(300), nullable=False, default=""),
    Column("editorial", String(200)),
    Column("anio", Integer),
    Column("isbn", String(20)),
    Column("tipo", String(20), nullable=False, default="libro"),  # libro|audiovisual|equipo|revista
    Column("signatura", String(60), nullable=False),   # clasificación en estante
    Column("codigo_barras", String(60), nullable=False, unique=True),  # identifica EL ejemplar
    Column("estado", String(15), nullable=False, default="disponible"),  # disponible|prestado|reparacion|baja
    Column("prestable", Boolean, nullable=False, default=True),   # false = solo consulta en sala
    Column("valor_reposicion_centimos", Integer),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

prestamos = Table(
    "prestamos", metadata,
    Column("id", Integer, primary_key=True),
    Column("item_id", Integer, ForeignKey("items.id", ondelete="RESTRICT"), nullable=False),
    Column("persona_id", Integer, ForeignKey("personas.id", ondelete="RESTRICT"), nullable=False),
    Column("prestado_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("vence_at", DateTime(timezone=True), nullable=False),
    Column("devuelto_at", DateTime(timezone=True)),
    Column("renovaciones", Integer, nullable=False, default=0),
    Column("atendido_por", Integer, ForeignKey("users.id"), nullable=False),
    Column("cargo_id", Integer, ForeignKey("cargos.id")),  # multa por atraso, si la hubo
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)

espacios = Table(
    "espacios", metadata,
    Column("id", Integer, primary_key=True),
    Column("sede", String(60), nullable=False),
    Column("nombre", String(120), nullable=False),
    Column("tipo", String(20), nullable=False),        # sala|laboratorio|auditorio|cabina
    Column("capacidad", Integer, nullable=False, default=1),
    Column("requiere_membresia", Boolean, nullable=False, default=False),
    Column("activo", Boolean, nullable=False, default=True),
    UniqueConstraint("sede", "nombre", name="uq_espacio_por_sede"),
)

reservas = Table(
    "reservas", metadata,
    Column("id", Integer, primary_key=True),
    Column("espacio_id", Integer, ForeignKey("espacios.id", ondelete="RESTRICT"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
    Column("inicia_at", DateTime(timezone=True), nullable=False),
    Column("termina_at", DateTime(timezone=True), nullable=False),
    Column("motivo", String(255), nullable=False, default=""),
    Column("estado", String(15), nullable=False, default="confirmada"),  # confirmada|cancelada|cumplida
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
)


# ======================================================================
# CUMPLIMIENTO — bitácora y derechos ARCO (Ley 8968)
# ======================================================================

audit_log = Table(
    "audit_log", metadata,
    Column("id", Integer, primary_key=True),
    Column("ts", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("actor_user_id", Integer),
    Column("actor_ip", String(64)),
    Column("accion", String(60), nullable=False),
    Column("entidad", String(40), nullable=False),
    Column("entidad_id", String(64)),
    Column("detalle", JSON),
)

# Canal de derechos ARCO: Acceso, Rectificación, Cancelación, Oposición.
arco_requests = Table(
    "arco_requests", metadata,
    Column("id", Integer, primary_key=True),
    Column("created_at", DateTime(timezone=True), nullable=False, default=utcnow),
    Column("email", String(255), nullable=False),
    Column("nombre", String(200), nullable=False),
    Column("tipo", String(15), nullable=False),        # acceso|rectificacion|cancelacion|oposicion
    Column("detalle", Text, nullable=False),
    Column("estado", String(15), nullable=False, default="pendiente"),  # pendiente|atendida
    Column("atendida_at", DateTime(timezone=True)),
    Column("atendida_por", Integer, ForeignKey("users.id")),
    Column("respuesta", Text),
)

# Rate limiting por ventana fija (60s), en BD: el proceso ya no puede guardar el
# contador en memoria porque corre serverless (múltiples instancias, sin estado
# entre invocaciones). Ver security.RateLimiter.
rate_limit_hits = Table(
    "rate_limit_hits", metadata,
    Column("rl_key", String(200), primary_key=True),
    Column("bucket", Integer, primary_key=True),
    Column("count", Integer, nullable=False, server_default="0"),
)


_AUDIT_TRIGGERS_PG = """
CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'audit_log es append-only'; END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_audit_no_update ON audit_log;
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
"""

_AUDIT_TRIGGERS_SQLITE = [
    "CREATE TABLE IF NOT EXISTS _maintenance_flag (key TEXT PRIMARY KEY, value TEXT);",
    "CREATE TRIGGER IF NOT EXISTS trg_audit_no_update BEFORE UPDATE ON audit_log "
    "BEGIN SELECT RAISE(ABORT, 'audit_log es append-only'); END;",
    # La purga por retención es la ÚNICA excepción y se habilita con el flag.
    "CREATE TRIGGER IF NOT EXISTS trg_audit_no_delete BEFORE DELETE ON audit_log "
    "WHEN (SELECT value FROM _maintenance_flag WHERE key='purge') IS NULL "
    "BEGIN SELECT RAISE(ABORT, 'audit_log es append-only'); END;",
]


def init_db() -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            conn.execute(text(_AUDIT_TRIGGERS_PG))
        else:
            for stmt in _AUDIT_TRIGGERS_SQLITE:
                conn.execute(text(stmt))


def audit(conn, *, actor_user_id=None, actor_ip=None, accion: str, entidad: str,
          entidad_id=None, detalle=None) -> None:
    """Registrar en bitácora. Usar SIEMPRE dentro de la MISMA transacción de la acción:
    si la acción se revierte, su registro también — y si el registro falla, la acción no ocurre."""
    conn.execute(audit_log.insert().values(
        ts=utcnow(), actor_user_id=actor_user_id, actor_ip=actor_ip,
        accion=accion, entidad=entidad,
        entidad_id=str(entidad_id) if entidad_id is not None else None,
        detalle=detalle,
    ))
