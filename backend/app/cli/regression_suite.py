"""CI entry point for the committed regression suite.

Separate from `app.cli.security_gate`: the gate explores generated attacks and may
surface new findings, while this suite replays committed fixtures and must stay green.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from app.core.identity import RequestIdentity
from app.regression.fixtures import FixtureStore
from app.regression.runner import RegressionSuiteRunner
from app.reports.service import regression_report_markdown
from app.schemas.redteam import DefenseMode


async def run_suite(
    defense_mode: DefenseMode,
    fixtures_dir: Path | None,
    report_path: Path | None,
) -> int:
    identity = RequestIdentity(
        request_id="ci-regression-suite",
        user_id="ci",
        tenant_id="tenant-demo",
        application_id="enterprise-support-agent",
        roles=["admin"],
    )
    runner = RegressionSuiteRunner(store=FixtureStore(fixtures_dir))
    result = await runner.run(identity, session=None, defense_mode=defense_mode)

    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(regression_report_markdown(result), encoding="utf-8")

    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0 if result.is_green else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Sentinel Aegis regression suite.")
    parser.add_argument(
        "--defense-mode",
        type=DefenseMode,
        choices=list(DefenseMode),
        default=DefenseMode.LAYERED,
    )
    parser.add_argument("--fixtures-dir", type=Path, default=None)
    parser.add_argument("--report-path", type=Path, default=None)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(run_suite(args.defense_mode, args.fixtures_dir, args.report_path))


if __name__ == "__main__":
    sys.exit(main())
