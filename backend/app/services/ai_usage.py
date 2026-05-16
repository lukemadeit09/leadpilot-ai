from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIUsageEvent, Organization, OrganizationMember, PlanType


PLAN_LABELS: dict[PlanType, str] = {
    PlanType.starter: "Starter",
    PlanType.pro: "Pro",
    PlanType.agency: "Agency",
}

PLAN_MONTHLY_LIMITS: dict[PlanType, Decimal] = {
    PlanType.starter: Decimal("5.00"),
    PlanType.pro: Decimal("50.00"),
    PlanType.agency: Decimal("250.00"),
}

PLAN_INCLUDED_SEATS: dict[PlanType, int] = {
    PlanType.starter: 1,
    PlanType.pro: 5,
    PlanType.agency: 20,
}

MODEL_PRICING_PER_1M_TOKENS: dict[str, tuple[Decimal, Decimal]] = {
    "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
    "gpt-4.1": (Decimal("2.00"), Decimal("8.00")),
}


class AIUsageService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def model_for(self, complexity: str) -> str:
        if complexity == "complex":
            return self.settings.openai_complex_model
        return self.settings.openai_simple_model

    def ensure_within_limit(
        self,
        db: Session,
        membership: OrganizationMember,
        endpoint_used: str,
        prompt: str,
        model_used: str,
        output_token_budget: int,
    ) -> None:
        organization = db.get(Organization, membership.organization_id)
        if not organization:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No organization access")

        input_tokens = self.estimate_tokens(prompt)
        projected_cost = self.estimate_cost(model_used, input_tokens, output_token_budget)
        monthly_total = self.monthly_total(db, membership.organization_id)
        plan = PlanType(organization.plan)
        monthly_limit = PLAN_MONTHLY_LIMITS[plan]

        if monthly_total + projected_cost > monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": "AI monthly usage limit reached",
                    "plan": plan.value,
                    "monthly_limit": float(monthly_limit),
                    "current_usage": float(monthly_total),
                    "endpoint": endpoint_used,
                },
            )

    def record_usage(
        self,
        db: Session,
        owner_id: UUID,
        organization_id: UUID,
        endpoint_used: str,
        model_used: str,
        input_text: str,
        output_text: str,
    ) -> AIUsageEvent:
        input_tokens = self.estimate_tokens(input_text)
        output_tokens = self.estimate_tokens(output_text)
        usage = AIUsageEvent(
            owner_id=owner_id,
            organization_id=organization_id,
            model_used=model_used,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=float(self.estimate_cost(model_used, input_tokens, output_tokens)),
            endpoint_used=endpoint_used,
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
        return usage

    def monthly_total(self, db: Session, organization_id: UUID) -> Decimal:
        return self._monthly_total(db, organization_id=organization_id)

    def usage_summary(self, db: Session, organization: Organization, user_id: UUID) -> dict:
        plan = PlanType(organization.plan)
        month_start = self.month_start()
        organization_used = self._monthly_total(db, organization_id=organization.id)
        user_used = self._monthly_total(db, organization_id=organization.id, owner_id=user_id)
        monthly_limit = PLAN_MONTHLY_LIMITS[plan]
        requests = (
            db.scalar(
                select(func.count())
                .select_from(AIUsageEvent)
                .where(AIUsageEvent.organization_id == organization.id, AIUsageEvent.created_at >= month_start)
            )
            or 0
        )
        tokens = (
            db.scalar(
                select(func.coalesce(func.sum(AIUsageEvent.input_tokens + AIUsageEvent.output_tokens), 0)).where(
                    AIUsageEvent.organization_id == organization.id,
                    AIUsageEvent.created_at >= month_start,
                )
            )
            or 0
        )
        remaining = max(Decimal("0"), monthly_limit - organization_used)
        usage_percent = Decimal("0") if monthly_limit == 0 else min(Decimal("100"), (organization_used / monthly_limit) * Decimal("100"))
        return {
            "organization_id": organization.id,
            "plan": plan.value,
            "plan_label": PLAN_LABELS[plan],
            "subscription_status": organization.subscription_status.value,
            "subscription_current_period_end": organization.subscription_current_period_end,
            "monthly_limit": float(monthly_limit),
            "organization_used": float(organization_used),
            "user_used": float(user_used),
            "remaining": float(remaining),
            "usage_percent": float(usage_percent.quantize(Decimal("0.01"))),
            "requests": int(requests),
            "tokens": int(tokens),
            "month_start": month_start,
        }

    def plan_catalog(self) -> list[dict]:
        return [
            {
                "plan": plan.value,
                "label": PLAN_LABELS[plan],
                "monthly_limit": float(PLAN_MONTHLY_LIMITS[plan]),
                "included_seats": PLAN_INCLUDED_SEATS[plan],
            }
            for plan in PlanType
        ]

    @staticmethod
    def month_start() -> datetime:
        return datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    def _monthly_total(self, db: Session, organization_id: UUID, owner_id: UUID | None = None) -> Decimal:
        month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        stmt = select(func.coalesce(func.sum(AIUsageEvent.estimated_cost), 0)).where(
            AIUsageEvent.organization_id == organization_id,
            AIUsageEvent.created_at >= month_start,
        )
        if owner_id:
            stmt = stmt.where(AIUsageEvent.owner_id == owner_id)
        total = db.scalar(stmt)
        return Decimal(str(total or 0))

    @staticmethod
    def estimate_tokens(text: str) -> int:
        return max(1, len(text) // 4)

    @staticmethod
    def estimate_cost(model_used: str, input_tokens: int, output_tokens: int) -> Decimal:
        input_rate, output_rate = MODEL_PRICING_PER_1M_TOKENS.get(
            model_used,
            MODEL_PRICING_PER_1M_TOKENS["gpt-4.1-mini"],
        )
        input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * input_rate
        output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * output_rate
        return (input_cost + output_cost).quantize(Decimal("0.000001"))
