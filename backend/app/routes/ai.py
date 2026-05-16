from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents import AnalyzerAgent, ReplyAgent
from app.auth.security import get_current_organization, get_current_user
from app.database import get_db
from app.models import OrganizationMember, User
from app.schemas import AnalyzeLeadRequest, AnalyzeLeadResponse, ReplyRequest, ReplyResponse
from app.services.ai_usage import AIUsageService
from app.services.ai_workflow import AILeadWorkflow

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze-lead", response_model=AnalyzeLeadResponse)
def analyze_lead(
    payload: AnalyzeLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> AnalyzeLeadResponse:
    usage = AIUsageService()
    model = usage.model_for("complex")
    usage.ensure_within_limit(db, membership, "/ai/analyze-lead", payload.message, model, output_token_budget=1200)
    lead, analysis, task, activity = AILeadWorkflow(model=model).run(db, current_user, membership.organization_id, payload)
    usage.record_usage(
        db,
        current_user.id,
        membership.organization_id,
        "/ai/analyze-lead",
        model,
        payload.message,
        f"{analysis.summary}\n{analysis.recommended_action}\n{analysis.suggested_reply}",
    )
    return AnalyzeLeadResponse(lead=lead, analysis=analysis, task=task, activity=activity)


@router.post("/generate-reply", response_model=ReplyResponse)
def generate_reply(
    payload: ReplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> ReplyResponse:
    usage = AIUsageService()
    model = usage.model_for("simple")
    usage.ensure_within_limit(db, membership, "/ai/generate-reply", payload.message, model, output_token_budget=500)
    analysis = AnalyzerAgent().analyze(payload.message, model)
    reply = ReplyAgent().draft(payload.message, analysis, payload.tone, model)
    usage.record_usage(db, current_user.id, membership.organization_id, "/ai/generate-reply", model, payload.message, reply)
    return ReplyResponse(suggested_reply=reply)
