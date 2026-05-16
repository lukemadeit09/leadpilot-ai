"""rag pgvector knowledge base

Revision ID: 20260516_0005
Revises: 20260516_0004
Create Date: 2026-05-16 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260516_0005"
down_revision: Union[str, None] = "20260516_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

document_status = postgresql.ENUM("pending", "processing", "ready", "failed", name="documentstatus")
document_status_column = postgresql.ENUM("pending", "processing", "ready", "failed", name="documentstatus", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    document_status.create(bind, checkfirst=True)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("uploaded_documents", sa.Column("status", document_status_column, server_default="pending", nullable=False))
    op.add_column("uploaded_documents", sa.Column("processing_error", sa.Text(), nullable=True))
    op.add_column("uploaded_documents", sa.Column("chunk_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("uploaded_documents", sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_uploaded_documents_status", "uploaded_documents", ["status"], unique=False)

    op.add_column("knowledge_chunks", sa.Column("source_page", sa.Integer(), nullable=True))
    op.add_column("knowledge_chunks", sa.Column("token_count", sa.Integer(), server_default="0", nullable=False))
    op.add_column("knowledge_chunks", sa.Column("embedding_model", sa.String(length=120), nullable=True))
    op.execute("ALTER TABLE knowledge_chunks ADD COLUMN IF NOT EXISTS embedding_vector vector(1536)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_vector "
        "ON knowledge_chunks USING ivfflat (embedding_vector vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_vector")
    op.execute("ALTER TABLE knowledge_chunks DROP COLUMN IF EXISTS embedding_vector")
    op.drop_column("knowledge_chunks", "embedding_model")
    op.drop_column("knowledge_chunks", "token_count")
    op.drop_column("knowledge_chunks", "source_page")
    op.drop_index("ix_uploaded_documents_status", table_name="uploaded_documents")
    op.drop_column("uploaded_documents", "processed_at")
    op.drop_column("uploaded_documents", "chunk_count")
    op.drop_column("uploaded_documents", "processing_error")
    op.drop_column("uploaded_documents", "status")
    document_status.drop(op.get_bind(), checkfirst=True)
