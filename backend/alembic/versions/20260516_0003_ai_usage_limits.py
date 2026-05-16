"""ai usage limits

Revision ID: 20260516_0003
Revises: 20260516_0002
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0003"
down_revision: Union[str, None] = "20260516_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

plan_type = postgresql.ENUM("starter", "pro", "agency", name="plantype")
plan_type_column = postgresql.ENUM("starter", "pro", "agency", name="plantype", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    plan_type.create(bind, checkfirst=True)

    op.add_column("organizations", sa.Column("plan", plan_type_column, server_default="starter", nullable=False))
    op.create_index("ix_organizations_plan", "organizations", ["plan"], unique=False)

    op.create_table(
        "ai_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_used", sa.String(length=120), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("estimated_cost", sa.Numeric(10, 6), nullable=False),
        sa.Column("endpoint_used", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_events_created_at", "ai_usage_events", ["created_at"], unique=False)
    op.create_index("ix_ai_usage_events_endpoint_used", "ai_usage_events", ["endpoint_used"], unique=False)
    op.create_index("ix_ai_usage_events_organization_id", "ai_usage_events", ["organization_id"], unique=False)
    op.create_index("ix_ai_usage_events_owner_id", "ai_usage_events", ["owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_usage_events_owner_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_organization_id", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_endpoint_used", table_name="ai_usage_events")
    op.drop_index("ix_ai_usage_events_created_at", table_name="ai_usage_events")
    op.drop_table("ai_usage_events")
    op.drop_index("ix_organizations_plan", table_name="organizations")
    op.drop_column("organizations", "plan")
    plan_type.drop(op.get_bind(), checkfirst=True)
