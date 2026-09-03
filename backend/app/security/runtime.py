from enum import Enum
from time import perf_counter

from pydantic import BaseModel, Field


class Decision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    WARN = "WARN"
    SANITIZE = "SANITIZE"
    ISOLATE = "ISOLATE"
    DENY = "DENY"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"


class Risk(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class GuardrailResult(BaseModel):
    decision: Decision
    risk: Risk
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    guardrail: str
    latency_ms: int


def latency_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)
