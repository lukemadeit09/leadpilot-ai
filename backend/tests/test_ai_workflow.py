from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIJob, AIJobStatus, AIUsageEvent, OrganizationMember, OrganizationRole
from app.tasks.ai_jobs import process_analyze_lead_job
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


def test_async_ai_job_creates_result_and_can_be_polled(client: TestClient, db_session: Session) -> None:
    token = register_user(client, email="async@example.com")["access_token"]

    created = client.post(
        "/ai/analyze-lead/jobs",
        headers=auth_headers(token),
        json={
            "name": "Async Buyer",
            "email": "async-buyer@example.com",
            "company": "Queue Labs",
            "message": "We need pricing and want to schedule a demo next week.",
        },
    )

    assert created.status_code == 202, created.text
    job = created.json()
    assert job["status"] == "succeeded"
    assert job["result_payload"]["lead"]["company"] == "Queue Labs"
    assert job["attempts"] == 1

    polled = client.get(f"/ai/jobs/{job['id']}", headers=auth_headers(token))
    assert polled.status_code == 200
    assert "Queue Labs" in polled.json()["result_payload"]["task"]["title"]


def test_async_job_status_is_org_scoped(client: TestClient) -> None:
    owner = register_user(client, email="job-owner@example.com")
    other = register_user(client, email="job-other@example.com")
    created = client.post(
        "/ai/analyze-lead/jobs",
        headers=auth_headers(owner["access_token"]),
        json={"message": "Need pricing and a demo next week."},
    )
    assert created.status_code == 202

    blocked = client.get(f"/ai/jobs/{created.json()['id']}", headers=auth_headers(other["access_token"]))
    assert blocked.status_code == 404


def test_async_job_marks_failed_after_final_attempt(client: TestClient, db_session: Session, monkeypatch) -> None:
    registered = register_user(client, email="failed-job@example.com")
    membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(registered["user"]["id"]))
    )
    assert membership is not None
    job = AIJob(
        owner_id=membership.user_id,
        organization_id=membership.organization_id,
        endpoint_used="/ai/analyze-lead",
        request_payload={"message": "Need pricing."},
        max_attempts=3,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    def fail_run(*args, **kwargs):
        raise RuntimeError("model provider unavailable")

    monkeypatch.setattr("app.tasks.ai_jobs.AILeadWorkflow.run", fail_run)

    try:
        process_analyze_lead_job(db_session, job.id, retries=3, max_retries=3)
    except RuntimeError:
        pass

    failed = db_session.get(AIJob, job.id)
    assert failed is not None
    assert failed.status == AIJobStatus.failed
    assert failed.error_message == "model provider unavailable"


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


def test_billing_usage_summary_and_plan_update(client: TestClient, db_session: Session) -> None:
    registered = register_user(client, email="billing@example.com")
    token = registered["access_token"]

    usage = client.get("/billing/usage", headers=auth_headers(token))
    assert usage.status_code == 200
    assert usage.json()["plan"] == "starter"
    assert usage.json()["monthly_limit"] == 5.0
    assert usage.json()["remaining"] == 5.0

    plans = client.get("/billing/plans", headers=auth_headers(token))
    assert plans.status_code == 200
    assert [plan["plan"] for plan in plans.json()] == ["starter", "pro", "agency"]

    updated = client.patch("/billing/plan", headers=auth_headers(token), json={"plan": "pro"})
    assert updated.status_code == 200
    assert updated.json()["plan"] == "pro"
    assert updated.json()["monthly_limit"] == 50.0


def test_only_org_admin_can_update_plan(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="billing-owner@example.com")
    member = register_user(client, email="billing-member@example.com")
    owner_membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(owner["user"]["id"]))
    )
    member_membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(member["user"]["id"]))
    )
    assert owner_membership is not None
    assert member_membership is not None

    member_membership.organization_id = owner_membership.organization_id
    member_membership.role = OrganizationRole.member
    db_session.commit()

    response = client.patch(
        "/billing/plan",
        headers=auth_headers(member["access_token"]),
        json={"plan": "agency"},
    )

    assert response.status_code == 403
