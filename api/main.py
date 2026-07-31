"""CCCN Hub — API principal.

Un solo proceso sirve la API y el frontend: mismo origen ⇒ la CSP estricta aplica
también a las páginas y el JWT viaja en fetch relativo a /api/v1.

Seguridad transversal:
- Headers estrictos (CSP sin 'unsafe-inline', HSTS en prod, nosniff, frame-ancestors 'none')
- SessionMiddleware solo para el estado del flujo OAuth (cookie firmada, httponly)
- Rate limiting en rutas públicas y de auth (dentro de cada router)
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from . import config
from .db import init_db
from .routers import auth_routes, hub

app = FastAPI(
    title="CCCN Hub",
    version="0.1.0",
    docs_url=None if config.IS_PROD else "/docs",
    redoc_url=None,
    openapi_url=None if config.IS_PROD else "/openapi.json",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=config.SESSION_SECRET,
    session_cookie="hub_oauth",
    https_only=config.IS_PROD,
    same_site="lax",
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    # 'unsafe-inline' prohibido: sin <style> ni style="" inline, sin JS embebido.
    csp = ("default-src 'none'; style-src 'self'; img-src 'self' data:; font-src 'self'; "
           "script-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; "
           "frame-ancestors 'none'")
    response.headers.setdefault("Content-Security-Policy", csp)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if config.IS_PROD:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(hub.router, prefix="/api/v1")

_web = Path(__file__).parent.parent / "web"
if _web.exists():
    app.mount("/app", StaticFiles(directory=str(_web), html=True), name="app")


@app.get("/health")
def health():
    return {"status": "ok", "env": config.ENV}


@app.get("/")
def root():
    return RedirectResponse(url="/app/")


@app.on_event("startup")
def _startup():
    init_db()
