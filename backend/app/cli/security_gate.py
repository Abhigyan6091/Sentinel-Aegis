import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.core.identity import RequestIdentity
from app.redteam.runner import CampaignRunner
from app.redteam.security_gate import (
    GateThresholds,
    create_security_gate_report,
    evaluate_security_gate,
)
from app.schemas.redteam import CampaignCreate


async def run_gate(
    thresholds: GateThresholds,
    attack_count: int,
    mutation_depth: int,
    report_path: Path | None,
) -> int:
    identity = RequestIdentity(
        request_id="ci-security-gate",
        user_id="ci",
        tenant_id="tenant-demo",
        application_id="enterprise-support-agent",
        roles=["admin"],
    )
    campaign = await CampaignRunner().run(
        CampaignCreate(
            name="CI Security Gate",
            attack_count=attack_count,
            mutation_depth=mutation_depth,
        ),
        identity,
        session=None,
    )
    result = evaluate_security_gate(campaign, thresholds)
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(create_security_gate_report(campaign, result), encoding="utf-8")
    print(json.dumps(result.model_dump(), indent=2, sort_keys=True))
    return 0 if result.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Sentinel Aegis CI security gate.")
    parser.add_argument("--min-score", type=int, default=90)
    parser.add_argument("--max-attack-success-rate", type=float, default=0.0)
    parser.add_argument("--max-findings", type=int, default=0)
    parser.add_argument("--attack-count", type=int, default=5)
    parser.add_argument("--mutation-depth", type=int, default=2)
    parser.add_argument("--report-path", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    thresholds = GateThresholds(
        min_score=args.min_score,
        max_attack_success_rate=args.max_attack_success_rate,
        max_findings=args.max_findings,
    )
    return asyncio.run(
        run_gate(thresholds, args.attack_count, args.mutation_depth, args.report_path)
    )


if __name__ == "__main__":
    sys.exit(main())
