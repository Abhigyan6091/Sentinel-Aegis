from datetime import datetime

from pydantic import BaseModel, Field


class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    application_id: str | None = None
    document: dict = Field(default_factory=dict)


class PolicyRead(BaseModel):
    id: str
    tenant_id: str
    application_id: str | None
    name: str
    document: dict
    status: str
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRead(BaseModel):
    id: str
    tenant_id: str
    request_id: str
    application_id: str | None
    tool_name: str
    arguments: dict
    risk: str
    status: str
    decision_reason: str | None
    decided_by: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    decision: str = Field(pattern="^(approved|rejected)$")
    reason: str = Field(min_length=1, max_length=2000)
