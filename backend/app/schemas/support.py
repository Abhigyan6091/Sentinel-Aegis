from pydantic import BaseModel, Field

from app.security.context_firewall import DocumentDecision
from app.security.policy import PolicyDecision
from app.security.runtime import Decision, GuardrailResult


class SupportChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    application_id: str | None = None


class ToolCallAudit(BaseModel):
    tool_name: str
    decision: Decision
    risk: str
    reason: str
    executed: bool
    result: dict[str, str] = Field(default_factory=dict)


class TraceStep(BaseModel):
    component: str
    decision: str
    reason: str


class SupportChatResponse(BaseModel):
    request_id: str
    answer: str
    decision: Decision
    blocked: bool
    guardrails: list[GuardrailResult]
    context_documents: list[DocumentDecision]
    allowed_context: list[dict[str, str]]
    tool_calls: list[ToolCallAudit]
    trace: list[TraceStep]
    tokens: dict[str, int]


def policy_to_tool_audit(decision: PolicyDecision, tool_name: str) -> ToolCallAudit:
    return ToolCallAudit(
        tool_name=tool_name,
        decision=decision.decision,
        risk=decision.risk.value,
        reason=decision.reason,
        executed=False,
        result={},
    )
