"""Catálogo de módulos del Hub y su regla de acceso.

Es un diccionario en código, no una tabla: agregar un módulo implica de todos modos
escribir su router y sus páginas, así que la fuente de verdad vive junto al código que
lo implementa. `ponytail:` si algún día un administrador debe poder crear módulos sin
desplegar, esto pasa a tabla — hoy sería una pantalla de configuración sin usuarios.

`requiere_membresia`: tipo de membresía activa necesaria para ENTRAR al módulo.
Las reglas finas (este artículo es público, este ejemplar no se presta) viven en el
módulo, sobre la columna `acceso` del recurso.
"""

MODULOS = [
    {
        "slug": "cop",
        "nombre": "Community of Practice",
        "descripcion": "Charlas, vlogs, conferencias y talleres de la comunidad docente.",
        "href": "/app/cop.html",
        "externo": False,
        "requiere_membresia": None,
        "estado": "en_construccion",
    },
    {
        "slug": "revista",
        "nombre": "Revista Académica",
        "descripcion": "Publicación indexada sobre enseñanza del inglés: artículos, blogs y podcast.",
        "href": "/app/revista.html",
        "externo": False,
        "requiere_membresia": None,
        "estado": "en_construccion",
    },
    {
        "slug": "libros",
        "nombre": "Biblioteca Digital",
        "descripcion": "Catálogo de libros electrónicos y audiolibros en OverDrive.",
        "href": None,  # se resuelve a config.OVERDRIVE_URL
        "externo": True,
        "requiere_membresia": "biblioteca",
        "estado": "activo",
    },
    {
        "slug": "badges",
        "nombre": "Credenciales e Insignias",
        "descripcion": "Emisión y verificación de credenciales digitales Open Badges.",
        "href": "/app/badges/",
        "externo": False,
        "requiere_membresia": None,
        "estado": "en_construccion",  # → activo al completar docs/MIGRACION_BADGES.md
    },
    {
        "slug": "biblioteca",
        "nombre": "Biblioteca y Espacios",
        "descripcion": "Acervo físico, préstamos y reserva de salas.",
        "href": "/app/biblioteca.html",
        "externo": False,
        "requiere_membresia": None,
        "estado": "en_construccion",
    },
]

BY_SLUG = {m["slug"]: m for m in MODULOS}


def puede_entrar(modulo: dict, role: str, membresias_activas: set[str]) -> bool:
    """El personal y la administración entran a todo; el resto necesita la membresía
    que el módulo exija. Se evalúa SIEMPRE en el servidor con datos del JWT + BD."""
    if role in ("staff", "admin"):
        return True
    requerida = modulo["requiere_membresia"]
    return requerida is None or requerida in membresias_activas
