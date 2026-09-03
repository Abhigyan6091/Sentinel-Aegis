from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class FindingStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    FIXED = "fixed"
    ACCEPTED_RISK = "accepted_risk"
    CLOSED = "closed"


# A finding may reopen from any resolved state: a regression run can prove a "fixed"
# finding is live again.
ALLOWED_TRANSITIONS: dict[FindingStatus, set[FindingStatus]] = {
    FindingStatus.OPEN: {FindingStatus.TRIAGED, FindingStatus.ACCEPTED_RISK, FindingStatus.CLOSED},
    FindingStatus.TRIAGED: {
        FindingStatus.FIXED,
        FindingStatus.ACCEPTED_RISK,
        FindingStatus.CLOSED,
        FindingStatus.OPEN,
    },
    FindingStatus.FIXED: {FindingStatus.CLOSED, FindingStatus.OPEN},
    FindingStatus.ACCEPTED_RISK: {FindingStatus.OPEN, FindingStatus.CLOSED},
    FindingStatus.CLOSED: {FindingStatus.OPEN},
}

RESOLVED_STATUSES = {FindingStatus.FIXED, FindingStatus.ACCEPTED_RISK, FindingStatus.CLOSED}


class FindingRecord(BaseModel):
    id: str
    tenant_id: str
    application_id: str | None = None
    attack_id: str | None = None
    campaign_id: str | None = None
    severity: str
    title: str
    category: str
    affected_component: str | None = None
    description: str
    impact: str | None = None
    root_cause: str | None = None
    recommendation: str
    status: FindingStatus
    evidence: dict = Field(default_factory=dict)
    reproduction_steps: list[str] = Field(default_factory=list)
    remediation: str | None = None
    regression_case_id: str | None = None
    decided_by: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FindingUpdate(BaseModel):
    status: FindingStatus | None = None
    remediation: str | None = Field(default=None, max_length=4000)
    reproduction_steps: list[str] | None = None
    decided_by: str | None = Field(default=None, max_length=64)


class RegressionCasePromotion(BaseModel):
    """Options for turning a finding into a committed regression fixture."""

    payload: str | None = Field(default=None, max_length=4000)
    expected_behavior: str | None = Field(default=None, max_length=1000)
    remediation: str | None = Field(default=None, max_length=4000)
