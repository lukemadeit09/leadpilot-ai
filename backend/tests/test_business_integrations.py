import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import IntegrationUsageEvent, Lead, OrganizationAPIKey
from app.services.api_keys import OrganizationAPIKeyService
from tests.conftest import auth_headers, register_user


def create_api_key(client: TestClient, token: str, name: str = "Website") -> str:
    response = client.post("/integrations/api-keys", headers=auth_headers(token), json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["api_key"]


def test_invalid_api_key_is_rejected_for_public_intake(client: TestClient) -> None:
    response = client.post(
        "/integrations/public/leads",
        headers={"X-LeadPilot-Key": "lp_live_invalid"},
        json={"message": "Need pricing next week."},
    )

    assert response.status_code == 401


def test_public_webhook_creates_org_scoped_lead_and_usage(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="webhook-owner@example.com")
    other = register_user(client, email="webhook-other@example.com")
    api_key = create_api_key(client, owner["access_token"], "Webhook")

    response = client.post(
        "/integrations/public/webhook",
        headers={"X-LeadPilot-Key": api_key},
        json={
            "event": "contact_form.submitted",
            "lead": {"name": "Webhook Buyer", "email": "buyer@example.com", "company": "Acme", "message": "Can we book a demo?"},
            "metadata": {"source": "website"},
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["name"] == "Webhook Buyer"
    owner_leads = client.get("/leads", headers=auth_headers(owner["access_token"]))
    other_leads = client.get("/leads", headers=auth_headers(other["access_token"]))
    assert [lead["name"] for lead in owner_leads.json()] == ["Webhook Buyer"]
    assert other_leads.json() == []

    usage = db_session.scalar(select(IntegrationUsageEvent).where(IntegrationUsageEvent.endpoint == "/integrations/public/webhook"))
    assert usage is not None
    assert usage.event_type == "contact_form.submitted"
    assert usage.status_code == 201


def test_widget_config_is_org_scoped_and_publicly_read_with_api_key(client: TestClient) -> None:
    owner = register_user(client, email="widget-owner@example.com")
    other = register_user(client, email="widget-other@example.com")
    api_key = create_api_key(client, owner["access_token"], "Widget")

    updated = client.patch(
        "/integrations/widget-config",
        headers=auth_headers(owner["access_token"]),
        json={"widget_title": "Request a demo", "widget_accent_color": "#22c55e"},
    )
    assert updated.status_code == 200, updated.text

    public_config = client.get("/integrations/public/widget-config", headers={"X-LeadPilot-Key": api_key})
    other_config = client.get("/integrations/widget-config", headers=auth_headers(other["access_token"]))

    assert public_config.status_code == 200
    assert public_config.json()["widget_title"] == "Request a demo"
    assert other_config.status_code == 200
    assert other_config.json()["widget_title"] == "Talk to sales"


def test_public_endpoint_rate_limit_applies_to_widget_calls(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_PUBLIC_PER_MINUTE", "1")
    get_settings.cache_clear()
    owner = register_user(client, email="widget-rate@example.com")
    api_key = create_api_key(client, owner["access_token"], "Widget")

    first = client.get("/integrations/public/widget-config", headers={"X-LeadPilot-Key": api_key})
    second = client.get("/integrations/public/widget-config", headers={"X-LeadPilot-Key": api_key})

    assert first.status_code == 200
    assert second.status_code == 429


def test_api_key_is_hash_only_and_revocation_blocks_public_calls(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="revoke-owner@example.com")
    raw_key = create_api_key(client, owner["access_token"], "Revocable")
    stored = db_session.scalar(select(OrganizationAPIKey))
    assert stored is not None
    assert stored.key_hash == OrganizationAPIKeyService.hash_key(raw_key)
    assert raw_key not in stored.key_hash

    response = client.delete(f"/integrations/api-keys/{stored.id}", headers=auth_headers(owner["access_token"]))
    assert response.status_code == 204

    blocked = client.post(
        "/integrations/public/leads",
        headers={"X-LeadPilot-Key": raw_key},
        json={"message": "Need pricing next week."},
    )
    assert blocked.status_code == 401


def test_public_lead_intake_tracks_usage(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="usage-owner@example.com")
    api_key = create_api_key(client, owner["access_token"], "Usage")

    response = client.post(
        "/integrations/public/leads",
        headers={"X-LeadPilot-Key": api_key},
        json={"name": "Usage Buyer", "message": "Need pricing next week."},
    )

    assert response.status_code == 201
    lead = db_session.scalar(select(Lead).where(Lead.name == "Usage Buyer"))
    usage = db_session.scalar(select(IntegrationUsageEvent).where(IntegrationUsageEvent.endpoint == "/integrations/public/leads"))
    assert lead is not None
    assert usage is not None
    assert usage.organization_id == lead.organization_id
