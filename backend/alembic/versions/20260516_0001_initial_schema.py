"""initial schema

Revision ID: 20260516_0001
Revises:
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

lead_status = postgresql.ENUM("new", "analyzed", "qualified", "contacted", "follow_up", "closed_won", "closed_lost", name="leadstatus")
task_status = postgresql.ENUM("pending", "in_progress", "completed", "cancelled", name="taskstatus")
task_priority = postgresql.ENUM("low", "medium", "high", "urgent", name="taskpriority")
lead_status_column = postgresql.ENUM(
    "new", "analyzed", "qualified", "contacted", "follow_up", "closed_won", "closed_lost", name="leadstatus", create_type=False
)
task_status_column = postgresql.ENUM("pending", "in_progress", "completed", "cancelled", name="taskstatus", create_type=False)
task_priority_column = postgresql.ENUM("low", "medium", "high", "urgent", name="taskpriority", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    lead_status.create(bind, checkfirst=True)
    task_status.create(bind, checkfirst=True)
    task_priority.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", lead_status_column, nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column("urgency", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_leads_email", "leads", ["email"], unique=False)
    op.create_index("ix_leads_status", "leads", ["status"], unique=False)

    op.create_table(
        "activity_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"], unique=False)

    op.create_table(
        "lead_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("sentiment", sa.String(length=50), nullable=False),
        sa.Column("urgency", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("lead_score", sa.Integer(), nullable=False),
        sa.Column("pain_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("buying_intent", sa.String(length=80), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("suggested_reply", sa.Text(), nullable=False),
        sa.Column("follow_up_task", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", task_status_column, nullable=False),
        sa.Column("priority", task_priority_column, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tasks_priority", "tasks", ["priority"], unique=False)
    op.create_index("ix_tasks_status", "tasks", ["status"], unique=False)

    op.create_table(
        "uploaded_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["uploaded_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("uploaded_documents")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_priority", table_name="tasks")
    op.drop_table("tasks")
    op.drop_table("lead_analyses")
    op.drop_index("ix_activity_logs_created_at", table_name="activity_logs")
    op.drop_table("activity_logs")
    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_email", table_name="leads")
    op.drop_table("leads")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    task_priority.drop(op.get_bind(), checkfirst=True)
    task_status.drop(op.get_bind(), checkfirst=True)
    lead_status.drop(op.get_bind(), checkfirst=True)
