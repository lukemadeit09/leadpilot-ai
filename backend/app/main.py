import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from redis import Redis
from sqlalchemy import text

from app.config import get_settings
from app.database import engine
from app.models import *  # noqa: F403
from app.routes import activity, ai, auth, knowledge, leads, tasks
from app.utils.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LeadPilot AI API",
    description="AI-powered CRM automation API for sales teams.",
    version="0.1.0",
)

if settings.app_env.lower() == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.on_event("startup")
def on_startup() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info("LeadPilot API started in %s mode", settings.app_env)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leadpilot-api"}


@app.get("/ready", tags=["system"])
def readiness() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2).ping()
    return {"status": "ready", "database": "ok", "redis": "ok"}


app.include_router(auth.router)
app.include_router(leads.dashboard_router)
app.include_router(leads.router)
app.include_router(ai.router)
app.include_router(tasks.router)
app.include_router(knowledge.router)
app.include_router(activity.router)
