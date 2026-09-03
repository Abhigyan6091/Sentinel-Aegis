from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field

from app.redteam.attacks import AttackCategory, AttackVariant
from app.redteam.evaluator import AttackEvaluation, FindingCandidate
from app.redteam.scoring import SecurityScore
from app.schemas.support import SupportChatResponse


class DefenseMode(str, Enum):
    NO_DEFENSE = "no_defense"
    RULES_ONLY = "rules_only"
    CLASSIFIER = "classifier"
    LLM_JUDGE = "llm_judge"
    LAYERED = "layered"


class CampaignCreate(BaseModel):
    name: str = Field(default="Deterministic Red-Team Campaign", min_length=1, max_length=255)
    categories: list[AttackCategory] | None = None
    attack_count: int = Field(default=5, ge=1, le=100)
    mutation_depth: int = Field(default=1, ge=1, le=5)
    defense_enabled: bool = True
    defense_mode: DefenseMode = DefenseMode.LAYERED
    concurrency: int = Field(default=1, ge=1, le=10)
    evaluation_mode: str = "rules_and_signals"


class BenchmarkCreate(BaseModel):
    name: str = Field(default="Defense Benchmark", min_length=1, max_length=255)
    categories: list[AttackCategory] | None = None
    attack_count: int = Field(default=5, ge=1, le=100)
    mutation_depth: int = Field(default=1, ge=1, le=5)
    defense_modes: list[DefenseMode] = Field(
        default_factory=lambda: [DefenseMode.NO_DEFENSE, DefenseMode.LAYERED]
    )


class CampaignSummary(BaseModel):
    campaign_id: str
    tenant_id: str
    application_id: str | None = None
    name: str
    status: str
    attack_count: int
    mutation_depth: int
    started_at: datetime
    completed_at: datetime | None = None


class CampaignAttackResult(BaseModel):
    variant: AttackVariant
    runtime: SupportChatResponse
    evaluation: AttackEvaluation
    trace: list[dict[str, str]]


class CampaignRunResponse(BaseModel):
    campaign: CampaignSummary
    score: SecurityScore
    results: list[CampaignAttackResult]
    findings: list[FindingCandidate]
    defense_mode: DefenseMode = DefenseMode.LAYERED


class BenchmarkRun(BaseModel):
    defense_mode: DefenseMode
    score: SecurityScore
    findings_count: int
    attack_success_rate: float


class BenchmarkResponse(BaseModel):
    name: str
    tenant_id: str
    runs: list[BenchmarkRun]


def new_campaign_id() -> str:
    return f"CMP-{uuid4().hex[:8].upper()}"
