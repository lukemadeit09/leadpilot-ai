from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user
from tests.test_leads import create_lead


def test_users_cannot_access_each_others_leads(client: TestClient) -> None:
    user_a = register_user(client, email="a@example.com")
    user_b = register_user(client, email="b@example.com")
    token_a = user_a["access_token"]
    token_b = user_b["access_token"]

    lead_a = create_lead(client, token_a, email="customer-a@example.com")

    list_b = client.get("/leads", headers=auth_headers(token_b))
    assert list_b.status_code == 200
    assert list_b.json() == []

    get_b = client.get(f"/leads/{lead_a['id']}", headers=auth_headers(token_b))
    assert get_b.status_code == 404

    patch_b = client.patch(f"/leads/{lead_a['id']}", headers=auth_headers(token_b), json={"status": "qualified"})
    assert patch_b.status_code == 404

    delete_b = client.delete(f"/leads/{lead_a['id']}", headers=auth_headers(token_b))
    assert delete_b.status_code == 404

    get_a = client.get(f"/leads/{lead_a['id']}", headers=auth_headers(token_a))
    assert get_a.status_code == 200


def test_unauthorized_requests_are_rejected(client: TestClient) -> None:
    protected_requests = [
        ("GET", "/leads", None),
        ("POST", "/leads", {"message": "Need a demo"}),
        ("GET", "/tasks", None),
        ("GET", "/activity", None),
        ("POST", "/ai/generate-reply", {"message": "Need pricing"}),
        ("POST", "/ai/analyze-lead", {"message": "Need pricing"}),
        ("GET", "/dashboard/metrics", None),
    ]

    for method, path, body in protected_requests:
        response = client.request(method, path, json=body)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"
