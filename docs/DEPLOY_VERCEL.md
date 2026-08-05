# Desplegar BETA en Vercel + Supabase

Proyecto de Supabase: `gswghemqsdsmkcocajrh`.

El CLI de Supabase se usa con `npx` — no hace falta instalarlo:

```bash
npx supabase@latest <comando>
```

## 1. Supabase (base de datos)

1. Proyecto ya creado. Región: la más cercana a Costa Rica (`us-east-1`).
2. **Database → Connection string → Connection pooling** (modo *Transaction*, puerto
   `6543`). Cada invocación serverless de Vercel abre su propia conexión — el pooler
   evita agotar las conexiones directas de Postgres. **No usar** la cadena de conexión
   directa (puerto 5432) para `HUB_DATABASE_URL`.
3. **Project Settings → Database → SSL**: dejar `sslmode=require` (ya viene en la cadena
   de conexión de Supabase).

### 1.1 Aplicar el esquema (migraciones)

El esquema **ya no lo crea la app**. `api/main.py` solo corre `init_db()` en `dev`
(SQLite); en beta y producción las tablas las aplican las migraciones de
`supabase/migrations/`. El motivo está comentado en `api/main.py`: en Vercel cada
arranque en frío es un proceso nuevo, y dos arranques simultáneos recrearían a la vez el
trigger append-only de `audit_log`, dejando una ventana sin esa garantía.

Comandos (interactivos — piden token del navegador y la contraseña de la base):

```bash
npx supabase@latest login
npx supabase@latest link --project-ref gswghemqsdsmkcocajrh
npx supabase@latest db push          # aplica supabase/migrations/ al proyecto remoto
```

Verificar que quedó aplicado:

```bash
npx supabase@latest migration list   # local y remoto deben coincidir
```

### 1.2 El Data API queda cerrado a propósito

El Hub **no usa** el Data API (PostgREST) de Supabase: habla Postgres directo con su
propia autenticación. La migración inicial habilita RLS y revoca permisos a `anon` y
`authenticated` en todas las tablas.

No es opcional ni cosmético: la clave `anon` de Supabase es pública y viaja en cualquier
navegador. Sin ese cierre, `GET /rest/v1/users` devolvería los hashes de contraseña a
cualquiera. La app se conecta como dueña de las tablas, así que RLS no la afecta
(Postgres no aplica RLS al owner salvo `FORCE`).

Al agregar una tabla nueva hay que repetir las dos líneas en su migración — el script
`tools/schema_sql.py` ya las genera para todas.

## 2. Vercel (hosting)

1. [vercel.com/new](https://vercel.com/new) → importar el repo
   `jabib-h/CCCN_Community_BETA`. Vercel detecta `vercel.json` automáticamente
   (framework preset: Other).
2. **Project Settings → Environment Variables** — agregar (Production **y** Preview):

   | Variable | Valor |
   |---|---|
   | `HUB_ENV` | `beta` |
   | `HUB_BASE_URL` | `https://<dominio-del-proyecto>.vercel.app` (actualizar tras el primer deploy) |
   | `HUB_DATABASE_URL` | cadena del pooler de Supabase (paso 1.2), con `+psycopg` en el esquema: `postgresql+psycopg://...` |
   | `HUB_JWT_SECRET` | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `HUB_SESSION_SECRET` | ídem, un valor **distinto** al de `HUB_JWT_SECRET` |
   | `HUB_MAIL_FROM`, `HUB_CONTACTO_DATOS` | según `.env.example` |
   | OAuth (`HUB_GOOGLE_*`, `HUB_MS_*`) | opcional; vacío = proveedor deshabilitado |

   Nunca pegar estos valores en el repo ni en el chat: se generan y se cargan
   directamente en el formulario de Vercel.
3. Deploy. Verificar `https://<proyecto>.vercel.app/health` → `{"status":"ok","env":"beta"}`.
4. (Opcional) **Project Settings → Domains** para apuntar un subdominio propio de prueba,
   p. ej. `beta.centrocultural.cr`, si se quiere probar con dominio real antes de promover
   a producción.

## 3. Verificación post-deploy

- `/health` responde `env: beta`.
- `/app/` sirve el frontend (mount de `web/` vía `StaticFiles`).
- Crear una cuenta de prueba y confirmar que un segundo request (segundo cold start)
  todavía reconoce el JWT emitido — si falla, `HUB_JWT_SECRET` no quedó fijo en Vercel
  (ver `config.py`: fuera de `dev`, el secreto **debe** venir del entorno).
- Verificar la base migrada (esquema, Data API cerrado, bitácora inmutable) con la
  cadena **directa** (5432), no la del pooler:

  ```bash
  python -m tools.check_postgres "postgresql+psycopg://postgres:...@db.gswghemqsdsmkcocajrh.supabase.co:5432/postgres"
  ```

  Escribe una cuenta de prueba y filas de bitácora: correrlo contra beta, nunca contra
  producción. (`python -m api.smoke_tests` **no** sirve para esto: fija `HUB_DATABASE_URL`
  a un SQLite temporal al importarse, así que nunca toca Postgres.)

## 4. Promoción a producción

BETA y PRODUCTION son repos independientes a propósito (revisión explícita antes de
tocar el dominio público). Cuando un cambio se valida en beta:

```bash
# Desde un checkout de PRODUCTION
git remote add beta https://github.com/jabib-h/CCCN_Community_BETA.git
git fetch beta main
git merge beta/main        # o cherry-pick los commits ya probados
git push origin main
```

No hay automatización de esta promoción todavía — es deliberado: cada paso a producción
pasa por una revisión humana. Ver `docs/DEPLOY_AZURE.md` (repo PRODUCTION) para el
despliegue en Azure.
