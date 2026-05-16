from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.auth.security import get_current_organization, get_current_user, require_organization_admin
from app.database import get_db
from app.models import IntegrationUsageEvent, Lead, LeadStatus, Organization, OrganizationAPIKey, OrganizationMember, User
from app.schemas import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyRead,
    IntegrationUsageRead,
    LeadRead,
    PublicLeadCreate,
    PublicWebhookPayload,
    WidgetConfigRead,
    WidgetConfigUpdate,
)
from app.services.activity import log_activity
from app.services.api_keys import OrganizationAPIKeyService
from app.services.integrations import track_integration_usage
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


@router.get("/usage", response_model=list[IntegrationUsageRead])
def list_integration_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> list[IntegrationUsageEvent]:
    return list(
        db.scalars(
            select(IntegrationUsageEvent)
            .where(IntegrationUsageEvent.organization_id == membership.organization_id)
            .order_by(desc(IntegrationUsageEvent.created_at))
            .limit(100)
        ).all()
    )


@router.get("/widget-config", response_model=WidgetConfigRead)
def get_widget_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(get_current_organization),
) -> WidgetConfigRead:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return WidgetConfigRead(
        organization_id=organization.id,
        widget_enabled=organization.widget_enabled,
        widget_title=organization.widget_title,
        widget_accent_color=organization.widget_accent_color,
    )


@router.patch("/widget-config", response_model=WidgetConfigRead)
def update_widget_config(
    payload: WidgetConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    membership: OrganizationMember = Depends(require_organization_admin),
) -> WidgetConfigRead:
    organization = db.get(Organization, membership.organization_id)
    if not organization:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(organization, field, value)
    log_security_event(
        db,
        "widget_config_updated",
        "Integration widget configuration updated",
        owner_id=current_user.id,
        organization_id=organization.id,
        metadata={"fields": list(updates.keys())},
    )
    db.commit()
    db.refresh(organization)
    return WidgetConfigRead(
        organization_id=organization.id,
        widget_enabled=organization.widget_enabled,
        widget_title=organization.widget_title,
        widget_accent_color=organization.widget_accent_color,
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
    lead = _create_public_lead(db, api_key, payload)
    track_integration_usage(db, api_key, "/integrations/public/leads", "lead_created", status.HTTP_201_CREATED)
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


@router.post("/public/webhook", response_model=LeadRead, status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit_public)])
def public_webhook(
    payload: PublicWebhookPayload,
    x_leadpilot_key: str | None = Header(default=None, alias="X-LeadPilot-Key"),
    db: Session = Depends(get_db),
) -> Lead:
    api_key = OrganizationAPIKeyService().authenticate(db, x_leadpilot_key)
    lead = _create_public_lead(db, api_key, payload.lead)
    track_integration_usage(
        db,
        api_key,
        "/integrations/public/webhook",
        payload.event,
        status.HTTP_201_CREATED,
        metadata={"metadata_keys": list(payload.metadata.keys())[:20]},
    )
    log_activity(db, api_key.created_by_id, api_key.organization_id, "webhook_lead_created", f"Lead captured through webhook: {payload.event}", lead.id)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("/public/widget-config", response_model=WidgetConfigRead, dependencies=[Depends(rate_limit_public)])
def public_widget_config(
    x_leadpilot_key: str | None = Header(default=None, alias="X-LeadPilot-Key"),
    db: Session = Depends(get_db),
) -> WidgetConfigRead:
    api_key = OrganizationAPIKeyService().authenticate(db, x_leadpilot_key)
    organization = db.get(Organization, api_key.organization_id)
    if not organization or not organization.widget_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Widget is not available")
    track_integration_usage(db, api_key, "/integrations/public/widget-config", "widget_config_read", status.HTTP_200_OK)
    db.commit()
    return WidgetConfigRead(
        organization_id=organization.id,
        widget_enabled=organization.widget_enabled,
        widget_title=organization.widget_title,
        widget_accent_color=organization.widget_accent_color,
    )


@router.get("/widget.js", include_in_schema=False, dependencies=[Depends(rate_limit_public)])
def widget_script() -> Response:
    script = """
(function () {
  var script = document.currentScript;
  var apiKey = script && script.getAttribute("data-leadpilot-key");
  var apiBase = (script && script.getAttribute("data-api-base")) || "";
  if (!apiKey || document.getElementById("leadpilot-widget")) return;

  var root = document.createElement("div");
  root.id = "leadpilot-widget";
  root.style.cssText = "position:fixed;right:20px;bottom:20px;z-index:2147483647;font-family:Inter,ui-sans-serif,system-ui,sans-serif";
  root.innerHTML = '<button data-lp-toggle style="border:0;border-radius:999px;background:#34d399;color:#07110f;padding:12px 16px;font-weight:700;box-shadow:0 12px 30px rgba(0,0,0,.25);cursor:pointer">Contact sales</button><form data-lp-form style="display:none;width:320px;margin-top:10px;border:1px solid rgba(148,163,184,.3);border-radius:16px;background:#08110f;color:white;padding:16px;box-shadow:0 24px 60px rgba(0,0,0,.35)"><div data-lp-title style="font-weight:700;margin-bottom:10px">Talk to sales</div><input name="name" placeholder="Name" style="box-sizing:border-box;width:100%;margin-bottom:8px;padding:10px;border-radius:10px;border:1px solid #334155;background:#020617;color:white"><input name="email" type="email" placeholder="Email" style="box-sizing:border-box;width:100%;margin-bottom:8px;padding:10px;border-radius:10px;border:1px solid #334155;background:#020617;color:white"><input name="company" placeholder="Company" style="box-sizing:border-box;width:100%;margin-bottom:8px;padding:10px;border-radius:10px;border:1px solid #334155;background:#020617;color:white"><textarea name="message" required minlength="5" placeholder="How can we help?" style="box-sizing:border-box;width:100%;min-height:86px;margin-bottom:10px;padding:10px;border-radius:10px;border:1px solid #334155;background:#020617;color:white"></textarea><button type="submit" style="width:100%;border:0;border-radius:10px;background:#34d399;color:#07110f;padding:10px;font-weight:700;cursor:pointer">Send</button><p data-lp-status style="min-height:18px;margin:10px 0 0;color:#94a3b8;font-size:12px"></p></form>';
  document.body.appendChild(root);

  var toggle = root.querySelector("[data-lp-toggle]");
  var form = root.querySelector("[data-lp-form]");
  var title = root.querySelector("[data-lp-title]");
  var status = root.querySelector("[data-lp-status]");
  toggle.addEventListener("click", function () {
    form.style.display = form.style.display === "none" ? "block" : "none";
  });

  fetch(apiBase + "/integrations/public/widget-config", { headers: { "X-LeadPilot-Key": apiKey } })
    .then(function (res) { return res.ok ? res.json() : null; })
    .then(function (config) {
      if (!config) return;
      title.textContent = config.widget_title || "Talk to sales";
      toggle.textContent = config.widget_title || "Contact sales";
      toggle.style.background = config.widget_accent_color || "#34d399";
      form.querySelector("button[type=submit]").style.background = config.widget_accent_color || "#34d399";
    })
    .catch(function () {});

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    status.textContent = "Sending...";
    var data = new FormData(form);
    fetch(apiBase + "/integrations/public/leads", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-LeadPilot-Key": apiKey },
      body: JSON.stringify({
        name: data.get("name") || null,
        email: data.get("email") || null,
        company: data.get("company") || null,
        message: data.get("message")
      })
    }).then(function (res) {
      if (!res.ok) throw new Error("Request failed");
      form.reset();
      status.textContent = "Thanks. The team will follow up shortly.";
    }).catch(function () {
      status.textContent = "Could not send right now. Please try again.";
    });
  });
})();
"""
    return Response(content=script, media_type="application/javascript")


def _create_public_lead(db: Session, api_key: OrganizationAPIKey, payload: PublicLeadCreate) -> Lead:
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
    return lead
