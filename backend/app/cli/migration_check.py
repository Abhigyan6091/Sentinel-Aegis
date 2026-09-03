"""Migration smoke test: prove the schema can be built, reverted, and rebuilt.

Run against a scratch database before a production deploy. A migration that cannot be
downgraded is a migration you cannot roll back, so this exercises both directions.
"""

import argparse
import sys

from alembic.config import Config

from alembic import command


def run_smoke_test(config_path: str, base_revision: str, verbose: bool) -> int:
    config = Config(config_path)
    if not verbose:
        config.set_main_option("loggers", "")

    print("upgrade -> head")
    command.upgrade(config, "head")
    print(f"downgrade -> {base_revision}")
    command.downgrade(config, base_revision)
    print("upgrade -> head")
    command.upgrade(config, "head")
    print("migration smoke test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Sentinel Aegis migration smoke test.")
    parser.add_argument("--config", default="alembic.ini")
    parser.add_argument(
        "--base-revision",
        default="base",
        help="Revision to downgrade to before re-upgrading (default: base).",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run_smoke_test(args.config, args.base_revision, args.verbose)
    except Exception as error:  # noqa: BLE001 - CLI boundary: report and fail the deploy
        print(f"migration smoke test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
