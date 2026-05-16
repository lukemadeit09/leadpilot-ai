from uuid import UUID

from app.database import SessionLocal
from app.services.knowledge import KnowledgeService
from app.worker import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def process_document_job(self, document_id: str) -> dict:
    with SessionLocal() as db:
        document = KnowledgeService().process_document(db, UUID(document_id))
        return {"document_id": str(document.id), "status": document.status.value, "chunk_count": document.chunk_count}
