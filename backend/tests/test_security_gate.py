import json
import subprocess
import sys

from app.redteam.scoring import SecurityScore
from app.redteam.security_gate import (
    GateThresholds,
    create_security_gate_report,
    evaluate_security_gate,
)
from app.schemas.redteam import CampaignRunResponse, CampaignSummary


def make_campaign(
    *,
    overall: int = 100,
    attack_success_rate: float = 0,
    findings: int = 0,
) -> CampaignRunResponse:
    return CampaignRunResponse(
        campaign=CampaignSummary(
            campaign_id="CMP-TEST",
            tenant_id="tenant-demo",
            application_id=None,
            name="Gate Test",
            status="completed",
            attack_count=5,
            mutation_depth=1,
            started_at="2026-09-03T00:00:00Z",
            completed_at="2026-09-03T00:01:00Z",
        ),
        score=SecurityScore(
            overall=overall,
            prompt_security=overall,
            rag_security=overall,
            agent_security=overall,
            data_security=overall,
            availability=100,
            attack_success_rate=attack_success_rate,
            detection_rate=1 - attack_success_rate,
            false_positive_rate=0,
            false_negative_rate=attack_success_rate,
            attacks_executed=5,
            successful_attacks=round(5 * attack_success_rate),
        ),
        results=[],
        findings=[
            {
                "finding_id": f"F-{index}",
                "severity": "HIGH",
                "title": "Bypass",
                "attack_id": f"ATK-{index}",
                "category": "prompt_injection",
                "affected_component": "Enterprise Support Agent",
                "description": "Unmitigated attack.",
                "impact": "Security control bypass.",
                "root_cause": "Missing mitigation.",
                "recommendation": "Add a regression.",
                "status": "OPEN",
            }
            for index in range(findings)
        ],
    )


def test_security_gate_passes_when_campaign_meets_thresholds():
    result = evaluate_security_gate(
        make_campaign(overall=100, attack_success_rate=0, findings=0),
        GateThresholds(min_score=100, max_attack_success_rate=0, max_findings=0),
    )

    assert result.passed is True
    assert result.failures == []


def test_security_gate_reports_all_threshold_failures():
    result = evaluate_security_gate(
        make_campaign(overall=70, attack_success_rate=0.4, findings=2),
        GateThresholds(min_score=90, max_attack_success_rate=0.1, max_findings=0),
    )

    assert result.passed is False
    assert result.failures == [
        "overall score 70 is below required minimum 90",
        "attack success rate 0.400 exceeds maximum 0.100",
        "finding count 2 exceeds maximum 0",
    ]


def test_security_gate_cli_outputs_json_and_exits_successfully():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli.security_gate",
            "--min-score",
            "100",
            "--max-attack-success-rate",
            "0",
            "--max-findings",
            "0",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["passed"] is True
    assert payload["score"]["overall"] == 100
    assert payload["thresholds"]["min_score"] == 100


def test_security_gate_report_includes_regression_cases_for_findings():
    campaign = make_campaign(overall=60, attack_success_rate=0.4, findings=2)
    result = evaluate_security_gate(
        campaign,
        GateThresholds(min_score=90, max_attack_success_rate=0, max_findings=0),
    )

    report = create_security_gate_report(campaign, result)

    assert "# Sentinel Aegis Security Gate Report" in report
    assert "- Status: FAIL" in report
    assert "## Regression Cases" in report
    assert "### F-0: Bypass" in report
    assert "- Attack ID: `ATK-0`" in report
    assert "- Expected regression assertion: the attack is mitigated and no finding is emitted."


def test_security_gate_cli_writes_report_file(tmp_path):
    report_path = tmp_path / "security-gate.md"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "app.cli.security_gate",
            "--min-score",
            "100",
            "--max-attack-success-rate",
            "0",
            "--max-findings",
            "0",
            "--report-path",
            str(report_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    assert report_path.read_text().startswith("# Sentinel Aegis Security Gate Report")
