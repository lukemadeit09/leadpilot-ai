from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user
from app.database import get_db
from app.models import OrganizationMember, UploadedDocument, User
from app.schemas import KnowledgeAskRequest, KnowledgeAskResponse, KnowledgeDocumentRead
from app.services.activity import log_activity
from app.services.knowledge import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledgebase"])


@router.post("/upload", response_model=KnowledgeDocumentRead)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> UploadedDocument:
    document = await KnowledgeService().upload(db, current_user, membership.organization_id, file)
    log_activity(db, current_user.id, membership.organization_id, "document_uploaded", f"Knowledge document uploaded: {document.filename}")
    db.commit()
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


@router.post("/ask", response_model=KnowledgeAskResponse)
def ask_knowledge(
    payload: KnowledgeAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> KnowledgeAskResponse:
    answer, sources = KnowledgeService().answer(db, membership.organization_id, payload.question)
    log_activity(db, current_user.id, membership.organization_id, "knowledge_question", f"Asked knowledge base: {payload.question}")
    db.commit()
    return KnowledgeAskResponse(answer=answer, sources=list(dict.fromkeys(sources)))
