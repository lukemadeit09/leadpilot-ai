from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import stripe
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Organization, PlanType, SubscriptionStatus, User


class StripeBillingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.stripe_secret_key:
            stripe.api_key = self.settings.stripe_secret_key

    def create_checkout_session(self, db: Session, organization: Organization, user: User, plan: PlanType) -> dict[str, str]:
        self._require_configured()
        price_id = self._price_id_for_plan(plan)
        customer_id = self._ensure_customer(db, organization, user)
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{self.settings.frontend_url.rstrip('/')}/settings?billing=success",
            cancel_url=f"{self.settings.frontend_url.rstrip('/')}/settings?billing=cancelled",
            metadata={"organization_id": str(organization.id), "plan": plan.value, "user_id": str(user.id)},
            subscription_data={"metadata": {"organization_id": str(organization.id), "plan": plan.value}},
        )
        return {"checkout_url": self._attr(session, "url"), "session_id": self._attr(session, "id")}

    def create_billing_portal_session(self, organization: Organization) -> dict[str, str]:
        self._require_configured()
        if not organization.stripe_customer_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No Stripe customer exists for this organization")
        session = stripe.billing_portal.Session.create(
            customer=organization.stripe_customer_id,
            return_url=f"{self.settings.frontend_url.rstrip('/')}/settings",
        )
        return {"portal_url": self._attr(session, "url")}

    def construct_webhook_event(self, payload: bytes, signature: str | None) -> Any:
        if not self.settings.stripe_webhook_secret:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe webhook secret is not configured")
        try:
            return stripe.Webhook.construct_event(payload, signature, self.settings.stripe_webhook_secret)
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid Stripe webhook signature") from exc

    def handle_webhook_event(self, db: Session, event: Any) -> dict[str, str]:
        event_type = self._attr(event, "type")
        data_object = self._attr(self._attr(event, "data"), "object")

        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(db, data_object)
        elif event_type in {"customer.subscription.created", "customer.subscription.updated"}:
            self._handle_subscription_updated(db, data_object)
        elif event_type == "customer.subscription.deleted":
            self._handle_subscription_deleted(db, data_object)

        return {"status": "processed"}

    def _ensure_customer(self, db: Session, organization: Organization, user: User) -> str:
        if organization.stripe_customer_id:
            return organization.stripe_customer_id

        customer = stripe.Customer.create(
            email=user.email,
            name=organization.name,
            metadata={"organization_id": str(organization.id), "user_id": str(user.id)},
        )
        customer_id = self._attr(customer, "id")
        organization.stripe_customer_id = customer_id
        user.stripe_customer_id = customer_id
        db.commit()
        db.refresh(organization)
        db.refresh(user)
        return customer_id

    def _handle_checkout_completed(self, db: Session, session: Any) -> None:
        organization_id = self._organization_id_from_metadata(session)
        organization = db.get(Organization, organization_id)
        if not organization:
            return

        organization.stripe_customer_id = self._attr(session, "customer") or organization.stripe_customer_id
        organization.stripe_subscription_id = self._attr(session, "subscription") or organization.stripe_subscription_id
        plan_value = self._attr(self._attr(session, "metadata"), "plan")
        if plan_value:
            organization.plan = PlanType(plan_value)
        organization.subscription_status = SubscriptionStatus.active
        db.commit()

    def _handle_subscription_updated(self, db: Session, subscription: Any) -> None:
        organization = self._organization_from_subscription(db, subscription)
        if not organization:
            return

        organization.stripe_customer_id = self._attr(subscription, "customer") or organization.stripe_customer_id
        organization.stripe_subscription_id = self._attr(subscription, "id") or organization.stripe_subscription_id
        organization.subscription_status = self._subscription_status(self._attr(subscription, "status"))
        period_end = self._attr(subscription, "current_period_end")
        organization.subscription_current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc) if period_end else None

        plan = self._plan_from_subscription(subscription)
        if plan:
            organization.plan = plan
        db.commit()

    def _handle_subscription_deleted(self, db: Session, subscription: Any) -> None:
        organization = self._organization_from_subscription(db, subscription)
        if not organization:
            return
        organization.subscription_status = SubscriptionStatus.canceled
        organization.stripe_subscription_id = self._attr(subscription, "id") or organization.stripe_subscription_id
        organization.subscription_current_period_end = None
        organization.plan = PlanType.starter
        db.commit()

    def _organization_from_subscription(self, db: Session, subscription: Any) -> Organization | None:
        metadata_org_id = self._attr(self._attr(subscription, "metadata"), "organization_id")
        if metadata_org_id:
            return db.get(Organization, UUID(str(metadata_org_id)))

        subscription_id = self._attr(subscription, "id")
        customer_id = self._attr(subscription, "customer")
        stmt = select(Organization)
        if subscription_id:
            found = db.scalar(stmt.where(Organization.stripe_subscription_id == subscription_id))
            if found:
                return found
        if customer_id:
            return db.scalar(stmt.where(Organization.stripe_customer_id == customer_id))
        return None

    def _organization_id_from_metadata(self, obj: Any) -> UUID:
        organization_id = self._attr(self._attr(obj, "metadata"), "organization_id")
        if not organization_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stripe event is missing organization metadata")
        return UUID(str(organization_id))

    def _plan_from_subscription(self, subscription: Any) -> PlanType | None:
        price_id = None
        items = self._attr(self._attr(subscription, "items"), "data") or []
        if items:
            price_id = self._attr(self._attr(items[0], "price"), "id")
        return self._plan_from_price_id(price_id) if price_id else None

    def _price_id_for_plan(self, plan: PlanType) -> str:
        price_ids = {
            PlanType.starter: self.settings.stripe_starter_price_id,
            PlanType.pro: self.settings.stripe_pro_price_id,
            PlanType.agency: self.settings.stripe_agency_price_id,
        }
        price_id = price_ids[plan]
        if not price_id:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Stripe price id is not configured for {plan.value}")
        return price_id

    def _plan_from_price_id(self, price_id: str | None) -> PlanType | None:
        if not price_id:
            return None
        price_to_plan = {
            self.settings.stripe_starter_price_id: PlanType.starter,
            self.settings.stripe_pro_price_id: PlanType.pro,
            self.settings.stripe_agency_price_id: PlanType.agency,
        }
        return price_to_plan.get(price_id)

    def _require_configured(self) -> None:
        if not self.settings.stripe_secret_key:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe secret key is not configured")

    @staticmethod
    def _subscription_status(value: str | None) -> SubscriptionStatus:
        if not value:
            return SubscriptionStatus.inactive
        try:
            return SubscriptionStatus(value)
        except ValueError:
            return SubscriptionStatus.inactive

    @staticmethod
    def _attr(obj: Any, key: str) -> Any:
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)
