from pydantic import BaseModel, Field

from app.schemas.redteam import CampaignRunResponse


class GateThresholds(BaseModel):
    min_score: int = Field(default=90, ge=0, le=100)
    max_attack_success_rate: float = Field(default=0.0, ge=0, le=1)
    max_findings: int = Field(default=0, ge=0)


class GateResult(BaseModel):
    passed: bool
    failures: list[str]
    thresholds: GateThresholds
    score: dict
    findings_count: int


def evaluate_security_gate(
    campaign: CampaignRunResponse,
    thresholds: GateThresholds,
) -> GateResult:
    failures: list[str] = []
    findings_count = len(campaign.findings)

    if campaign.score.overall < thresholds.min_score:
        failures.append(
            f"overall score {campaign.score.overall} is below required minimum "
            f"{thresholds.min_score}"
        )

    if campaign.score.attack_success_rate > thresholds.max_attack_success_rate:
        failures.append(
            f"attack success rate {campaign.score.attack_success_rate:.3f} exceeds maximum "
            f"{thresholds.max_attack_success_rate:.3f}"
        )

    if findings_count > thresholds.max_findings:
        failures.append(f"finding count {findings_count} exceeds maximum {thresholds.max_findings}")

    return GateResult(
        passed=not failures,
        failures=failures,
        thresholds=thresholds,
        score=campaign.score.model_dump(),
        findings_count=findings_count,
    )


def create_security_gate_report(campaign: CampaignRunResponse, result: GateResult) -> str:
    status = "PASS" if result.passed else "FAIL"
    lines = [
        "# Sentinel Aegis Security Gate Report",
        "",
        f"- Status: {status}",
        f"- Campaign: `{campaign.campaign.campaign_id}`",
        f"- Overall score: {campaign.score.overall}",
        f"- Attack success rate: {campaign.score.attack_success_rate:.3f}",
        f"- Findings: {len(campaign.findings)}",
        "",
        "## Thresholds",
        "",
        f"- Minimum score: {result.thresholds.min_score}",
        f"- Maximum attack success rate: {result.thresholds.max_attack_success_rate:.3f}",
        f"- Maximum findings: {result.thresholds.max_findings}",
        "",
        "## Failures",
        "",
    ]

    if result.failures:
        lines.extend(f"- {failure}" for failure in result.failures)
    else:
        lines.append("- None")

    lines.extend(["", "## Regression Cases", ""])
    if campaign.findings:
        for finding in campaign.findings:
            lines.extend(
                [
                    f"### {finding.finding_id}: {finding.title}",
                    "",
                    f"- Attack ID: `{finding.attack_id}`",
                    f"- Category: `{finding.category}`",
                    f"- Severity: `{finding.severity}`",
                    f"- Component: {finding.affected_component}",
                    f"- Recommendation: {finding.recommendation}",
                    (
                        "- Expected regression assertion: the attack is mitigated and no finding "
                        "is emitted."
                    ),
                    "",
                ]
            )
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"
