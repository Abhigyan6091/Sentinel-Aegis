"""Durable regression fixtures derived from security findings.

A finding is a one-off observation from an exploratory campaign. A regression case is
the committed, replayable form of that finding: the exact payload plus the mitigation
the runtime is now expected to produce. Cases live as JSON files on disk so a security
report can be reproduced from version control rather than from a live database.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.redteam.attacks import AttackCategory, AttackVariant

_SAFE_CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


class RegressionCase(BaseModel):
    """One committed attack that the runtime must keep mitigating."""

    case_id: str
    title: str
    category: AttackCategory
    severity: str
    payload: str
    expected_behavior: str
    expected_mitigated: bool = True
    source_finding_id: str | None = None
    source_campaign_id: str | None = None
    evidence: dict[str, list[str] | str] = Field(default_factory=dict)
    reproduction_steps: list[str] = Field(default_factory=list)
    remediation: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_variant(self) -> AttackVariant:
        """Rebuild the attack so the shared evaluator can judge the replay."""
        return AttackVariant(
            attack_id=self.case_id,
            seed_id=self.case_id,
            category=self.category,
            severity=self.severity,
            payload=self.payload,
            expected_behavior=self.expected_behavior,
            mutation_strategy="regression",
            metadata={"source": "regression_fixture"},
        )


def case_id_for(category: str, attack_id: str) -> str:
    """Build a stable id: rerunning the gate updates a case rather than cloning it.

    Attack ids are deterministic for a given seed catalogue, so the same attack always
    maps to the same fixture file.
    """
    raw = f"REG-{category.replace('_', '-')}-{attack_id}"
    return re.sub(r"[^A-Za-z0-9._-]", "-", raw)[:64]


def build_regression_case(
    *,
    case_id: str,
    title: str,
    category: AttackCategory,
    severity: str,
    payload: str,
    expected_behavior: str,
    detection_signals: list[str],
    source_finding_id: str | None = None,
    source_campaign_id: str | None = None,
    remediation: str = "",
) -> RegressionCase:
    return RegressionCase(
        case_id=case_id,
        title=title,
        category=category,
        severity=severity,
        payload=payload,
        expected_behavior=expected_behavior,
        source_finding_id=source_finding_id,
        source_campaign_id=source_campaign_id,
        evidence={
            "observed_detection_signals": detection_signals,
            "observed_outcome": "attack succeeded against the runtime",
        },
        reproduction_steps=[
            "Start the Sentinel Aegis API with the default layered defense configuration.",
            f"POST the case payload to /api/v1/support/chat as category {category.value}.",
            f"Observe the response: {expected_behavior}",
            "Fail the case if the runtime emits no blocking, isolation, redaction, "
            "or approval signal.",
        ],
        remediation=remediation,
    )


class FixtureStore:
    """Reads and writes regression cases as one JSON file per case."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory or get_settings().regression_fixtures_dir)

    def _path(self, case_id: str) -> Path:
        if not _SAFE_CASE_ID.match(case_id):
            raise ValueError(f"unsafe regression case id: {case_id!r}")
        return self.directory / f"{case_id}.json"

    def save(self, case: RegressionCase) -> Path:
        path = self._path(case.case_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(case.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def get(self, case_id: str) -> RegressionCase | None:
        path = self._path(case_id)
        if not path.exists():
            return None
        return RegressionCase.model_validate_json(path.read_text(encoding="utf-8"))

    def load_all(self) -> list[RegressionCase]:
        if not self.directory.exists():
            return []
        cases = [
            RegressionCase.model_validate_json(path.read_text(encoding="utf-8"))
            for path in sorted(self.directory.glob("*.json"))
        ]
        return cases

    def delete(self, case_id: str) -> bool:
        path = self._path(case_id)
        if not path.exists():
            return False
        path.unlink()
        return True


def regression_case_from_result(
    variant: AttackVariant,
    finding_id: str,
    title: str,
    detection_signals: list[str],
    remediation: str,
    campaign_id: str | None = None,
) -> RegressionCase:
    """Canonical finding-to-fixture conversion shared by the API, CLI, and seeding."""
    return build_regression_case(
        case_id=case_id_for(variant.category.value, variant.attack_id),
        title=title,
        category=variant.category,
        severity=variant.severity,
        payload=variant.payload,
        expected_behavior=variant.expected_behavior,
        detection_signals=detection_signals,
        source_finding_id=finding_id,
        source_campaign_id=campaign_id,
        remediation=remediation,
    )
