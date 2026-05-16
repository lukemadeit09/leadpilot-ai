from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_ai_workflow_fallback_creates_lead_analysis_task_and_activity(client: TestClient) -> None:
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
