"""policy versions and approval queue

Revision ID: 20260903_0003
Revises: 20260903_0002
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0003"
down_revision: str | None = "20260903_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def upgrade() -> None:
    op.add_column(
        "policies",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_table(
        "approval_requests",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("risk", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=True),
        sa.Column("decided_by", sa.String(length=64), nullable=True),
        *timestamps(),
    )
    op.create_index("ix_approval_requests_tenant_id", "approval_requests", ["tenant_id"])
    op.create_index("ix_approval_requests_request_id", "approval_requests", ["request_id"])
    op.create_index(
        "ix_approval_requests_tenant_status",
        "approval_requests",
        ["tenant_id", "status"],
    )


def downgrade() -> None:
    op.drop_table("approval_requests")
    op.drop_column("policies", "version")
