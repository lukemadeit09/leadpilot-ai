"""ai background jobs

Revision ID: 20260516_0004
Revises: 20260516_0003
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0004"
down_revision: Union[str, None] = "20260516_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ai_job_status = postgresql.ENUM("queued", "running", "succeeded", "failed", name="aijobstatus")
ai_job_status_column = postgresql.ENUM("queued", "running", "succeeded", "failed", name="aijobstatus", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    ai_job_status.create(bind, checkfirst=True)

    op.create_table(
        "ai_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("celery_task_id", sa.String(length=255), nullable=True),
        sa.Column("status", ai_job_status_column, nullable=False),
        sa.Column("endpoint_used", sa.String(length=120), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_jobs_celery_task_id", "ai_jobs", ["celery_task_id"], unique=False)
    op.create_index("ix_ai_jobs_created_at", "ai_jobs", ["created_at"], unique=False)
    op.create_index("ix_ai_jobs_endpoint_used", "ai_jobs", ["endpoint_used"], unique=False)
    op.create_index("ix_ai_jobs_organization_id", "ai_jobs", ["organization_id"], unique=False)
    op.create_index("ix_ai_jobs_owner_id", "ai_jobs", ["owner_id"], unique=False)
    op.create_index("ix_ai_jobs_status", "ai_jobs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_jobs_status", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_owner_id", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_organization_id", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_endpoint_used", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_created_at", table_name="ai_jobs")
    op.drop_index("ix_ai_jobs_celery_task_id", table_name="ai_jobs")
    op.drop_table("ai_jobs")
    ai_job_status.drop(op.get_bind(), checkfirst=True)
