from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "leadpilot",
    broker=settings.broker_url,
    backend=settings.result_backend_url,
    include=["app.tasks.ai_jobs", "app.tasks.knowledge_jobs"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
)
