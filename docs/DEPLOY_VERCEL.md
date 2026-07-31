# Desplegar BETA en Vercel + Supabase

Pasos manuales (una sola vez). Requieren acceso a los dashboards de Vercel y Supabase —
no hay CLI de ninguno de los dos instalada en este entorno de desarrollo.

## 1. Supabase (base de datos)

1. Crear proyecto en [supabase.com](https://supabase.com/dashboard) → región más cercana
   a Costa Rica (`us-east-1` es la más cercana disponible).
2. **Database → Connection string → Connection pooling** (modo *Transaction*, puerto
   `6543`). Cada invocación serverless de Vercel abre su propia conexión — el pooler
   evita agotar las conexiones directas de Postgres. **No usar** la cadena de conexión
   directa (puerto 5432) para `HUB_DATABASE_URL`.
3. Guardar esa cadena para el paso 3. El esquema (tablas, triggers append-only) lo crea
   la app sola en el primer arranque (`init_db()` en `api/main.py`) — no hace falta correr
   SQL a mano en Supabase.
4. **Project Settings → Database → SSL**: dejar `sslmode=require` (ya viene en la cadena
   de conexión de Supabase).

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
- `python -m api.smoke_tests` localmente con `HUB_DATABASE_URL` apuntando al mismo
  Supabase (usar la cadena directa, no el pooler, para pruebas puntuales) antes de cada
  promoción a producción.

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
