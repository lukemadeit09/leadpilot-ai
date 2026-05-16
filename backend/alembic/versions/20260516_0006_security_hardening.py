"""security hardening

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

uuid_type = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column("users", sa.Column("failed_login_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("users", sa.Column("last_failed_login_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "security_audit_logs",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("owner_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_security_audit_logs_owner_id", "security_audit_logs", ["owner_id"], unique=False)
    op.create_index("ix_security_audit_logs_organization_id", "security_audit_logs", ["organization_id"], unique=False)
    op.create_index("ix_security_audit_logs_action", "security_audit_logs", ["action"], unique=False)
    op.create_index("ix_security_audit_logs_created_at", "security_audit_logs", ["created_at"], unique=False)

    op.create_table(
        "organization_api_keys",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("organization_id", uuid_type, sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=24), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_organization_api_keys_organization_id", "organization_api_keys", ["organization_id"], unique=False)
    op.create_index("ix_organization_api_keys_created_by_id", "organization_api_keys", ["created_by_id"], unique=False)
    op.create_index("ix_organization_api_keys_key_prefix", "organization_api_keys", ["key_prefix"], unique=False)
    op.create_index("ix_organization_api_keys_key_hash", "organization_api_keys", ["key_hash"], unique=True)
    op.create_index("ix_organization_api_keys_revoked_at", "organization_api_keys", ["revoked_at"], unique=False)
    op.create_index("ix_organization_api_keys_created_at", "organization_api_keys", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_organization_api_keys_created_at", table_name="organization_api_keys")
    op.drop_index("ix_organization_api_keys_revoked_at", table_name="organization_api_keys")
    op.drop_index("ix_organization_api_keys_key_hash", table_name="organization_api_keys")
    op.drop_index("ix_organization_api_keys_key_prefix", table_name="organization_api_keys")
    op.drop_index("ix_organization_api_keys_created_by_id", table_name="organization_api_keys")
    op.drop_index("ix_organization_api_keys_organization_id", table_name="organization_api_keys")
    op.drop_table("organization_api_keys")

    op.drop_index("ix_security_audit_logs_created_at", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_action", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_organization_id", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_owner_id", table_name="security_audit_logs")
    op.drop_table("security_audit_logs")

    op.drop_column("users", "locked_until")
    op.drop_column("users", "last_failed_login_at")
    op.drop_column("users", "failed_login_count")
