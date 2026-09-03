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
