# Arquitectura del CCCN Hub

Las decisiones tomadas, con su razón. Si una decisión cambia, se edita acá **antes** de
tocar el código.

---

## 1. Un monolito modular, no microservicios

**Decisión:** un solo proceso FastAPI, una sola base de datos, un solo despliegue.
Cada servicio (comunidad de práctica, revista, biblioteca, credenciales) es un *router*
y un conjunto de tablas dentro de la misma aplicación.

**Por qué:** el requisito central del Hub es *unificar usuarios y bases*. Cinco servicios
separados implican cinco tablas de usuarios, cinco sesiones y una capa de sincronización
que mantener — exactamente el problema que el Hub existe para eliminar. Un monolito con
módulos da la unificación gratis: un `JOIN` en vez de una llamada HTTP entre servicios.

**Cuándo revisar:** si un módulo necesita escalar o desplegarse por separado (por ejemplo,
transcodificación de video en la comunidad de práctica), ese módulo sale a su propio
servicio *consumiendo* la identidad del Hub, no duplicándola.

---

## 2. La base heredada del Badge System

El CCCN Badge System ya resolvió, probó y documentó: identidad con OAuth, RBAC desde JWT,
consentimiento informado de la Ley 8968, gates de minoridad, bitácora append-only forzada
por triggers, canal ARCO, cabeceras de seguridad sin `unsafe-inline` y un design system
de marca con tipografía autoalojada.

El Hub **reutiliza esa base** (`config.py`, `security.py`, `auth.py`, el núcleo de `db.py`,
el flujo de autenticación y `web/shared/ds/`) en lugar de reescribirla. Lo que **no** se
copió todavía es el producto Badges en sí (emisión, Open Badges, VC, firma Ed25519):
eso entra con la migración descrita en [docs/MIGRACION_BADGES.md](docs/MIGRACION_BADGES.md).

`CCCN_BadgeSystem/` **no fue modificado**. Sigue siendo un repositorio funcional e
independiente hasta que se ejecute esa migración.

---

## 3. Identidad: `personas` y `users` son cosas distintas

- **`personas`** — la persona física. Existe aunque nunca abra una cuenta: a una persona
  se le presta un libro y se le emite una credencial. Se identifica por `sis_id`
  (estudiantes y personal, el mismo de Canvas/AIH) o por cédula (externos).
- **`users`** — la credencial de acceso al Hub. Puede no existir; puede vincularse a una
  persona después (`users.persona_id`).

Separarlos es lo que permite operar la biblioteca con quien no tiene cuenta y, más tarde,
vincular su historial cuando la abra. En el Badge System esta tabla se llama `recipients`;
al migrar se renombra a `personas` (ver la guía de migración).

---

## 4. Permisos: rol + membresía, evaluados en el servidor

Tres roles: `user`, `staff`, `admin`. Las **membresías** (`membresias`) son las que
habilitan módulos; el catálogo y su regla de acceso viven en [api/modules.py](api/modules.py).

Dos reglas que no se negocian:

1. **El rol y el alcance salen del servidor**, nunca del body ni del query string
   (Panorama Legal, Paso 4). El rol se relee de la base en cada petición, para que
   revocarlo no espere a que expire el JWT.
2. **Ocultar una tarjeta en el navegador no es control de acceso.** La puerta real es
   `require_modulo()` en cada router. El frontend solo dibuja lo que el servidor ya filtró.

---

## 5. Contenido: una sola tabla

Charlas, talleres, vlogs, artículos, blogs y podcast son el mismo objeto: metadatos, un
enlace y una regla de acceso. Viven en `recursos`, distinguidos por `modulo` y `tipo`.
Cinco tablas casi idénticas serían cinco veces el mismo CRUD.

Si la revista incorpora revisión por pares, eso es una tabla nueva (`revisiones`) que
apunta a `recursos` — no una segunda tabla de contenido.

**Nota sobre identificadores:** una revista se identifica con **ISSN**, cada artículo con
**DOI**. El ISBN identifica libros y monografías. El esquema tiene las tres columnas
porque el CCCN publica los tres tipos de material, pero conviene decidir con la persona
encargada editorial cuál corresponde a cada publicación antes de indexar.

---

## 6. Dinero: enteros, y por ahora solo el libro mayor

Los montos se guardan en **céntimos, como enteros** (`monto_centimos`). SQLite degrada
`Numeric` a punto flotante y la aritmética de cobros no admite error de redondeo.

La tabla `cargos` registra lo que se **debe**, no procesa pagos. La integración con una
pasarela (Tilopay, Greenpay, BAC o Stripe) es una decisión abierta con implicaciones
legales y de conciliación contable, y no se toma dentro del código: ver
[§ Decisiones abiertas](#8-decisiones-abiertas).

Lo que sí queda escrito, para cuando esa decisión se tome (Panorama Legal §3.5):
el conteo y la acumulación se hacen **en el servidor**, nunca en el cliente; cada
petición de cobro lleva una llave de idempotencia para que un reintento de red no
facture dos veces; y el saldo se lee de la tabla local sincronizada por webhook firmado,
no consultando la pasarela en cada render.

---

## 7. OverDrive no se hospeda: se enlaza

`centrocultural.overdrive.com` es un servicio operado por un tercero. El Hub **no puede**
alojarlo; lo que hace es controlar quién llega a él: la tarjeta solo entrega la URL a
quien tenga membresía de biblioteca vigente, y el enlace se abre con
`rel="noopener noreferrer"`.

El inicio de sesión único hacia OverDrive (SIP2 o SAML contra su consola de biblioteca)
es una gestión con el proveedor, no una tarea de código. Mientras no exista, la persona
usuaria autentica dos veces.

---

## 9. Dos repos, dos entornos: BETA (Vercel+Supabase) y PRODUCTION (Azure)

**Decisión:** el mismo código (este monolito) se despliega en dos repositorios
independientes, no en dos ramas de uno solo:

- **BETA** — `github.com/jabib-h/CCCN_Community_BETA`, desplegado en Vercel
  (`HUB_ENV=beta`), base de datos Postgres en Supabase. Sirve para probar módulos y
  cambios antes de exponerlos al dominio público. Ver `docs/DEPLOY_VERCEL.md`.
- **PRODUCTION** — `github.com/jabib-h/CCCN_Community_PRODUCTION`, desplegado en Azure
  App Service (`HUB_ENV=production`) en `community.centrocultural.cr`, siguiendo las
  mismas convenciones de despliegue que `A - API/NCTE` (GitHub Actions, cabeceras de
  seguridad, dominio gestionado en Azure). Base de datos Postgres en Azure (Flexible
  Server o el que se decida — ver tabla de abajo). Ver `docs/DEPLOY_AZURE.md` en ese
  repo.

**Por qué repos separados y no una rama `beta`:** promover un cambio a producción es un
`git merge`/`cherry-pick` explícito entre remotos (ver `docs/DEPLOY_VERCEL.md §4`), nunca
un push directo. La separación física de repos hace ese paso visible y deliberado en vez
de depender de disciplina de branching.

**Por qué `IS_PROD` ahora es `ENV != "dev"` (no `ENV == "production"`):** tanto beta
(Vercel) como producción (Azure) corren en filesystem efímero o multi-instancia — ninguno
puede persistir un secreto autogenerado en disco entre invocaciones. Solo el modo `dev`
local puede darse ese lujo. El *rate limiter* pasó de memoria por proceso a una tabla en
Postgres (`rate_limit_hits`, ventana fija de 60s) por la misma razón.

---

## 8. Decisiones abiertas

Ninguna bloquea el desarrollo actual, pero todas cambian código cuando se resuelvan:

| Decisión | Por qué importa | Quién decide |
|---|---|---|
| Pasarela de pago | Define el modelo de `cargos`, el flujo de conciliación y los Términos §12 | Dirección + Contabilidad |
| ISSN de la revista y registro DOI (Crossref/DataCite) | Sin ellos la revista no es indexable | Encargatura editorial |
| Inscripción de la base ante PRODHAB | Exenta si el uso es interno; obligatoria si hay difusión o comercialización de datos (canon anual de $200) | Asesoría legal |
| Aprobación de los documentos legales | Hoy están marcados **BORRADOR**; el consentimiento se recoge contra ellos | Dirección + asesoría legal |
| Migración del Badge System | Hasta que ocurra, credenciales vive en su propio repositorio | Técnica |
| Postgres de producción | Azure Flexible Server vs. reusar Supabase también en prod — "por definir" | Técnica |
| Relación con `badges.centrocultural.cr` | El `did:web` de las credenciales depende de en qué dominio termine viviendo Badges tras su migración | Técnica + Dirección |
