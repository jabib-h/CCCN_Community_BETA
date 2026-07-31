# CCCN Hub

Plataforma única del Centro Cultural Costarricense Norteamericano. Reúne bajo una sola
cuenta, una sola base de datos y un solo control de permisos:

| Módulo | Qué es | Estado |
|---|---|---|
| **Community of Practice** | Charlas, vlogs, conferencias y talleres de la comunidad docente | En construcción |
| **Revista Académica** | Publicación indexada sobre enseñanza del inglés: artículos, blogs, podcast | En construcción |
| **Biblioteca Digital** | Catálogo de libros y audiolibros en OverDrive | Activo (enlace controlado por membresía) |
| **Credenciales e Insignias** | Open Badges firmados y verificables | En construcción — ver [migración](docs/MIGRACION_BADGES.md) |
| **Biblioteca y Espacios** | Acervo físico, préstamos y reserva de salas | En construcción |

Lo transversal —identidad, membresías, permisos, cobros y auditoría— ya funciona y es
lo que cada módulo nuevo hereda sin volver a resolverlo.

## Correr en local

```bash
pip install -r requirements.txt
python run.py                    # http://localhost:8700
```

Sin configuración, arranca con SQLite en `data/hub_dev.db` y genera sus secretos en
`data/state/` (ambos ignorados por git). Para configurar algo, copiá `.env.example` a
`.env`.

Crear la primera cuenta administradora:

```bash
python -c "
from api.db import engine, users, utcnow, init_db
from api.security import hash_password
init_db()
now = utcnow()
with engine.begin() as c:
    c.execute(users.insert().values(
        email='admin@centrocultural.cr', password_hash=hash_password('CAMBIAR-ESTA-CLAVE'),
        role='admin', display_name='Administración', active=True, created_at=now,
        accepted_privacy_at=now, accepted_tos_at=now, legal_version='staff'))
print('listo')"
```

## Verificar

```bash
python -m compileall -q api      # sintaxis
python -m api.smoke_tests        # 29 pruebas de regresión (SQLite temporal, no toca la BD real)
```

## Estructura

```
CCCN_HUB/
├── run.py                  Entrada de desarrollo
├── ARQUITECTURA.md         Las decisiones y su razón — leer antes de cambiar diseño
├── CLAUDE.md               Reglas de desarrollo — leer antes de tocar código
├── .env.example            Todas las variables de entorno documentadas
│
├── api/                    BACKEND — solo Python, cero assets
│   ├── main.py             App, cabeceras de seguridad, montaje de web/
│   ├── config.py           Entorno; en producción falla si falta un secreto
│   ├── db.py               Esquema único + triggers append-only
│   ├── security.py         Argon2 · JWT · rate limiter
│   ├── auth.py             RBAC y acceso por módulo (rol SOLO del servidor)
│   ├── modules.py          Catálogo de módulos y su regla de acceso
│   ├── smoke_tests.py      Regresión (python -m api.smoke_tests)
│   └── routers/            auth_routes · hub
│
├── web/                    FRONTEND — vanilla, sin build, servido por la API en /app
│   ├── index.html          Landing pública
│   ├── acceso.html         Ingreso y registro con consentimiento informado
│   ├── hub.html            Portada autenticada
│   ├── legal/              privacidad · terminos · cookies · arco  (BORRADOR)
│   └── shared/             FUENTE ÚNICA DE MARCA: ds/ (tokens + Raleway autoalojada),
│                           img/, api.js, ui.js, app.css, hub.css, public.css
│
├── docs/                   MIGRACION_BADGES.md
└── data/     ⊘ gitignored  BD de desarrollo, secretos locales
```

## Cumplimiento

Construido contra `../Panorama Legal/manual-cumplimiento-regulatorio.md` (Ley N.º 8968,
PRODHAB) y las prácticas de `../Project Guard/`. Lo que ya está aplicado y verificado
por las pruebas:

- Consentimiento expreso y no preseleccionado antes de crear la cuenta (art. 5).
- Autorregistro de personas menores de edad bloqueado (art. 196 bis Código Penal).
- Bitácora `audit_log` append-only forzada por *triggers* de base de datos.
- Canal ARCO público (no exige tener cuenta para ejercer un derecho).
- Rol y alcance resueltos siempre en el servidor; nunca desde el cliente.
- Consultas exclusivamente parametrizadas (SQLAlchemy Core).
- CSP estricta sin `unsafe-inline`, HSTS en producción, secretos solo por entorno.
- Errores de autenticación genéricos y bloqueo temporal tras 5 intentos fallidos.

**Los documentos de `web/legal/` están marcados BORRADOR** y deben ser aprobados por la
Dirección y la asesoría legal antes de salir a producción: el consentimiento se recoge
contra ellos.
