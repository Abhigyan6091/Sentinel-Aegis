from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import get_settings


def test_foundation_migration_creates_required_tables(monkeypatch, tmp_path):
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    get_settings.cache_clear()
    config = Config("alembic.ini")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    tables = set(inspect(engine).get_table_names())

    assert {
        "users",
        "tenants",
        "applications",
        "projects",
        "policies",
        "guardrails",
        "attack_campaigns",
        "attacks",
        "attack_variants",
        "attack_results",
        "findings",
        "traces",
        "tool_calls",
        "security_events",
        "evaluation_runs",
    } <= tables


def test_finding_lifecycle_migration_adds_evidence_columns(monkeypatch, tmp_path):
    database_path = tmp_path / "lifecycle.db"
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    get_settings.cache_clear()
    config = Config("alembic.ini")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    columns = {column["name"] for column in inspect(engine).get_columns("findings")}

    assert {
        "campaign_id",
        "impact",
        "root_cause",
        "evidence",
        "reproduction_steps",
        "remediation",
        "regression_case_id",
        "decided_by",
        "resolved_at",
    } <= columns


def test_finding_lifecycle_migration_is_reversible(monkeypatch, tmp_path):
    database_path = tmp_path / "downgrade.db"
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    get_settings.cache_clear()
    config = Config("alembic.ini")

    command.upgrade(config, "head")
    command.downgrade(config, "20260903_0003")

    engine = create_engine(f"sqlite:///{database_path}")
    columns = {column["name"] for column in inspect(engine).get_columns("findings")}

    assert "regression_case_id" not in columns
    assert "status" in columns


def test_migration_smoke_test_survives_a_full_downgrade_and_rebuild(monkeypatch, tmp_path):
    """Phase P8: a migration you cannot reverse is a deploy you cannot roll back."""
    from app.cli.migration_check import run_smoke_test

    database_path = tmp_path / "smoke.db"
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{database_path}")
    get_settings.cache_clear()

    assert run_smoke_test("alembic.ini", "base", verbose=False) == 0

    engine = create_engine(f"sqlite:///{database_path}")
    tables = set(inspect(engine).get_table_names())
    assert {"findings", "policies", "rag_chunks", "approval_requests"} <= tables
