from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents import AnalyzerAgent, ReplyAgent
from app.auth.security import get_current_organization, get_current_user
from app.database import get_db
from app.models import OrganizationMember, User
from app.schemas import AnalyzeLeadRequest, AnalyzeLeadResponse, ReplyRequest, ReplyResponse
from app.services.ai_workflow import AILeadWorkflow

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/analyze-lead", response_model=AnalyzeLeadResponse)
def analyze_lead(
    payload: AnalyzeLeadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> AnalyzeLeadResponse:
    lead, analysis, task, activity = AILeadWorkflow().run(db, current_user, membership.organization_id, payload)
    return AnalyzeLeadResponse(lead=lead, analysis=analysis, task=task, activity=activity)


@router.post("/generate-reply", response_model=ReplyResponse)
def generate_reply(
    payload: ReplyRequest,
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> ReplyResponse:
    analysis = AnalyzerAgent().analyze(payload.message)
    reply = ReplyAgent().draft(payload.message, analysis, payload.tone)
    return ReplyResponse(suggested_reply=reply)
