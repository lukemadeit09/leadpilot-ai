from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIJob, AIJobStatus, OrganizationMember, User
from app.schemas import AnalyzeLeadRequest
from app.services.ai_usage import AIUsageService
from app.config import get_settings
from app.tasks.ai_jobs import analyze_lead_job, process_analyze_lead_job


class AIJobService:
    endpoint = "/ai/analyze-lead"

    def create_analysis_job(
        self,
        db: Session,
        user: User,
        membership: OrganizationMember,
        payload: AnalyzeLeadRequest,
    ) -> AIJob:
        usage = AIUsageService()
        model = usage.model_for("complex")
        usage.ensure_within_limit(db, membership, self.endpoint, payload.message, model, output_token_budget=1200)

        job = AIJob(
            owner_id=user.id,
            organization_id=membership.organization_id,
            endpoint_used=self.endpoint,
            request_payload=payload.model_dump(mode="json"),
            max_attempts=3,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        if get_settings().celery_task_always_eager:
            job.celery_task_id = "eager"
            db.commit()
            process_analyze_lead_job(db, job.id)
        else:
            task = analyze_lead_job.delay(str(job.id))
            job.celery_task_id = task.id
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_job_for_member(db: Session, job_id: UUID, membership: OrganizationMember) -> AIJob:
        job = db.scalar(select(AIJob).where(AIJob.id == job_id, AIJob.organization_id == membership.organization_id))
        if not job:
            raise HTTPException(status_code=404, detail="AI job not found")
        return job

    @staticmethod
    def mark_failed(db: Session, job: AIJob, message: str) -> None:
        job.status = AIJobStatus.failed
        job.error_message = message
        db.commit()
