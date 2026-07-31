"""Smoke tests de regresión del Hub: headers, consentimiento, menores, bloqueo por
intentos fallidos, RBAC por módulo/membresía, cobros y bitácora append-only.

  python -m api.smoke_tests        (usa SQLite temporal — no toca ninguna BD real)
"""
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding="utf-8")  # consola Windows cp1252

_tmpdir = tempfile.mkdtemp(prefix="hub_smoke_")
os.environ["HUB_DATABASE_URL"] = f"sqlite:///{_tmpdir}/smoke.db"
os.environ["HUB_ENV"] = "dev"
# El limitador por IP se prueba aparte (ver más abajo); acá estorbaría a las demás pruebas,
# que hacen muchas más llamadas por minuto de las que haría una persona.
os.environ["HUB_RATE_LIMIT_AUTH"] = "500"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select, text, update  # noqa: E402

from .db import audit_log, cargos, engine, init_db, membresias, users, utcnow  # noqa: E402
from .main import app  # noqa: E402
from .security import RateLimiter, hash_password  # noqa: E402

PASSED = 0


def check(name: str, cond: bool, extra: str = ""):
    global PASSED
    print(f"[{'OK ' if cond else 'FAIL'}] {name}{(' — ' + extra) if extra and not cond else ''}")
    if not cond:
        sys.exit(1)
    PASSED += 1


def run():
    init_db()
    client = TestClient(app)
    now = utcnow()

    with engine.begin() as conn:
        conn.execute(users.insert().values(
            email="admin@centrocultural.cr", password_hash=hash_password("AdminSegura123!"),
            role="admin", display_name="Admin Prueba", active=True, created_at=now,
            accepted_privacy_at=now, accepted_tos_at=now, legal_version="staff"))

    # ---- Cabeceras de seguridad ----
    r = client.get("/health")
    check("health responde", r.status_code == 200)
    csp = r.headers.get("content-security-policy", "")
    check("CSP presente y sin unsafe-inline", csp and "unsafe-inline" not in csp)
    check("nosniff", r.headers.get("x-content-type-options") == "nosniff")
    check("frame-ancestors none", "frame-ancestors 'none'" in csp)

    # ---- Registro: consentimiento expreso obligatorio (Ley 8968 art. 5) ----
    base = {"email": "docente@example.com", "password": "ClaveLarga123!",
            "nombre": "Ana Docente", "fecha_nacimiento": "1990-05-01"}
    r = client.post("/api/v1/auth/register", json={**base, "accept_privacy": False, "accept_tos": True})
    check("registro sin consentimiento se rechaza", r.status_code == 422)

    r = client.post("/api/v1/auth/register",
                    json={**base, "email": "menor@example.com", "fecha_nacimiento": "2015-01-01",
                          "accept_privacy": True, "accept_tos": True})
    check("autorregistro de menor bloqueado", r.status_code == 403)

    r = client.post("/api/v1/auth/register", json={**base, "accept_privacy": True, "accept_tos": True})
    check("registro válido", r.status_code == 201, r.text)
    token = r.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    r = client.post("/api/v1/auth/register", json={**base, "accept_privacy": True, "accept_tos": True})
    check("correo duplicado se rechaza", r.status_code == 409)

    # ---- Login: mensaje genérico y bloqueo por intentos ----
    r = client.post("/api/v1/auth/login", json={"email": "nadie@example.com", "password": "x"})
    r2 = client.post("/api/v1/auth/login", json={"email": "docente@example.com", "password": "mala"})
    check("auth no distingue usuario inexistente de clave errónea",
          r.status_code == 401 and r.json()["detail"] == r2.json()["detail"])

    for _ in range(4):
        client.post("/api/v1/auth/login", json={"email": "docente@example.com", "password": "mala"})
    r = client.post("/api/v1/auth/login", json={"email": "docente@example.com", "password": "ClaveLarga123!"})
    check("cuenta se bloquea tras 5 fallos", r.status_code == 423, r.text)
    with engine.begin() as conn:  # desbloquear para el resto de las pruebas
        conn.execute(update(users).where(users.c.email == "docente@example.com")
                     .values(locked_until=None, failed_logins=0))

    # ---- Portada: requiere autenticación ----
    check("portada sin token es 401", client.get("/api/v1/hub/inicio").status_code == 401)
    check("token basura es 401",
          client.get("/api/v1/hub/inicio", headers={"Authorization": "Bearer no.es.un.jwt"}).status_code == 401)

    # ---- Acceso por módulo según membresía ----
    r = client.get("/api/v1/hub/inicio", headers=auth)
    check("portada con token", r.status_code == 200, r.text)
    mods = {m["slug"]: m for m in r.json()["modulos"]}
    check("módulo abierto es accesible", mods["cop"]["permitido"] is True)
    check("módulo con membresía se niega sin ella", mods["libros"]["permitido"] is False)
    check("módulo negado no filtra su URL", mods["libros"]["href"] is None)

    uid = client.get("/api/v1/auth/me", headers=auth).json()["id"]
    with engine.begin() as conn:
        conn.execute(membresias.insert().values(
            user_id=uid, tipo="biblioteca", estado="activa", inicia_at=now, created_at=now))
    mods = {m["slug"]: m for m in client.get("/api/v1/hub/inicio", headers=auth).json()["modulos"]}
    check("membresía activa abre el módulo", mods["libros"]["permitido"] is True)
    check("módulo externo resuelve a OverDrive", "overdrive.com" in (mods["libros"]["href"] or ""))

    # Vencida no cuenta, aunque el estado siga en 'activa'.
    from datetime import timedelta
    with engine.begin() as conn:
        conn.execute(update(membresias).where(membresias.c.user_id == uid)
                     .values(vence_at=now - timedelta(days=1)))
    mods = {m["slug"]: m for m in client.get("/api/v1/hub/inicio", headers=auth).json()["modulos"]}
    check("membresía vencida no da acceso", mods["libros"]["permitido"] is False)

    # ---- Cobros pendientes ----
    with engine.begin() as conn:
        conn.execute(cargos.insert().values(
            user_id=uid, concepto="multa", descripcion="Atraso en devolución",
            monto_centimos=140000, moneda="CRC", estado="pendiente", created_at=now))
        conn.execute(cargos.insert().values(
            user_id=uid, concepto="membresia", descripcion="Anualidad", monto_centimos=1500000,
            moneda="CRC", estado="pagado", pagado_at=now, created_at=now))
    body = client.get("/api/v1/hub/inicio", headers=auth).json()
    check("solo se listan cargos pendientes", len(body["cargos_pendientes"]) == 1)
    check("monto entero en céntimos", body["cargos_pendientes"][0]["monto_centimos"] == 140000)

    # ---- ARCO (Ley 8968): público, no exige cuenta ----
    r = client.post("/api/v1/hub/arco", json={
        "email": "titular@example.com", "nombre": "Titular Datos", "tipo": "acceso",
        "detalle": "Solicito copia de mis datos personales tratados por el Hub."})
    check("solicitud ARCO se registra", r.status_code == 201, r.text)
    r = client.post("/api/v1/hub/arco", json={
        "email": "titular@example.com", "nombre": "Titular", "tipo": "borrado_total",
        "detalle": "Tipo inventado que debe rechazarse."})
    check("tipo ARCO inválido se rechaza", r.status_code == 422)

    # ---- Bitácora append-only forzada por la base (Panorama Legal, Paso 6) ----
    with engine.connect() as conn:
        n = conn.execute(select(audit_log)).fetchall()
        check("la bitácora registró las acciones", len(n) >= 3, f"filas={len(n)}")
    for sql, nombre in [("UPDATE audit_log SET accion='x'", "UPDATE a la bitácora"),
                        ("DELETE FROM audit_log", "DELETE a la bitácora")]:
        try:
            with engine.begin() as conn:
                conn.execute(text(sql))
            check(f"{nombre} bloqueado", False, "la base lo permitió")
        except Exception:
            check(f"{nombre} bloqueado", True)

    # ---- Limitador por IP (probado directo: en HTTP estorbaría al resto de la suite) ----
    rl = RateLimiter()
    check("limitador deja pasar hasta el tope", all(rl.allow("ip-a", 3) for _ in range(3)))
    check("limitador corta al superar el tope", rl.allow("ip-a", 3) is False)
    check("el tope es por clave, no global", rl.allow("ip-b", 3) is True)

    print(f"\n{PASSED}/{PASSED} pruebas OK")


if __name__ == "__main__":
    run()
