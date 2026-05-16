from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Organization, OrganizationMember, OrganizationRole, PlanType, SubscriptionStatus, User
from tests.conftest import auth_headers, register_user


def configure_stripe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_local")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_local")
    monkeypatch.setenv("STRIPE_STARTER_PRICE_ID", "price_starter")
    monkeypatch.setenv("STRIPE_PRO_PRICE_ID", "price_pro")
    monkeypatch.setenv("STRIPE_AGENCY_PRICE_ID", "price_agency")
    monkeypatch.setenv("FRONTEND_URL", "http://localhost:3000")
    get_settings.cache_clear()


def organization_for_user(db_session: Session, user_id: str) -> Organization:
    membership = db_session.scalar(select(OrganizationMember).where(OrganizationMember.user_id == UUID(user_id)))
    assert membership is not None
    organization = db_session.get(Organization, membership.organization_id)
    assert organization is not None
    return organization


def test_checkout_creates_stripe_customer_and_session(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_stripe(monkeypatch)
    registered = register_user(client, email="stripe-checkout@example.com")

    monkeypatch.setattr("stripe.Customer.create", lambda **kwargs: SimpleNamespace(id="cus_123"))
    monkeypatch.setattr(
        "stripe.checkout.Session.create",
        lambda **kwargs: SimpleNamespace(id="cs_123", url="https://checkout.stripe.test/session"),
    )

    response = client.post(
        "/billing/checkout",
        headers=auth_headers(registered["access_token"]),
        json={"plan": "pro"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {"checkout_url": "https://checkout.stripe.test/session", "session_id": "cs_123"}

    organization = organization_for_user(db_session, registered["user"]["id"])
    user = db_session.get(User, UUID(registered["user"]["id"]))
    assert organization.stripe_customer_id == "cus_123"
    assert user is not None
    assert user.stripe_customer_id == "cus_123"


def test_billing_portal_requires_existing_customer(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_stripe(monkeypatch)
    registered = register_user(client, email="stripe-portal@example.com")
    organization = organization_for_user(db_session, registered["user"]["id"])
    organization.stripe_customer_id = "cus_portal"
    db_session.commit()

    monkeypatch.setattr(
        "stripe.billing_portal.Session.create",
        lambda **kwargs: SimpleNamespace(url="https://billing.stripe.test/session"),
    )

    response = client.post("/billing/portal", headers=auth_headers(registered["access_token"]))

    assert response.status_code == 200, response.text
    assert response.json() == {"portal_url": "https://billing.stripe.test/session"}


def test_webhook_updates_subscription_status_and_plan(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_stripe(monkeypatch)
    registered = register_user(client, email="stripe-webhook@example.com")
    organization = organization_for_user(db_session, registered["user"]["id"])

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "customer": "cus_123",
                "status": "active",
                "current_period_end": 1_893_456_000,
                "metadata": {"organization_id": str(organization.id)},
                "items": {"data": [{"price": {"id": "price_agency"}}]},
            }
        },
    }
    monkeypatch.setattr("stripe.Webhook.construct_event", lambda payload, signature, secret: event)

    response = client.post("/billing/webhook", headers={"Stripe-Signature": "sig"}, content=b"{}")

    assert response.status_code == 200, response.text
    db_session.refresh(organization)
    assert organization.plan == PlanType.agency
    assert organization.subscription_status == SubscriptionStatus.active
    assert organization.stripe_customer_id == "cus_123"
    assert organization.stripe_subscription_id == "sub_123"
    assert organization.subscription_current_period_end is not None


def test_checkout_completed_webhook_sets_initial_subscription_state(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_stripe(monkeypatch)
    registered = register_user(client, email="stripe-completed@example.com")
    organization = organization_for_user(db_session, registered["user"]["id"])

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_checkout",
                "subscription": "sub_checkout",
                "metadata": {"organization_id": str(organization.id), "plan": "pro"},
            }
        },
    }
    monkeypatch.setattr("stripe.Webhook.construct_event", lambda payload, signature, secret: event)

    response = client.post("/billing/webhook", headers={"Stripe-Signature": "sig"}, content=b"{}")

    assert response.status_code == 200, response.text
    db_session.refresh(organization)
    assert organization.plan == PlanType.pro
    assert organization.subscription_status == SubscriptionStatus.active
    assert organization.stripe_customer_id == "cus_checkout"
    assert organization.stripe_subscription_id == "sub_checkout"


def test_webhook_rejects_invalid_signature(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_stripe(monkeypatch)

    def raise_signature_error(payload, signature, secret):
        raise ValueError("invalid payload")

    monkeypatch.setattr("stripe.Webhook.construct_event", raise_signature_error)

    response = client.post("/billing/webhook", headers={"Stripe-Signature": "bad"}, content=b"{}")

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Stripe webhook signature"


def test_member_cannot_start_checkout(client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_stripe(monkeypatch)
    owner = register_user(client, email="stripe-owner@example.com")
    member = register_user(client, email="stripe-member@example.com")
    owner_org = organization_for_user(db_session, owner["user"]["id"])
    member_membership = db_session.scalar(select(OrganizationMember).where(OrganizationMember.user_id == UUID(member["user"]["id"])))
    assert member_membership is not None
    member_membership.organization_id = owner_org.id
    member_membership.role = OrganizationRole.member
    db_session.commit()

    response = client.post(
        "/billing/checkout",
        headers=auth_headers(member["access_token"]),
        json={"plan": "pro"},
    )

    assert response.status_code == 403
