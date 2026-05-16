from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import *  # noqa: F403
from app.routes import activity, ai, auth, knowledge, leads, tasks

settings = get_settings()

app = FastAPI(
    title="LeadPilot AI API",
    description="AI-powered CRM automation API for sales teams.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "leadpilot-api"}


app.include_router(auth.router)
app.include_router(leads.dashboard_router)
app.include_router(leads.router)
app.include_router(ai.router)
app.include_router(tasks.router)
app.include_router(knowledge.router)
app.include_router(activity.router)
