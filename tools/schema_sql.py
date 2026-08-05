"""Emite el DDL de Postgres del esquema declarado en api/db.py.

`api/db.py` es la ÚNICA fuente de verdad del esquema. Este script no la duplica: la
compila al dialecto de Postgres para que la migración de Supabase sea un artefacto
derivado y no una segunda definición escrita a mano (que se desincronizaría sola).

Uso:
    python -m tools.schema_sql                 # imprime el DDL completo
    python -m tools.schema_sql --tables-only   # solo CREATE TABLE, sin triggers ni RLS

Al cambiar el esquema NO alcanza con reejecutarlo: esto genera la creación desde cero,
no el ALTER. Para un cambio sobre una base que ya existe hay que escribir la migración
incremental a mano y usar esta salida solo como referencia de cómo debe quedar.
"""
import argparse

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from api import db

# Sin políticas: nadie pasa. La app se conecta como dueña de las tablas y las salta
# (Postgres no aplica RLS al owner salvo FORCE), pero los roles del Data API de Supabase
# — anon y authenticated, alcanzables con la clave pública desde cualquier navegador —
# quedan bloqueados. Sin esto, GET /rest/v1/users devolvería los hashes de contraseña.
_HARDENING = (
    "ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\n"
    "REVOKE ALL ON TABLE {table} FROM anon, authenticated;"
)


def build(tables_only: bool = False) -> str:
    dialect = postgresql.dialect()
    out = []

    for table in db.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect)).strip()
        out.append(f"{ddl};")

    if tables_only:
        return "\n\n".join(out) + "\n"

    out.append(
        "\n-- ---------- Cierre del Data API ----------\n"
        "-- El Hub no usa el Data API de Supabase: habla Postgres directo con su propia\n"
        "-- autenticación. Estas tablas no deben ser alcanzables con la clave anon."
    )
    out.append("\n".join(_HARDENING.format(table=t.name) for t in db.metadata.sorted_tables))

    out.append("\n-- ---------- Bitácora append-only (Panorama Legal, Paso 6) ----------")
    out.append(db._AUDIT_TRIGGERS_PG.strip())

    return "\n\n".join(out) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tables-only", action="store_true")
    print(build(tables_only=parser.parse_args().tables_only))
