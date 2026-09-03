"""rag documents and chunks

Revision ID: 20260903_0002
Revises: 20260903_0001
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0002"
down_revision: str | None = "20260903_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("sensitivity", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_rag_documents_tenant_id", "rag_documents", ["tenant_id"])
    op.create_index("ix_rag_documents_tenant_source", "rag_documents", ["tenant_id", "source"])

    op.create_table(
        "rag_chunks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.String(length=64), sa.ForeignKey("rag_documents.id")),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("trust_score", sa.Float(), nullable=False),
        sa.Column("sensitivity", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_rag_chunks_tenant_id", "rag_chunks", ["tenant_id"])
    op.create_index("ix_rag_chunks_tenant_document", "rag_chunks", ["tenant_id", "document_id"])


def downgrade() -> None:
    op.drop_table("rag_chunks")
    op.drop_table("rag_documents")
