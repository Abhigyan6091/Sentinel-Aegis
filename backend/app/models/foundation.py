from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def new_id() -> str:
    return str(uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class TenantScopedMixin:
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class User(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)


class Application(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "applications"
    __table_args__ = (Index("ix_applications_tenant_name", "tenant_id", "name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class Project(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "projects"
    __table_args__ = (Index("ix_projects_tenant_name", "tenant_id", "name"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class Policy(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    document: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Guardrail(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "guardrails"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="enabled")


class AttackCampaign(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "attack_campaigns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")


class Attack(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "attacks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class AttackVariant(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "attack_variants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    attack_id: Mapped[str] = mapped_column(String(64), ForeignKey("attacks.id"))
    parent_attack_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mutation_strategy: Mapped[str | None] = mapped_column(String(128), nullable=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class AttackResult(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "attack_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    campaign_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("attack_campaigns.id"))
    attack_id: Mapped[str] = mapped_column(String(64), ForeignKey("attacks.id"))
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id"))
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    signals: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class Finding(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "findings"
    __table_args__ = (Index("ix_findings_tenant_status", "tenant_id", "status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    attack_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("attacks.id"))
    campaign_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    affected_component: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reproduction_steps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)
    regression_case_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class Trace(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "traces"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    attack_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("attacks.id"))
    spans: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)


class RagDocument(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "rag_documents"
    __table_args__ = (Index("ix_rag_documents_tenant_source", "tenant_id", "source"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    trust_score: Mapped[float] = mapped_column()
    sensitivity: Mapped[str] = mapped_column(String(32), nullable=False, default="PUBLIC")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class RagChunk(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "rag_chunks"
    __table_args__ = (Index("ix_rag_chunks_tenant_document", "tenant_id", "document_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(String(64), ForeignKey("rag_documents.id"))
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    trust_score: Mapped[float] = mapped_column()
    sensitivity: Mapped[str] = mapped_column(String(32), nullable=False, default="PUBLIC")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class ApprovalRequest(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "approval_requests"
    __table_args__ = (Index("ix_approval_requests_tenant_status", "tenant_id", "status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    arguments: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    risk: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    decision_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class ToolCall(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "tool_calls"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    request_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    risk: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)


class SecurityEvent(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("applications.id"))
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class EvaluationRun(Base, TimestampMixin, TenantScopedMixin):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=new_id)
    application_id: Mapped[str] = mapped_column(String(64), ForeignKey("applications.id"))
    campaign_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("attack_campaigns.id"))
    mode: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
