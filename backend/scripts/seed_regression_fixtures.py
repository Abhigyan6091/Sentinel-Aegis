"""Regenerate the committed regression fixtures from an undefended discovery run.

The defended runtime mitigates every seeded attack, so a normal gate run produces no
findings and therefore no fixtures. Running the same catalogue with defenses off makes
every attack succeed, which is what turns each one into a committed regression case:
the case then asserts the defended runtime still mitigates it.

Usage: python -m scripts.seed_regression_fixtures [output_dir]
"""

import asyncio
import sys
from pathlib import Path

from app.core.identity import RequestIdentity
from app.redteam.attacks import AttackGenerator
from app.redteam.runner import CampaignRunner
from app.regression.fixtures import FixtureStore, regression_case_from_result
from app.schemas.redteam import CampaignCreate, DefenseMode

DEFAULT_OUTPUT_DIR = Path("regression/cases")


async def seed(output_dir: Path) -> list[Path]:
    identity = RequestIdentity(
        request_id="fixture-seed",
        user_id="security-research",
        tenant_id="tenant-demo",
        application_id="enterprise-support-agent",
        roles=["admin"],
    )
    seeds = AttackGenerator.default().seeds
    campaign = await CampaignRunner().run(
        CampaignCreate(
            name="Regression Fixture Seed",
            attack_count=len(seeds),
            mutation_depth=1,
            defense_mode=DefenseMode.NO_DEFENSE,
        ),
        identity,
        session=None,
    )

    store = FixtureStore(output_dir)
    written: list[Path] = []
    for result in campaign.results:
        finding = result.evaluation.finding
        if finding is None:
            continue
        case = regression_case_from_result(
            result.variant,
            finding_id=finding.finding_id,
            title=finding.title,
            detection_signals=result.evaluation.detection_signals,
            remediation=finding.recommendation,
        )
        # Fixtures are committed artifacts: pin the timestamp so regenerating them
        # does not produce a diff on every run.
        case.created_at = campaign.campaign.started_at.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        written.append(store.save(case))
    return written


def main() -> int:
    output_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT_DIR
    for path in asyncio.run(seed(output_dir)):
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
