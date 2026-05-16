from fastapi.testclient import TestClient

from tests.conftest import auth_headers, register_user


def test_register_login_and_me(client: TestClient) -> None:
    created = register_user(client, email="rep@example.com")

    assert created["token_type"] == "bearer"
    assert created["access_token"]
    assert created["user"]["email"] == "rep@example.com"

    login = client.post("/auth/login", json={"email": "rep@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["email"] == "rep@example.com"


def test_duplicate_registration_is_rejected(client: TestClient) -> None:
    register_user(client, email="duplicate@example.com")

    response = client.post(
        "/auth/register",
        json={"email": "duplicate@example.com", "full_name": "Duplicate User", "password": "password123"},
    )

    assert response.status_code == 409


def test_invalid_login_is_rejected(client: TestClient) -> None:
    register_user(client, email="wrong-login@example.com")

    response = client.post("/auth/login", json={"email": "wrong-login@example.com", "password": "not-the-password"})

    assert response.status_code == 401


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
