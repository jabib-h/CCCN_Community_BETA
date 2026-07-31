"""Portada autenticada del Hub y canal de derechos ARCO.

El catálogo de módulos se resuelve en el servidor contra las membresías reales del
usuario: el frontend recibe ya filtrado qué puede abrir y qué no (Panorama Legal §3.3).
Ocultar una tarjeta en el navegador no es control de acceso; la puerta real es
`require_modulo` en cada router de módulo.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from .. import config
from ..auth import client_ip, get_current_user, membresias_activas
from ..db import arco_requests, audit, cargos, engine, membresias, utcnow
from ..modules import MODULOS, puede_entrar
from ..security import rate_limiter

router = APIRouter()


@router.get("/hub/inicio")
def inicio(user: dict = Depends(get_current_user)):
    """Todo lo que la portada necesita en una sola llamada."""
    activas = membresias_activas(user["id"])
    with engine.connect() as conn:
        mis_membresias = conn.execute(
            select(membresias.c.tipo, membresias.c.estado, membresias.c.vence_at)
            .where(membresias.c.user_id == user["id"])).fetchall()
        pendientes = conn.execute(
            select(cargos.c.id, cargos.c.descripcion, cargos.c.monto_centimos,
                   cargos.c.moneda, cargos.c.vence_at)
            .where((cargos.c.user_id == user["id"]) & (cargos.c.estado == "pendiente"))).fetchall()

    modulos = []
    for m in MODULOS:
        permitido = puede_entrar(m, user["role"], activas)
        modulos.append({
            "slug": m["slug"], "nombre": m["nombre"], "descripcion": m["descripcion"],
            "estado": m["estado"], "externo": m["externo"],
            "href": (config.OVERDRIVE_URL if m["externo"] else m["href"]) if permitido else None,
            "permitido": permitido,
            "requiere_membresia": m["requiere_membresia"],
        })

    return {
        "usuario": {"display_name": user["display_name"], "role": user["role"],
                    "email": user["email"], "sede": user["sede"]},
        "modulos": modulos,
        "membresias": [{"tipo": r.tipo, "estado": r.estado,
                        "vence_at": r.vence_at.isoformat() if r.vence_at else None}
                       for r in mis_membresias],
        "cargos_pendientes": [{"id": r.id, "descripcion": r.descripcion,
                               "monto_centimos": r.monto_centimos, "moneda": r.moneda,
                               "vence_at": r.vence_at.isoformat() if r.vence_at else None}
                              for r in pendientes],
    }


# ---------- Derechos ARCO (Ley 8968 art. 5.7) ----------
# Público a propósito: ejercer un derecho no puede exigir tener cuenta activa.

class ArcoIn(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=2, max_length=200)
    tipo: str = Field(pattern="^(acceso|rectificacion|cancelacion|oposicion)$")
    detalle: str = Field(min_length=10, max_length=4000)


@router.post("/hub/arco", status_code=201)
def solicitud_arco(body: ArcoIn, request: Request):
    if not rate_limiter.allow(f"arco:{client_ip(request)}", config.RATE_LIMIT_AUTH):
        raise HTTPException(429, "Demasiadas solicitudes; probá de nuevo en un minuto")
    with engine.begin() as conn:
        result = conn.execute(arco_requests.insert().values(
            created_at=utcnow(), email=body.email.lower(), nombre=body.nombre.strip(),
            tipo=body.tipo, detalle=body.detalle, estado="pendiente"))
        rid = result.inserted_primary_key[0]
        audit(conn, actor_ip=client_ip(request), accion="arco_solicitud",
              entidad="arco_request", entidad_id=rid, detalle={"tipo": body.tipo})
    return {"id": rid, "estado": "pendiente",
            "mensaje": f"Recibimos tu solicitud. Te responderemos al correo indicado. "
                       f"Consultas: {config.CONTACTO_DATOS}"}
