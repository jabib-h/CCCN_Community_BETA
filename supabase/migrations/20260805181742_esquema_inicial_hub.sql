-- Esquema inicial del Hub (CCCN Community BETA).
--
-- GENERADO desde api/db.py con `python -m tools.schema_sql`. api/db.py es la única
-- fuente de verdad del esquema; este archivo es un artefacto derivado. Si cambia el
-- esquema, NO se regenera este archivo: se escribe una migración incremental nueva.
--
-- Incluye tres cosas que no son opcionales:
--   1. Las tablas.
--   2. RLS habilitado y permisos revocados a anon/authenticated en todas ellas. El Hub
--      no usa el Data API de Supabase (habla Postgres directo con su propia auth), y sin
--      esto las tablas quedarían accesibles con la clave anon desde cualquier navegador.
--   3. Los triggers que hacen audit_log append-only (Panorama Legal, Paso 6).

CREATE TABLE audit_log (
	id SERIAL NOT NULL, 
	ts TIMESTAMP WITH TIME ZONE NOT NULL, 
	actor_user_id INTEGER, 
	actor_ip VARCHAR(64), 
	accion VARCHAR(60) NOT NULL, 
	entidad VARCHAR(40) NOT NULL, 
	entidad_id VARCHAR(64), 
	detalle JSON, 
	PRIMARY KEY (id)
);

CREATE TABLE espacios (
	id SERIAL NOT NULL, 
	sede VARCHAR(60) NOT NULL, 
	nombre VARCHAR(120) NOT NULL, 
	tipo VARCHAR(20) NOT NULL, 
	capacidad INTEGER NOT NULL, 
	requiere_membresia BOOLEAN NOT NULL, 
	activo BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_espacio_por_sede UNIQUE (sede, nombre)
);

CREATE TABLE items (
	id SERIAL NOT NULL, 
	sede VARCHAR(60) NOT NULL, 
	titulo VARCHAR(300) NOT NULL, 
	autor VARCHAR(300) NOT NULL, 
	editorial VARCHAR(200), 
	anio INTEGER, 
	isbn VARCHAR(20), 
	tipo VARCHAR(20) NOT NULL, 
	signatura VARCHAR(60) NOT NULL, 
	codigo_barras VARCHAR(60) NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	prestable BOOLEAN NOT NULL, 
	valor_reposicion_centimos INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (codigo_barras)
);

CREATE TABLE personas (
	id SERIAL NOT NULL, 
	kind VARCHAR(10) NOT NULL, 
	sis_id VARCHAR(50), 
	cedula VARCHAR(30), 
	nombre VARCHAR(200) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	telefono VARCHAR(40), 
	sede VARCHAR(60), 
	es_menor BOOLEAN NOT NULL, 
	tutor_consent_at TIMESTAMP WITH TIME ZONE, 
	tutor_consent_por VARCHAR(200), 
	public_slug VARCHAR(64), 
	consent_publico_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (sis_id), 
	UNIQUE (public_slug)
);

CREATE TABLE rate_limit_hits (
	rl_key VARCHAR(200) NOT NULL, 
	bucket INTEGER NOT NULL, 
	count INTEGER DEFAULT '0' NOT NULL, 
	PRIMARY KEY (rl_key, bucket)
);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255), 
	oauth_provider VARCHAR(20), 
	oauth_sub VARCHAR(255), 
	role VARCHAR(20) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	persona_id INTEGER, 
	active BOOLEAN NOT NULL, 
	failed_logins INTEGER NOT NULL, 
	locked_until TIMESTAMP WITH TIME ZONE, 
	accepted_privacy_at TIMESTAMP WITH TIME ZONE, 
	accepted_tos_at TIMESTAMP WITH TIME ZONE, 
	legal_version VARCHAR(20), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	last_login TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_oauth_identity UNIQUE (oauth_provider, oauth_sub), 
	UNIQUE (email), 
	FOREIGN KEY(persona_id) REFERENCES personas (id) ON DELETE RESTRICT
);

CREATE TABLE arco_requests (
	id SERIAL NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	nombre VARCHAR(200) NOT NULL, 
	tipo VARCHAR(15) NOT NULL, 
	detalle TEXT NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	atendida_at TIMESTAMP WITH TIME ZONE, 
	atendida_por INTEGER, 
	respuesta TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(atendida_por) REFERENCES users (id)
);

CREATE TABLE cargos (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	concepto VARCHAR(30) NOT NULL, 
	descripcion VARCHAR(255) NOT NULL, 
	monto_centimos INTEGER NOT NULL, 
	moneda VARCHAR(3) NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	vence_at TIMESTAMP WITH TIME ZONE, 
	pagado_at TIMESTAMP WITH TIME ZONE, 
	referencia_pago VARCHAR(120), 
	origen_tipo VARCHAR(20), 
	origen_id VARCHAR(64), 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE membresias (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	tipo VARCHAR(30) NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	inicia_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	vence_at TIMESTAMP WITH TIME ZONE, 
	otorgada_por INTEGER, 
	notas TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_membresia_por_tipo UNIQUE (user_id, tipo), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(otorgada_por) REFERENCES users (id)
);

CREATE TABLE recursos (
	id SERIAL NOT NULL, 
	modulo VARCHAR(20) NOT NULL, 
	tipo VARCHAR(20) NOT NULL, 
	titulo VARCHAR(300) NOT NULL, 
	resumen TEXT NOT NULL, 
	autores VARCHAR(500) NOT NULL, 
	idioma VARCHAR(5) NOT NULL, 
	url VARCHAR(500) NOT NULL, 
	portada_url VARCHAR(500), 
	duracion_min INTEGER, 
	doi VARCHAR(120), 
	issn VARCHAR(20), 
	isbn VARCHAR(20), 
	volumen VARCHAR(20), 
	numero VARCHAR(20), 
	paginas VARCHAR(20), 
	licencia VARCHAR(60) NOT NULL, 
	palabras_clave VARCHAR(300) NOT NULL, 
	acceso VARCHAR(15) NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	publicado_at TIMESTAMP WITH TIME ZONE, 
	created_by INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (doi), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);

CREATE TABLE reservas (
	id SERIAL NOT NULL, 
	espacio_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	inicia_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	termina_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	motivo VARCHAR(255) NOT NULL, 
	estado VARCHAR(15) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(espacio_id) REFERENCES espacios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE RESTRICT
);

CREATE TABLE prestamos (
	id SERIAL NOT NULL, 
	item_id INTEGER NOT NULL, 
	persona_id INTEGER NOT NULL, 
	prestado_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	vence_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	devuelto_at TIMESTAMP WITH TIME ZONE, 
	renovaciones INTEGER NOT NULL, 
	atendido_por INTEGER NOT NULL, 
	cargo_id INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE RESTRICT, 
	FOREIGN KEY(persona_id) REFERENCES personas (id) ON DELETE RESTRICT, 
	FOREIGN KEY(atendido_por) REFERENCES users (id), 
	FOREIGN KEY(cargo_id) REFERENCES cargos (id)
);


-- ---------- Cierre del Data API ----------

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE audit_log FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE espacios ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE espacios FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE items ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE items FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE personas FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE rate_limit_hits ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE rate_limit_hits FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE users FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE arco_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE arco_requests FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE cargos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE cargos FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE membresias ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE membresias FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE recursos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE recursos FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE reservas ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE reservas FROM anon, authenticated;

-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia
-- autenticación. Estas tablas no deben ser alcanzables con la clave anon.
ALTER TABLE prestamos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE prestamos FROM anon, authenticated;


-- ---------- Bitácora append-only (Panorama Legal, Paso 6) ----------

CREATE OR REPLACE FUNCTION audit_log_immutable() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'audit_log es append-only'; END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_audit_no_update ON audit_log;
CREATE TRIGGER trg_audit_no_update BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION audit_log_immutable();
