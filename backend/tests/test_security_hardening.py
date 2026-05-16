from io import BytesIO
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import OrganizationAPIKey, OrganizationMember, OrganizationRole, SecurityAuditLog, User
from app.services.api_keys import OrganizationAPIKeyService
from tests.conftest import auth_headers, register_user


def test_auth_rate_limit_blocks_repeated_login_attempts(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_MINUTE", "1")
    get_settings.cache_clear()

    first = client.post("/auth/login", json={"email": "missing@example.com", "password": "wrong-password"})
    second = client.post("/auth/login", json={"email": "missing@example.com", "password": "wrong-password"})

    assert first.status_code == 401
    assert second.status_code == 429


def test_failed_login_tracking_and_lockout(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAILED_LOGIN_LOCK_THRESHOLD", "2")
    get_settings.cache_clear()
    register_user(client, email="lockout@example.com")

    first = client.post("/auth/login", json={"email": "lockout@example.com", "password": "bad-password"})
    second = client.post("/auth/login", json={"email": "lockout@example.com", "password": "bad-password"})
    locked = client.post("/auth/login", json={"email": "lockout@example.com", "password": "password123"})

    assert first.status_code == 401
    assert second.status_code == 401
    assert locked.status_code == 423
    user = db_session.scalar(select(User).where(User.email == "lockout@example.com"))
    assert user is not None
    assert user.failed_login_count == 2
    assert user.locked_until is not None
    audit_count = db_session.scalar(select(func.count()).select_from(SecurityAuditLog).where(SecurityAuditLog.action == "login_failed"))
    assert audit_count == 2


def test_security_headers_are_applied(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_upload_rejects_unsupported_content_type(client: TestClient) -> None:
    token = register_user(client, email="upload-type@example.com")["access_token"]

    response = client.post(
        "/knowledge/upload",
        headers=auth_headers(token),
        files={"file": ("malware.exe", BytesIO(b"not allowed"), "application/x-msdownload")},
    )

    assert response.status_code == 400


def test_upload_rejects_oversized_file(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "8")
    get_settings.cache_clear()
    token = register_user(client, email="upload-size@example.com")["access_token"]

    response = client.post(
        "/knowledge/upload",
        headers=auth_headers(token),
        files={"file": ("large.txt", BytesIO(b"this file is too large"), "text/plain")},
    )

    assert response.status_code == 400
    assert "exceeds" in response.json()["detail"]


def test_org_api_key_is_returned_once_and_stored_hashed(client: TestClient, db_session: Session) -> None:
    registered = register_user(client, email="api-key-owner@example.com")

    response = client.post(
        "/integrations/api-keys",
        headers=auth_headers(registered["access_token"]),
        json={"name": "Website form"},
    )

    assert response.status_code == 201, response.text
    raw_key = response.json()["api_key"]
    stored = db_session.scalar(select(OrganizationAPIKey).where(OrganizationAPIKey.id == UUID(response.json()["id"])))
    assert stored is not None
    assert stored.key_hash == OrganizationAPIKeyService.hash_key(raw_key)
    assert raw_key not in stored.key_hash
    listed = client.get("/integrations/api-keys", headers=auth_headers(registered["access_token"]))
    assert listed.status_code == 200
    assert "api_key" not in listed.json()[0]


def test_public_lead_intake_uses_api_key_org_scope(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="public-owner@example.com")
    other = register_user(client, email="public-other@example.com")
    key_response = client.post(
        "/integrations/api-keys",
        headers=auth_headers(owner["access_token"]),
        json={"name": "Landing page"},
    )
    api_key = key_response.json()["api_key"]

    created = client.post(
        "/integrations/public/leads",
        headers={"X-LeadPilot-Key": api_key},
        json={"name": "Buyer", "email": "buyer@example.com", "company": "Acme", "message": "We need pricing next week."},
    )

    assert created.status_code == 201, created.text
    owner_leads = client.get("/leads", headers=auth_headers(owner["access_token"]))
    other_leads = client.get("/leads", headers=auth_headers(other["access_token"]))
    assert len(owner_leads.json()) == 1
    assert len(other_leads.json()) == 0


def test_member_cannot_create_org_api_key(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="key-owner@example.com")
    member = register_user(client, email="key-member@example.com")
    owner_membership = db_session.scalar(select(OrganizationMember).where(OrganizationMember.user_id == UUID(owner["user"]["id"])))
    member_membership = db_session.scalar(select(OrganizationMember).where(OrganizationMember.user_id == UUID(member["user"]["id"])))
    assert owner_membership is not None
    assert member_membership is not None
    member_membership.organization_id = owner_membership.organization_id
    member_membership.role = OrganizationRole.member
    db_session.commit()

    response = client.post(
        "/integrations/api-keys",
        headers=auth_headers(member["access_token"]),
        json={"name": "Blocked key"},
    )

    assert response.status_code == 403
