from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user
from app.database import get_db
from app.config import get_settings
from app.models import OrganizationMember, UploadedDocument, User
from app.schemas import KnowledgeAskRequest, KnowledgeAskResponse, KnowledgeDocumentRead, KnowledgeSearchRequest, KnowledgeSearchResponse
from app.services.activity import log_activity
from app.services.ai_usage import AIUsageService
from app.services.knowledge import KnowledgeService
from app.tasks.knowledge_jobs import process_document_job

router = APIRouter(prefix="/knowledge", tags=["knowledgebase"])


@router.post("/upload", response_model=KnowledgeDocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> UploadedDocument:
    try:
        document = await KnowledgeService().upload(db, current_user, membership.organization_id, file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    log_activity(db, current_user.id, membership.organization_id, "document_uploaded", f"Knowledge document uploaded: {document.filename}")
    db.commit()
    db.refresh(document)
    if get_settings().celery_task_always_eager:
        KnowledgeService().process_document(db, document.id)
    else:
        process_document_job.delay(str(document.id))
    db.refresh(document)
    return document


@router.get("/documents", response_model=list[KnowledgeDocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> list[UploadedDocument]:
    return list(
        db.scalars(
            select(UploadedDocument).where(UploadedDocument.organization_id == membership.organization_id).order_by(desc(UploadedDocument.created_at))
        ).all()
    )


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> KnowledgeSearchResponse:
    results = KnowledgeService().search(db, membership.organization_id, payload.query, payload.limit)
    return KnowledgeSearchResponse(results=results)


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge(
    payload: KnowledgeAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> KnowledgeAskResponse:
    usage = AIUsageService()
    model = usage.model_for("simple")
    usage.ensure_within_limit(db, membership, "/knowledge/ask", payload.question, model, output_token_budget=700)
    answer, citations = KnowledgeService().answer(db, membership.organization_id, payload.question, model)
    log_activity(db, current_user.id, membership.organization_id, "knowledge_question", f"Asked knowledge base: {payload.question}")
    db.commit()
    usage.record_usage(db, current_user.id, membership.organization_id, "/knowledge/ask", model, payload.question, answer)
    sources = [citation["filename"] for citation in citations]
    return KnowledgeAskResponse(answer=answer, sources=list(dict.fromkeys(sources)), citations=citations)
