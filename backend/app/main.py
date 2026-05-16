from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.middleware.request_logging import log_requests
from app.middleware.security_headers import add_security_headers
from app.models import *  # noqa: F403
from app.routes import activity, ai, auth, billing, integrations, knowledge, leads, tasks
from app.utils.logging import configure_logging
from app.utils.sentry import init_sentry

settings = get_settings()
configure_logging(settings)
init_sentry(settings)

app = FastAPI(
    title="LeadPilot AI API",
    description="AI-powered CRM automation API for sales teams.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-LeadPilot-Key", "Stripe-Signature"],
)
app.middleware("http")(log_requests)
app.middleware("http")(add_security_headers)


@app.on_event("startup")
def on_startup() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leadpilot-api", "environment": settings.app_env}


@app.get("/live", tags=["system"])
def live() -> dict[str, str]:
    return {"status": "ok", "service": "leadpilot-api", "checked_at": datetime.now(timezone.utc).isoformat()}


@app.get("/ready", tags=["system"])
def ready(db: Session = Depends(get_db)) -> dict[str, object]:
    checks: dict[str, str] = {"database": "ok"}
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"
        return {"status": "degraded", "checks": checks}
    return {"status": "ok", "checks": checks}


app.include_router(auth.router)
app.include_router(leads.dashboard_router)
app.include_router(leads.router)
app.include_router(ai.router)
app.include_router(billing.router)
app.include_router(integrations.router)
app.include_router(tasks.router)
app.include_router(knowledge.router)
app.include_router(activity.router)
