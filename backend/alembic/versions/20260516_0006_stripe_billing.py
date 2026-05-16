"""stripe billing subscriptions

Revision ID: 20260516_0006
Revises: 20260516_0005
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0006"
down_revision: Union[str, None] = "20260516_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

subscription_status = postgresql.ENUM("inactive", "trialing", "active", "past_due", "canceled", "unpaid", name="subscriptionstatus")
subscription_status_column = postgresql.ENUM(
    "inactive",
    "trialing",
    "active",
    "past_due",
    "canceled",
    "unpaid",
    name="subscriptionstatus",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    subscription_status.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.create_index("ix_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=False)

    op.add_column("organizations", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column("organizations", sa.Column("stripe_subscription_id", sa.String(length=255), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("subscription_status", subscription_status_column, server_default="inactive", nullable=False),
    )
    op.add_column("organizations", sa.Column("subscription_current_period_end", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_organizations_stripe_customer_id", "organizations", ["stripe_customer_id"], unique=False)
    op.create_index("ix_organizations_stripe_subscription_id", "organizations", ["stripe_subscription_id"], unique=False)
    op.create_index("ix_organizations_subscription_status", "organizations", ["subscription_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_organizations_subscription_status", table_name="organizations")
    op.drop_index("ix_organizations_stripe_subscription_id", table_name="organizations")
    op.drop_index("ix_organizations_stripe_customer_id", table_name="organizations")
    op.drop_column("organizations", "subscription_current_period_end")
    op.drop_column("organizations", "subscription_status")
    op.drop_column("organizations", "stripe_subscription_id")
    op.drop_column("organizations", "stripe_customer_id")

    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "stripe_customer_id")

    subscription_status.drop(op.get_bind(), checkfirst=True)
