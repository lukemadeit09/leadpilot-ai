from uuid import UUID

from app.database import SessionLocal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIJob, AIJobStatus, OrganizationMember, User
from app.schemas import AnalyzeLeadRequest, AnalyzeLeadResponse
from app.services.ai_usage import AIUsageService
from app.services.ai_workflow import AILeadWorkflow
from app.worker import celery_app


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_backoff=True, retry_backoff_max=60, retry_jitter=True, max_retries=3)
def analyze_lead_job(self, job_id: str) -> dict:
    with SessionLocal() as db:
        return process_analyze_lead_job(db, UUID(job_id), retries=self.request.retries, max_retries=self.max_retries)


def process_analyze_lead_job(db: Session, job_id: UUID, retries: int = 0, max_retries: int = 3) -> dict:
    job = db.get(AIJob, job_id)
    if not job:
        return {"status": "missing", "job_id": str(job_id)}

    job.status = AIJobStatus.running
    job.attempts = retries + 1
    job.error_message = None
    db.commit()

    try:
        user = db.get(User, job.owner_id)
        membership = db.scalar(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == job.organization_id,
                OrganizationMember.user_id == job.owner_id,
            )
        )
        if not user or not membership:
            raise RuntimeError("AI job owner or organization membership no longer exists")

        payload = AnalyzeLeadRequest.model_validate(job.request_payload)
        usage = AIUsageService()
        model = usage.model_for("complex")
        usage.ensure_within_limit(db, membership, job.endpoint_used, payload.message, model, output_token_budget=1200)
        lead, analysis, task, activity = AILeadWorkflow(model=model).run(db, user, job.organization_id, payload)
        usage.record_usage(
            db,
            user.id,
            job.organization_id,
            job.endpoint_used,
            model,
            payload.message,
            f"{analysis.summary}\n{analysis.recommended_action}\n{analysis.suggested_reply}",
        )

        response = AnalyzeLeadResponse(lead=lead, analysis=analysis, task=task, activity=activity).model_dump(mode="json")
        job = db.get(AIJob, job_id)
        if not job:
            return response
        job.status = AIJobStatus.succeeded
        job.result_payload = response
        job.error_message = None
        db.commit()
        return response
    except Exception as exc:
        job = db.get(AIJob, job_id)
        if job:
            job.error_message = str(exc)
            job.status = AIJobStatus.failed if retries >= max_retries else AIJobStatus.running
            db.commit()
        raise
