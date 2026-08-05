# CLAUDE.md — Reglas de desarrollo · CCCN Hub

## Arranque de sesión
1. Leé `README.md` (qué es) y `ARQUITECTURA.md` (por qué es así).
2. `python -m api.smoke_tests` debe pasar ANTES y DESPUÉS de tus cambios.
3. Si cambiás una decisión de diseño, actualizá `ARQUITECTURA.md` en el mismo cambio.

## Reglas duras

**Seguridad** (Panorama Legal + Project Guard):
- Consultas SOLO parametrizadas (SQLAlchemy Core). Cero SQL concatenado.
- Rol, identidad y alcance SOLO del servidor (`api/auth.py`); jamás del body o del query.
  Ocultar algo en el navegador no es control de acceso.
- Secretos SOLO por entorno. Si agregás uno: `api/config.py` (falla en prod si falta) + `.env.example`.
- `audit()` dentro de la MISMA transacción de toda acción que modifique estado.
- **Nunca escribas y después lances una excepción dentro de `engine.begin()`:** el
  `raise` hace rollback y la escritura se pierde en silencio. Confirmá primero, lanzá
  después (ver el contador de intentos fallidos en `routers/auth_routes.py`).
- PII nunca en superficies públicas. Menores: todo flujo nuevo respeta los gates de tutor.
- Escape de HTML en todo lo que venga de la base (`ui.esc` en el frontend).

**Esquema y base de datos:**
- `api/db.py` es la ÚNICA fuente de verdad del esquema. Las migraciones de
  `supabase/migrations/` son un artefacto derivado (`python -m tools.schema_sql`).
- Un cambio de esquema son DOS cosas en el mismo commit: editar `api/db.py` **y** agregar
  una migración incremental nueva. No se regenera la migración inicial — ya está aplicada
  en bases reales. `schema_sql.py` solo sirve de referencia de cómo debe quedar.
- **Toda tabla nueva necesita, en su migración**, las dos líneas que la cierran al Data API:
  `ALTER TABLE x ENABLE ROW LEVEL SECURITY;` y `REVOKE ALL ON TABLE x FROM anon, authenticated;`
  La clave `anon` de Supabase es pública; sin eso la tabla queda legible desde cualquier
  navegador. La app se conecta como dueña y RLS no la afecta.
- La app NO crea el esquema fuera de `dev`: `init_db()` solo corre si `not IS_PROD`
  (ver el comentario en `api/main.py` — en serverless recrearía el trigger de la bitácora
  en cada arranque en frío).

**Frontend:**
- La CSP no permite `unsafe-inline`: cero `<style>`, cero `style=""`, cero `<script>` embebido.
  Si necesitás un color dinámico, aplicalo por CSSOM desde un `.js`, no por atributo.
- La CSP tampoco permite `font-src` externo: **no enlaces Google Fonts**. La tipografía
  está autoalojada en `web/shared/ds/assets/fonts/`.
- `web/shared/ds/` es la ÚNICA copia del design system y de la marca. No dupliques
  tokens, logos ni tipografías en otra carpeta.
- Sin build, sin framework, sin dependencias de CDN. Vanilla servido por la API.

**Base de datos:**
- El esquema corre en Postgres Y SQLite. Nada específico de un dialecto fuera de los
  bloques ya marcados en `db.py`.
- Dinero en enteros (céntimos). Nunca float, nunca `Numeric`.
- Una sola base para todos los módulos. Si creés que un módulo necesita la suya,
  discutilo antes de escribirla — es lo que el Hub existe para evitar.

**Legal:**
- Los documentos de `web/legal/` mantienen la marca BORRADOR hasta aprobación formal
  de Dirección.
- Si agregás un tratamiento de datos nuevo (un dato que antes no se recogía, una
  finalidad nueva), **actualizá la Política de Privacidad en el mismo cambio**: el
  consentimiento se recoge contra ese texto y una finalidad no declarada es una falta
  grave ante PRODHAB.

## Antes de agregar un módulo

1. Entrada en `api/modules.py` (slug, nombre, membresía requerida, estado).
2. Router en `api/routers/`, con `Depends(require_modulo("<slug>"))` en cada endpoint.
3. Tablas en `api/db.py`, reusando `personas` y `users` — nunca una tabla de usuarios propia.
4. Color de la barra en `web/shared/hub.css` (`.mod__bar--<slug>`).
5. Casos en `api/smoke_tests.py`: al menos que el módulo se niegue sin la membresía.

## Verificación

```bash
python -m compileall -q api      # sintaxis
python -m api.smoke_tests        # regresión completa (SQLite temporal)
```

Si tocaste el esquema, la base o algo específico de Postgres, `smoke_tests` **no alcanza**:
corre siempre sobre SQLite y no ve los triggers, RLS ni permisos reales. Levantá el
Postgres del CLI y verificá contra él:

```bash
npx supabase@latest start -x studio,inbucket,mailpit,imgproxy,edge-runtime,logflare,vector,supavisor,realtime,storage-api,pg-meta
python -m tools.check_postgres   # esquema + Data API cerrado + bitácora inmutable
npx supabase@latest stop
```

## Convenciones
- Español en docs, UI y mensajes de error; identificadores en el idioma que ya use el módulo.
- Errores HTTP: útiles para quien los lee, sin filtrar detalles internos. En autenticación,
  genéricos (nunca distinguir "no existe" de "clave incorrecta").
- Marcá las simplificaciones deliberadas con un comentario `ponytail:` que nombre el techo
  de la solución y su camino de mejora.
