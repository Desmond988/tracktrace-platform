import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.routes import admin, auth, content, forms, me, people, shipments, tracking
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.session import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Track & Trace API", version="1.0.0",
    description="Shipment tracking, customer portal and staff operations. No payment functionality by design.",
    docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json",
)
register_error_handlers(app)

_cors = settings.cors_origins_list
if callable(_cors):
    _cors = _cors()
_origins = list(_cors or [])
_frontend = getattr(settings, "FRONTEND_URL", None) or getattr(settings, "frontend_url", None)
if _frontend and _frontend not in _origins:
    _origins.append(_frontend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if not request.url.path.startswith(("/docs", "/redoc")):
        resp.headers.setdefault("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
    if settings.is_production:
        resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return resp

for r in (auth.router, tracking.router, shipments.router, me.router, people.router, forms.router, content.router, admin.router):
    app.include_router(r)

@app.get("/health", tags=["health"])
def health():
    """Liveness: the process is up."""
    return {"status": "ok"}

@app.get("/health/db", tags=["health"])
def health_db():
    """Readiness: the database answers."""
    try:
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        return {"status": "ok", "database": "up"}
    except Exception:
        logging.getLogger("app.health").exception("DB health check failed")
        return JSONResponse({"status": "error", "database": "down"}, status_code=503)