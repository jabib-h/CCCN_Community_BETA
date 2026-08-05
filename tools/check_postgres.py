"""Verifica una base Postgres ya migrada: esquema, cierre del Data API, bitácora
append-only y una ronda real de la app contra esas tablas.

`api/smoke_tests.py` corre siempre sobre SQLite temporal (fija HUB_DATABASE_URL al
importarse), así que no sirve para comprobar Postgres. Este script cubre ese hueco.

    # contra el Postgres local del CLI (npx supabase start)
    python -m tools.check_postgres

    # contra el proyecto remoto — usar la cadena DIRECTA (5432), no la del pooler
    python -m tools.check_postgres "postgresql+psycopg://postgres:...@db.<ref>.supabase.co:5432/postgres"

Escribe datos de prueba: NO apuntarlo a producción.
"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")  # consola Windows cp1252

LOCAL = "postgresql+psycopg://postgres:postgres@127.0.0.1:54322/postgres"

url = sys.argv[1] if len(sys.argv) > 1 else LOCAL
os.environ["HUB_DATABASE_URL"] = url
os.environ["HUB_ENV"] = "beta"          # el modo que corre en Vercel
os.environ.setdefault("HUB_JWT_SECRET", "prueba-local-no-secreta-jwt-0000000000")
os.environ.setdefault("HUB_SESSION_SECRET", "prueba-local-no-secreta-ses-0000000000")
os.environ.setdefault("HUB_BASE_URL", "http://testserver")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from api.db import engine, metadata  # noqa: E402
from api.main import app  # noqa: E402

_fails: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(f"[{'OK ' if cond else 'FAIL'}] {name}" + (f"  → {extra}" if not cond and extra else ""))
    if not cond:
        _fails.append(name)


def main() -> int:
    esperadas = len(metadata.tables)
    print(f"Base: {url.rsplit('@', 1)[-1]}\n")

    with engine.begin() as c:
        tablas = c.execute(text(
            "select count(*) from pg_tables where schemaname='public'")).scalar()
        sin_rls = c.execute(text(
            "select count(*) from pg_tables t where schemaname='public' and not ("
            " select relrowsecurity from pg_class c join pg_namespace n on n.oid=c.relnamespace"
            " where c.relname=t.tablename and n.nspname='public')")).scalar()
        permisos = c.execute(text(
            "select count(*) from information_schema.role_table_grants"
            " where table_schema='public' and grantee in ('anon','authenticated')")).scalar()
        trigger = c.execute(text(
            "select count(*) from pg_trigger where tgrelid='audit_log'::regclass"
            " and not tgisinternal")).scalar()

    check(f"están las {esperadas} tablas del esquema", tablas == esperadas, f"hay {tablas}")
    check("todas con RLS habilitado", sin_rls == 0, f"{sin_rls} sin RLS")
    check("anon/authenticated sin permisos (Data API cerrado)", permisos == 0,
          f"{permisos} permisos otorgados")
    check("trigger append-only en audit_log", trigger >= 1)

    # La app no debe tocar el esquema al arrancar fuera de dev: eso lo hacen las migraciones.
    with TestClient(app) as client:
        with engine.begin() as c:
            tras = c.execute(text(
                "select count(*) from pg_tables where schemaname='public'")).scalar()
        check("el arranque de la app no crea ni altera tablas", tras == tablas)

        r = client.get("/health")
        check("/health responde", r.status_code == 200 and r.json()["env"] == "beta", r.text[:120])

        email = f"check.postgres.{os.getpid()}@centrocultural.cr"
        pwd = "Contrasena-Larga-De-Prueba-123"
        r = client.post("/api/v1/auth/register", json={
            "email": email, "password": pwd, "nombre": "Check Postgres",
            "fecha_nacimiento": "1990-05-14", "accept_privacy": True, "accept_tos": True})
        check("registro contra el esquema migrado", r.status_code == 201, r.text[:160])
        token = r.json().get("token", "") if r.status_code == 201 else ""

        r = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
        check("login", r.status_code == 200, r.text[:160])

        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        check("el JWT sirve en /auth/me", r.status_code == 200, r.text[:160])

    # La bitácora debe ser inmutable EN LA BASE, no solo por convención de la app.
    with engine.begin() as c:
        antes = c.execute(text("select count(*) from audit_log")).scalar()
    check("la actividad quedó registrada en la bitácora", antes >= 2, f"{antes} filas")

    for verbo, sql in (("UPDATE", "update audit_log set accion='alterado'"),
                       ("DELETE", "delete from audit_log")):
        try:
            with engine.begin() as c:
                c.execute(text(sql))
            check(f"{verbo} a la bitácora bloqueado", False, "pasó — la bitácora es alterable")
        except Exception as exc:
            check(f"{verbo} a la bitácora bloqueado", "append-only" in str(exc), str(exc)[:120])

    with engine.begin() as c:
        despues = c.execute(text("select count(*) from audit_log")).scalar()
    check("la bitácora conserva sus filas", despues == antes, f"{antes} → {despues}")

    print()
    if _fails:
        print(f"FALLARON {len(_fails)}: {', '.join(_fails)}")
        return 1
    print("Postgres verificado: esquema, Data API cerrado y bitácora inmutable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
