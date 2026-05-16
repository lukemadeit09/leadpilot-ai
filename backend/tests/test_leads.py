from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def create_lead(client: TestClient, token: str, email: str = "lead@example.com") -> dict:
    response = client.post(
        "/leads",
        headers=auth_headers(token),
        json={
            "name": "Jordan Lee",
            "email": email,
            "company": "Acme Ops",
            "message": "Interested in pricing and a demo next week.",
            "status": "new",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_leads_crud_lifecycle(client: TestClient) -> None:
    token = register_user(client)["access_token"]

    lead = create_lead(client, token)
    assert lead["status"] == "new"
    assert lead["score"] == 0

    listed = client.get("/leads", headers=auth_headers(token))
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    fetched = client.get(f"/leads/{lead['id']}", headers=auth_headers(token))
    assert fetched.status_code == 200
    assert fetched.json()["company"] == "Acme Ops"

    patched = client.patch(
        f"/leads/{lead['id']}",
        headers=auth_headers(token),
        json={"status": "qualified", "score": 88, "sentiment": "positive", "urgency": "high"},
    )
    assert patched.status_code == 200
    assert patched.json()["status"] == "qualified"
    assert patched.json()["score"] == 88

    deleted = client.delete(f"/leads/{lead['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204

    missing = client.get(f"/leads/{lead['id']}", headers=auth_headers(token))
    assert missing.status_code == 404


def test_lead_search_filters_current_users_data(client: TestClient) -> None:
    token = register_user(client)["access_token"]
    create_lead(client, token, email="pricing@example.com")

    found = client.get("/leads?search=pricing", headers=auth_headers(token))
    assert found.status_code == 200
    assert len(found.json()) == 1

    not_found = client.get("/leads?search=not-present", headers=auth_headers(token))
    assert not_found.status_code == 200
    assert not_found.json() == []
