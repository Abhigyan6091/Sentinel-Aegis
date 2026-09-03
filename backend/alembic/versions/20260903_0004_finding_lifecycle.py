"""finding lifecycle, evidence, and remediation tracking

Revision ID: 20260903_0004
Revises: 20260903_0003
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0004"
down_revision: str | None = "20260903_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_NEW_COLUMNS = (
    sa.Column("campaign_id", sa.String(length=64), nullable=True),
    sa.Column("impact", sa.Text(), nullable=True),
    sa.Column("root_cause", sa.Text(), nullable=True),
    sa.Column("evidence", sa.JSON(), nullable=False, server_default="{}"),
    sa.Column("reproduction_steps", sa.JSON(), nullable=False, server_default="[]"),
    sa.Column("remediation", sa.Text(), nullable=True),
    sa.Column("regression_case_id", sa.String(length=64), nullable=True),
    sa.Column("decided_by", sa.String(length=64), nullable=True),
    sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
)


def upgrade() -> None:
    for column in _NEW_COLUMNS:
        op.add_column("findings", column)
    op.create_index("ix_findings_tenant_status", "findings", ["tenant_id", "status"])
    op.create_index("ix_findings_campaign_id", "findings", ["campaign_id"])


def downgrade() -> None:
    op.drop_index("ix_findings_campaign_id", table_name="findings")
    op.drop_index("ix_findings_tenant_status", table_name="findings")
    for column in reversed(_NEW_COLUMNS):
        op.drop_column("findings", column.name)
