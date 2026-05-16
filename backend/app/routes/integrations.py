from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user, require_organization_admin
from app.database import get_db
from app.models import Lead, LeadStatus, OrganizationAPIKey, OrganizationMember, User
from app.schemas import APIKeyCreate, APIKeyCreated, APIKeyRead, LeadRead, PublicLeadCreate
from app.services.activity import log_activity
from app.services.api_keys import OrganizationAPIKeyService
from app.services.rate_limit import rate_limit_public
from app.services.security_audit import log_security_event

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/api-keys", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> APIKeyCreated:
    api_key, raw_key = OrganizationAPIKeyService().create_key(db, membership.organization_id, current_user.id, payload.name)
    log_security_event(
        db,
        "api_key_created",
        f"Organization API key created: {api_key.name}",
        owner_id=current_user.id,
        organization_id=membership.organization_id,
        metadata={"key_prefix": api_key.key_prefix},
    )
    db.commit()
    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        api_key=raw_key,
        created_at=api_key.created_at,
    )


@router.get("/api-keys", response_model=list[APIKeyRead])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> list[OrganizationAPIKey]:
    return list(
        db.scalars(
            select(OrganizationAPIKey)
            .where(OrganizationAPIKey.organization_id == membership.organization_id)
            .order_by(desc(OrganizationAPIKey.created_at))
        ).all()
    )


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> None:
    api_key = db.scalar(
        select(OrganizationAPIKey).where(
            OrganizationAPIKey.id == api_key_id,
            OrganizationAPIKey.organization_id == membership.organization_id,
        )
    )
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.revoked_at = datetime.now(timezone.utc)
    log_security_event(
        db,
        "api_key_revoked",
        f"Organization API key revoked: {api_key.name}",
        owner_id=current_user.id,
        organization_id=membership.organization_id,
        metadata={"key_prefix": api_key.key_prefix},
    )
    db.commit()


@router.post("/public/leads", response_model=LeadRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_public)])
def public_lead_intake(
    payload: PublicLeadCreate,
    x_leadpilot_key: str | None = Header(default=None, alias="X-LeadPilot-Key"),
    db: Session = Depends(get_db),
) -> Lead:
    api_key = OrganizationAPIKeyService().authenticate(db, x_leadpilot_key)
    lead = Lead(
        owner_id=api_key.created_by_id,
        organization_id=api_key.organization_id,
        name=payload.name,
        email=str(payload.email) if payload.email else None,
        company=payload.company,
        message=payload.message,
        status=LeadStatus.new,
    )
    db.add(lead)
    db.flush()
    log_activity(db, api_key.created_by_id, api_key.organization_id, "public_lead_created", "Lead captured through public integration.", lead.id)
    log_security_event(
        db,
        "api_key_used",
        "Organization API key used for public lead intake",
        owner_id=api_key.created_by_id,
        organization_id=api_key.organization_id,
        metadata={"key_prefix": api_key.key_prefix},
    )
    db.commit()
    db.refresh(lead)
    return lead
