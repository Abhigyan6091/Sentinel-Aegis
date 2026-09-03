"""foundation schema

Revision ID: 20260903_0001
Revises:
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260903_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    ]


def tenant_column() -> sa.Column:
    return sa.Column("tenant_id", sa.String(length=64), nullable=False)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        *timestamps(),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_applications_tenant_id", "applications", ["tenant_id"])
    op.create_index("ix_applications_tenant_name", "applications", ["tenant_id", "name"])
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])
    op.create_index("ix_projects_tenant_name", "projects", ["tenant_id", "name"])
    op.create_table(
        "policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("document", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_policies_tenant_id", "policies", ["tenant_id"])
    op.create_table(
        "guardrails",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_guardrails_tenant_id", "guardrails", ["tenant_id"])
    op.create_table(
        "attack_campaigns",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_attack_campaigns_tenant_id", "attack_campaigns", ["tenant_id"])
    op.create_table(
        "attacks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("expected_behavior", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_attacks_tenant_id", "attacks", ["tenant_id"])
    op.create_table(
        "attack_variants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("attack_id", sa.String(length=64), sa.ForeignKey("attacks.id")),
        sa.Column("parent_attack_id", sa.String(length=64), nullable=True),
        sa.Column("mutation_strategy", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_attack_variants_tenant_id", "attack_variants", ["tenant_id"])
    op.create_table(
        "attack_results",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("campaign_id", sa.String(length=64), sa.ForeignKey("attack_campaigns.id")),
        sa.Column("attack_id", sa.String(length=64), sa.ForeignKey("attacks.id")),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("result", sa.String(length=64), nullable=False),
        sa.Column("signals", sa.JSON(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_attack_results_tenant_id", "attack_results", ["tenant_id"])
    op.create_table(
        "findings",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("attack_id", sa.String(length=64), sa.ForeignKey("attacks.id")),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("affected_component", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_findings_tenant_id", "findings", ["tenant_id"])
    op.create_table(
        "traces",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("attack_id", sa.String(length=64), sa.ForeignKey("attacks.id")),
        sa.Column("spans", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_traces_tenant_id", "traces", ["tenant_id"])
    op.create_index("ix_traces_request_id", "traces", ["request_id"])
    op.create_table(
        "tool_calls",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("tool_name", sa.String(length=128), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("risk", sa.String(length=32), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_tool_calls_tenant_id", "tool_calls", ["tenant_id"])
    op.create_index("ix_tool_calls_request_id", "tool_calls", ["request_id"])
    op.create_table(
        "security_events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_security_events_tenant_id", "security_events", ["tenant_id"])
    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        tenant_column(),
        sa.Column("application_id", sa.String(length=64), sa.ForeignKey("applications.id")),
        sa.Column("campaign_id", sa.String(length=64), sa.ForeignKey("attack_campaigns.id")),
        sa.Column("mode", sa.String(length=64), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_evaluation_runs_tenant_id", "evaluation_runs", ["tenant_id"])


def downgrade() -> None:
    for table_name in (
        "evaluation_runs",
        "security_events",
        "tool_calls",
        "traces",
        "findings",
        "attack_results",
        "attack_variants",
        "attacks",
        "attack_campaigns",
        "guardrails",
        "policies",
        "projects",
        "applications",
        "users",
        "tenants",
    ):
        op.drop_table(table_name)
