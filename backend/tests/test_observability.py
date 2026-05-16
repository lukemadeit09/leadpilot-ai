from fastapi.testclient import TestClient


def test_health_live_and_ready_endpoints(client: TestClient) -> None:
    health = client.get("/health")
    live = client.get("/live")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["service"] == "leadpilot-api"
    assert live.status_code == 200
    assert live.json()["status"] == "ok"
    assert "checked_at" in live.json()
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok", "checks": {"database": "ok"}}


def test_request_logging_adds_request_id_header_safely(client: TestClient) -> None:
    response = client.get("/health", headers={"Authorization": "Bearer should-not-be-logged", "X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-id"
