"""Campaign and regression reports in JSON and Markdown, plus JSON re-import.

Reports are the durable, shareable form of a campaign: JSON round-trips exactly so a
committed report can be re-imported and re-rendered, and Markdown is the human review
artifact attached to CI runs.
"""

import json

from app.regression.runner import RegressionSuiteResult
from app.schemas.redteam import CampaignRunResponse

REPORT_FORMAT_VERSION = "1.0"


def campaign_report_payload(campaign: CampaignRunResponse) -> dict:
    return {
        "report_format_version": REPORT_FORMAT_VERSION,
        "kind": "campaign",
        "campaign": campaign.model_dump(mode="json"),
    }


def campaign_report_json(campaign: CampaignRunResponse) -> str:
    return json.dumps(campaign_report_payload(campaign), indent=2, sort_keys=True) + "\n"


def campaign_from_report(payload: dict) -> CampaignRunResponse:
    """Rebuild a campaign from an exported report so committed reports stay reproducible."""
    if payload.get("kind") != "campaign":
        raise ValueError("report payload is not a campaign report")
    version = payload.get("report_format_version")
    if version != REPORT_FORMAT_VERSION:
        raise ValueError(f"unsupported report format version: {version!r}")
    return CampaignRunResponse.model_validate(payload["campaign"])


def campaign_report_markdown(campaign: CampaignRunResponse) -> str:
    summary = campaign.campaign
    score = campaign.score
    lines = [
        "# Sentinel Aegis Campaign Report",
        "",
        f"- Campaign: `{summary.campaign_id}`",
        f"- Name: {summary.name}",
        f"- Tenant: `{summary.tenant_id}`",
        f"- Defense mode: `{campaign.defense_mode.value}`",
        f"- Attacks executed: {score.attacks_executed}",
        f"- Successful attacks: {score.successful_attacks}",
        f"- Attack success rate: {score.attack_success_rate:.3f}",
        f"- Overall score: {score.overall}",
        "",
        "## Attack Results",
        "",
        "| Attack | Category | Severity | Outcome |",
        "| --- | --- | --- | --- |",
    ]
    for result in campaign.results:
        outcome = "SUCCEEDED" if result.evaluation.successful_attack else "mitigated"
        lines.append(
            f"| `{result.variant.attack_id}` | {result.variant.category.value} "
            f"| {result.variant.severity} | {outcome} |"
        )

    lines.extend(["", "## Findings", ""])
    if campaign.findings:
        for finding in campaign.findings:
            lines.extend(
                [
                    f"### {finding.finding_id}: {finding.title}",
                    "",
                    f"- Severity: `{finding.severity}`",
                    f"- Attack ID: `{finding.attack_id}`",
                    f"- Category: `{finding.category}`",
                    f"- Component: {finding.affected_component}",
                    f"- Impact: {finding.impact}",
                    f"- Root cause: {finding.root_cause}",
                    f"- Recommendation: {finding.recommendation}",
                    "",
                ]
            )
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def regression_report_markdown(result: RegressionSuiteResult) -> str:
    status = "PASS" if result.is_green else "FAIL"
    lines = [
        "# Sentinel Aegis Regression Suite Report",
        "",
        f"- Status: {status}",
        f"- Tenant: `{result.tenant_id}`",
        f"- Defense mode: `{result.defense_mode.value}`",
        f"- Cases: {result.total}",
        f"- Passed: {result.passed}",
        f"- Failed: {result.failed}",
        "",
        "## Cases",
        "",
        "| Case | Category | Severity | Result |",
        "| --- | --- | --- | --- |",
    ]
    if result.cases:
        for case in result.cases:
            lines.append(
                f"| `{case.case_id}` | {case.category} | {case.severity} "
                f"| {'PASS' if case.passed else 'FAIL'} |"
            )
    else:
        lines.append("| _none_ | | | |")

    failures = [case for case in result.cases if not case.passed]
    lines.extend(["", "## Failures", ""])
    if failures:
        for case in failures:
            lines.extend(
                [
                    f"### {case.case_id}: {case.title}",
                    "",
                    f"- Reason: {case.reason}",
                    f"- Observed signals: {', '.join(case.detection_signals) or 'none'}",
                    "",
                ]
            )
    else:
        lines.append("- None")

    return "\n".join(lines).rstrip() + "\n"


def regression_report_json(result: RegressionSuiteResult) -> str:
    payload = {
        "report_format_version": REPORT_FORMAT_VERSION,
        "kind": "regression_suite",
        "result": result.model_dump(mode="json"),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
