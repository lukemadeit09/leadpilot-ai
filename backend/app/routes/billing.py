from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user, require_organization_admin
from app.database import get_db
from app.models import Organization, OrganizationMember, User
from app.schemas import BillingCheckoutRequest, BillingCheckoutResponse, BillingPortalResponse, PlanRead, PlanUpdate, UsageSummary
from app.services.ai_usage import AIUsageService
from app.services.stripe_billing import StripeBillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanRead])
def list_plans(current_user: User = Depends(get_current_user)) -> list[dict]:
    return AIUsageService().plan_catalog()


@router.get("/usage", response_model=UsageSummary)
def current_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> dict:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return AIUsageService().usage_summary(db, organization, current_user.id)


@router.post("/checkout", response_model=BillingCheckoutResponse)
def create_checkout_session(
    payload: BillingCheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> dict[str, str]:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return StripeBillingService().create_checkout_session(db, organization, current_user, payload.plan)


@router.post("/portal", response_model=BillingPortalResponse)
def create_billing_portal_session(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> dict[str, str]:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    return StripeBillingService().create_billing_portal_session(organization)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    payload = await request.body()
    service = StripeBillingService()
    event = service.construct_webhook_event(payload, stripe_signature)
    return service.handle_webhook_event(db, event)


@router.patch("/plan", response_model=UsageSummary)
def update_plan(
    payload: PlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> dict:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    organization.plan = payload.plan
    db.commit()
    db.refresh(organization)
    return AIUsageService().usage_summary(db, organization, current_user.id)
