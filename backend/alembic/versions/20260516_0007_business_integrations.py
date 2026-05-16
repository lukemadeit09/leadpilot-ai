"""business integrations

Revision ID: 20260516_0007
Revises: 20260516_0006
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0007"
down_revision: Union[str, None] = "20260516_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("organizations", sa.Column("widget_enabled", sa.Boolean(), server_default=sa.true(), nullable=False))
    op.add_column("organizations", sa.Column("widget_title", sa.String(length=120), server_default="Talk to sales", nullable=False))
    op.add_column("organizations", sa.Column("widget_accent_color", sa.String(length=20), server_default="#34d399", nullable=False))

    op.create_table(
        "integration_usage_events",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("api_key_id", uuid_type, sa.ForeignKey("organization_api_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("endpoint", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_integration_usage_events_organization_id", "integration_usage_events", ["organization_id"], unique=False)
    op.create_index("ix_integration_usage_events_api_key_id", "integration_usage_events", ["api_key_id"], unique=False)
    op.create_index("ix_integration_usage_events_endpoint", "integration_usage_events", ["endpoint"], unique=False)
    op.create_index("ix_integration_usage_events_event_type", "integration_usage_events", ["event_type"], unique=False)
    op.create_index("ix_integration_usage_events_created_at", "integration_usage_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_integration_usage_events_created_at", table_name="integration_usage_events")
    op.drop_index("ix_integration_usage_events_event_type", table_name="integration_usage_events")
    op.drop_index("ix_integration_usage_events_endpoint", table_name="integration_usage_events")
    op.drop_index("ix_integration_usage_events_api_key_id", table_name="integration_usage_events")
    op.drop_index("ix_integration_usage_events_organization_id", table_name="integration_usage_events")
    op.drop_table("integration_usage_events")

    op.drop_column("organizations", "widget_accent_color")
    op.drop_column("organizations", "widget_title")
    op.drop_column("organizations", "widget_enabled")
