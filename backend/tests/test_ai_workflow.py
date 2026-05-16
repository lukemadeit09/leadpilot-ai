from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIUsageEvent, OrganizationMember
from tests.conftest import auth_headers, register_user


def test_ai_workflow_fallback_creates_lead_analysis_task_activity_and_usage(
    client: TestClient,
    db_session: Session,
) -> None:
    token = register_user(client)["access_token"]

    response = client.post(
        "/ai/analyze-lead",
        headers=auth_headers(token),
        json={
            "name": "Avery Morgan",
            "email": "avery@example.com",
            "company": "Northstar Labs",
            "message": "Hi, we have 45 employees and want pricing plus a demo next week.",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["lead"]["company"] == "Northstar Labs"
    assert payload["lead"]["status"] == "qualified"
    assert payload["analysis"]["lead_score"] >= 80
    assert payload["analysis"]["sentiment"] == "positive"
    assert "demo" in payload["analysis"]["suggested_reply"].lower()
    assert payload["task"]["title"] == "Schedule demo with Northstar Labs"
    assert payload["activity"]["action"] == "email_analyzed"

    tasks = client.get("/tasks", headers=auth_headers(token))
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1

    activity = client.get("/activity", headers=auth_headers(token))
    assert activity.status_code == 200
    assert activity.json()[0]["action"] == "email_analyzed"

    usage = db_session.scalar(select(AIUsageEvent).where(AIUsageEvent.endpoint_used == "/ai/analyze-lead"))
    assert usage is not None
    assert usage.model_used == "gpt-4.1"
    assert usage.input_tokens > 0
    assert usage.output_tokens > 0
    assert Decimal(str(usage.estimated_cost)) > 0


def test_generate_reply_uses_fallback_without_openai_key(client: TestClient) -> None:
    token = register_user(client, email="reply@example.com")["access_token"]

    response = client.post(
        "/ai/generate-reply",
        headers=auth_headers(token),
        json={"message": "Can you send pricing and schedule a demo?", "tone": "professional"},
    )

    assert response.status_code == 200
    assert "suggested_reply" in response.json()
    assert "pricing" in response.json()["suggested_reply"].lower()


def test_ai_request_is_blocked_when_monthly_limit_is_reached(client: TestClient, db_session: Session) -> None:
    registered = register_user(client, email="limited@example.com")
    token = registered["access_token"]
    membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(registered["user"]["id"]))
    )
    assert membership is not None
    db_session.add(
        AIUsageEvent(
            owner_id=membership.user_id,
            organization_id=membership.organization_id,
            model_used="gpt-4.1",
            input_tokens=1,
            output_tokens=1,
            estimated_cost=5.00,
            endpoint_used="/ai/analyze-lead",
        )
    )
    db_session.commit()

    response = client.post(
        "/ai/analyze-lead",
        headers=auth_headers(token),
        json={"message": "Hi, can you send pricing and schedule a demo next week?"},
    )

    assert response.status_code == 402
    assert response.json()["detail"]["message"] == "AI monthly usage limit reached"
