from pydantic import BaseModel, Field

from app.redteam.attacks import AttackCategory
from app.schemas.redteam import DefenseMode


class RegressionSuiteRequest(BaseModel):
    defense_mode: DefenseMode = DefenseMode.LAYERED
    case_ids: list[str] | None = None
    store_artifact: bool = True


class RegressionCaseCreate(BaseModel):
    case_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    title: str = Field(min_length=1, max_length=255)
    category: AttackCategory
    severity: str = Field(default="HIGH", max_length=32)
    payload: str = Field(min_length=1, max_length=4000)
    expected_behavior: str = Field(min_length=1, max_length=1000)
    expected_mitigated: bool = True
    remediation: str = Field(default="", max_length=4000)
