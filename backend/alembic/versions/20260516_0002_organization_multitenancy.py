"""organization multi-tenancy

Revision ID: 20260516_0002
Revises: 20260516_0001
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0002"
down_revision: Union[str, None] = "20260516_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

organization_role = postgresql.ENUM("owner", "admin", "member", name="organizationrole")
organization_role_column = postgresql.ENUM("owner", "admin", "member", name="organizationrole", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    organization_role.create(bind, checkfirst=True)

    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "organization_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", organization_role_column, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_organization_members_org_user"),
    )
    op.create_index("ix_organization_members_organization_id", "organization_members", ["organization_id"], unique=False)
    op.create_index("ix_organization_members_role", "organization_members", ["role"], unique=False)
    op.create_index("ix_organization_members_user_id", "organization_members", ["user_id"], unique=False)

    for table_name in ["leads", "tasks", "activity_logs", "uploaded_documents", "knowledge_chunks"]:
        op.add_column(table_name, sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.execute(
        """
        CREATE TEMP TABLE user_org_map AS
        SELECT id AS user_id, gen_random_uuid() AS organization_id
        FROM users
        """
    )
    op.execute(
        """
        INSERT INTO organizations (id, name, created_at)
        SELECT user_org_map.organization_id, users.full_name || '''s Workspace', now()
        FROM user_org_map
        JOIN users ON users.id = user_org_map.user_id
        """
    )
    op.execute(
        """
        INSERT INTO organization_members (id, organization_id, user_id, role, created_at)
        SELECT gen_random_uuid(), organization_id, user_id, 'owner', now()
        FROM user_org_map
        """
    )
    for table_name in ["leads", "tasks", "activity_logs", "uploaded_documents"]:
        op.execute(
            f"""
            UPDATE {table_name}
            SET organization_id = user_org_map.organization_id
            FROM user_org_map
            WHERE {table_name}.owner_id = user_org_map.user_id
            """
        )
    op.execute(
        """
        UPDATE knowledge_chunks
        SET organization_id = uploaded_documents.organization_id
        FROM uploaded_documents
        WHERE knowledge_chunks.document_id = uploaded_documents.id
        """
    )

    for table_name in ["leads", "tasks", "activity_logs", "uploaded_documents", "knowledge_chunks"]:
        op.alter_column(table_name, "organization_id", nullable=False)
        op.create_index(f"ix_{table_name}_organization_id", table_name, ["organization_id"], unique=False)
        op.create_foreign_key(
            f"fk_{table_name}_organization_id_organizations",
            table_name,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    for table_name in ["knowledge_chunks", "uploaded_documents", "activity_logs", "tasks", "leads"]:
        op.drop_constraint(f"fk_{table_name}_organization_id_organizations", table_name, type_="foreignkey")
        op.drop_index(f"ix_{table_name}_organization_id", table_name=table_name)
        op.drop_column(table_name, "organization_id")

    op.drop_index("ix_organization_members_user_id", table_name="organization_members")
    op.drop_index("ix_organization_members_role", table_name="organization_members")
    op.drop_index("ix_organization_members_organization_id", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_table("organizations")
    organization_role.drop(op.get_bind(), checkfirst=True)
