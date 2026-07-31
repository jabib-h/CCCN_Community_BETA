# Migración del Badge System al Hub

El CCCN Badge System (`../CCCN_BadgeSystem/`) se absorbe como el módulo **Credenciales**
del Hub. Este documento es el plan; **todavía no se ejecutó**. `CCCN_BadgeSystem/` está
intacto y sigue funcionando por su cuenta.

## Por qué no se hizo de una vez

Es una mudanza mecánica de ~2.400 líneas ya probadas, pero toca dos contratos públicos
que no se pueden romper a ciegas:

1. **`did:web` depende del dominio.** La identidad del emisor se resuelve en
   `/.well-known/did.json` del host. Si las credenciales pasan de `badges.centrocultural.cr`
   a `community.centrocultural.cr`, las credenciales ya emitidas dejan de verificar.
2. **Las URLs públicas están citadas dentro de credenciales y documentos legales:**
   `/issuer.json`, `/b/{id}`, `/u/{slug}`, `/assertions/*`, `/credentials/*`, `/legal/*`.
   Son permanentes por contrato del estándar Open Badges.

Como el Badge System **aún no está desplegado en producción**, ninguna credencial real
depende todavía de esas URLs — que es justo lo que hace que este sea el mejor momento
para mudarlo. Pero la decisión de dominio hay que tomarla antes, no después.

## Prerrequisito: decidir el dominio

Dos opciones, ambas válidas:

- **A — El Hub sirve también `badges.centrocultural.cr`.** Se agrega el hostname a la
  misma App Service. Las URLs públicas de credenciales no cambian nunca. Es la opción
  segura y la recomendada.
- **B — Todo bajo `community.centrocultural.cr`.** Más simple de operar, pero el `did:web`
  y todas las URLs de identidad cambian. Solo viable mientras no haya credenciales
  emitidas en producción.

## Pasos

1. **Copiar los módulos de dominio** desde `CCCN_BadgeSystem/api/` sin cambios de lógica:
   `issuance.py`, `openbadges.py`, `vc.py`, `badge_render.py`, `notify.py`,
   `maintenance.py`, `users_cli.py` y los routers `public.py`, `student.py`, `admin.py`.
2. **Reponer en `api/security.py`** el bloque Ed25519 + base58/multibase + `hash_recipient_email`,
   copiado tal cual desde el Badge System (se omitió acá por no tener uso todavía).
3. **Fusionar el esquema** en `api/db.py`: agregar `badge_classes`, `assertions`,
   `import_batches`, `credential_log` y las columnas de reclamo.
4. **Renombrar la tabla de personas.** El Badge System usa `recipients`; el Hub usa
   `personas`. Renombrar en el código copiado (`recipients` → `personas`,
   `recipient_id` → `persona_id`), **excepto** en los payloads de Open Badges, donde
   `recipient` es un nombre del estándar y no se toca.
5. **Renombrar el prefijo de entorno** `BADGES_` → `HUB_` y consolidar en `.env.example`.
   `BADGES_SIGNING_KEY_PEM` → `HUB_SIGNING_KEY_PEM`.
6. **Montar los routers** en `api/main.py`, respetando el contrato de rutas: las URLs de
   identidad pública van **sin** versión (contrato del estándar) y la API de aplicación
   bajo `/api/v1`.
7. **Mover el frontend** de `CCCN_BadgeSystem/web/` a `web/badges/`, salvo `web/shared/`,
   que ya está acá y no debe duplicarse (regla de fuente única de marca).
8. **Reponer las dependencias** comentadas en `requirements.txt`: `cryptography` y
   `python-multipart`.
9. **Fusionar las pruebas**: llevar los casos de `CCCN_BadgeSystem/api/smoke_tests.py`
   a `api/smoke_tests.py`. La suite conjunta debe pasar completa antes de dar la
   migración por terminada.
10. **Cambiar el estado del módulo** `badges` a `"activo"` en `api/modules.py`.
11. **Unificar los documentos legales.** La política de privacidad del Hub ya cubre el
    alcance de credenciales; hay que retirar la del Badge System para que no queden dos
    versiones vigentes que digan cosas distintas.

## Verificación de que salió bien

```bash
python -m compileall -q api
python -m api.smoke_tests          # suite del Hub + casos del Badge System, todos en verde
```

Y a mano: emitir una credencial de prueba, verificarla por su enlace público, revocarla,
y confirmar que la cadena de integridad (`credential_log`) sigue encadenada.

## Qué hacer con el repositorio original

Una vez que la suite conjunta pase, `CCCN_BadgeSystem/` deja de ser fuente de verdad.
**No borrarlo sin autorización explícita**: conserva historia de git, CI y `CHANGELOG.md`
que documentan decisiones de diseño de las credenciales. Archivarlo en solo lectura.
