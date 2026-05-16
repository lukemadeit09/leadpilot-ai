from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import OrganizationMember, OrganizationRole
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


def test_member_in_same_org_can_access_org_leads(client: TestClient, db_session: Session) -> None:
    owner = register_user(client, email="org-owner@example.com")
    member = register_user(client, email="org-member@example.com")
    owner_token = owner["access_token"]
    member_token = member["access_token"]
    owner_membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(owner["user"]["id"]))
    )
    member_membership = db_session.scalar(
        select(OrganizationMember).where(OrganizationMember.user_id == UUID(member["user"]["id"]))
    )
    assert owner_membership is not None
    assert member_membership is not None
    assert owner_membership.role == OrganizationRole.owner

    member_membership.organization_id = owner_membership.organization_id
    member_membership.role = OrganizationRole.member
    db_session.commit()

    lead = create_lead(client, owner_token, email="shared-org@example.com")
    member_read = client.get(f"/leads/{lead['id']}", headers=auth_headers(member_token))

    assert member_read.status_code == 200
    assert member_read.json()["email"] == "shared-org@example.com"


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
