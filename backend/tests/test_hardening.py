"""Phase P8: HTTP hardening, secret resolution, and production preflight checks."""

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.core.preflight import (
    UnsafeConfigurationError,
    production_config_problems,
    verify_production_config,
)
from app.core.secrets import (
    SecretResolutionError,
    is_secret_reference,
    resolve_secret,
    resolve_settings_secrets,
)
from app.main import create_app

DEMO_KEY = {"x-api-key": "dev-aegis-key"}


def make_client(monkeypatch, tmp_path, **env) -> TestClient:
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'hardening.db'}")
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    return TestClient(create_app())


def test_security_headers_are_present_on_every_response(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"


def test_hsts_is_only_sent_in_production(monkeypatch, tmp_path):
    local = make_client(monkeypatch, tmp_path)
    assert "strict-transport-security" not in local.get("/health").headers

    production = make_client(
        monkeypatch,
        tmp_path,
        AEGIS_ENVIRONMENT="production",
        AEGIS_AUTH_MODE="jwt",
        AEGIS_ALLOW_DEV_API_KEYS="false",
        AEGIS_AUTO_CREATE_SCHEMA="false",
        AEGIS_JWT_ISSUER="https://issuer.example.com",
        AEGIS_JWT_AUDIENCE="sentinel-aegis",
        AEGIS_JWT_JWKS_URL="https://issuer.example.com/jwks",
        AEGIS_DATABASE_URL="postgresql+asyncpg://aegis:aegis@postgres:5432/aegisai",
    )
    headers = production.get("/health").headers
    assert "max-age=31536000" in headers["strict-transport-security"]


def test_request_id_is_echoed_and_generated(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    echoed = client.get("/health", headers={"x-request-id": "req-abc"})
    generated = client.get("/health")

    assert echoed.headers["x-request-id"] == "req-abc"
    assert generated.headers["x-request-id"]


def test_oversized_requests_are_rejected(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, AEGIS_MAX_REQUEST_BYTES="256")

    response = client.post(
        "/api/v1/support/chat",
        headers=DEMO_KEY,
        json={"message": "x" * 2000},
    )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "request_too_large"


def test_requests_within_the_limit_are_accepted(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path, AEGIS_MAX_REQUEST_BYTES="4096")

    response = client.post(
        "/api/v1/support/chat",
        headers=DEMO_KEY,
        json={"message": "How do I request a refund?"},
    )

    assert response.status_code == 200


def test_errors_use_a_structured_envelope_with_a_request_id(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    unauthorized = client.get("/api/v1/findings")
    validation = client.post("/api/v1/support/chat", headers=DEMO_KEY, json={"message": ""})

    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "unauthenticated"
    assert unauthorized.json()["error"]["request_id"]

    assert validation.status_code == 422
    body = validation.json()["error"]
    assert body["code"] == "validation_error"
    assert body["details"]
    # The rejected value must not be echoed back into the error body.
    assert "message" in body["details"][0]["location"]


def test_cors_is_disabled_unless_origins_are_configured(monkeypatch, tmp_path):
    closed = make_client(monkeypatch, tmp_path)
    response = closed.get("/health", headers={"origin": "https://evil.example.com"})
    assert "access-control-allow-origin" not in response.headers

    allowed = make_client(
        monkeypatch,
        tmp_path,
        AEGIS_CORS_ALLOW_ORIGINS='["https://console.example.com"]',
    )
    permitted = allowed.get("/health", headers={"origin": "https://console.example.com"})
    rejected = allowed.get("/health", headers={"origin": "https://evil.example.com"})

    assert permitted.headers["access-control-allow-origin"] == "https://console.example.com"
    assert "access-control-allow-origin" not in rejected.headers


def test_openapi_docs_are_hidden_in_production(monkeypatch, tmp_path):
    client = make_client(
        monkeypatch,
        tmp_path,
        AEGIS_ENVIRONMENT="production",
        AEGIS_AUTH_MODE="jwt",
        AEGIS_ALLOW_DEV_API_KEYS="false",
        AEGIS_AUTO_CREATE_SCHEMA="false",
        AEGIS_JWT_ISSUER="https://issuer.example.com",
        AEGIS_JWT_AUDIENCE="sentinel-aegis",
        AEGIS_JWT_JWKS_URL="https://issuer.example.com/jwks",
        AEGIS_DATABASE_URL="postgresql+asyncpg://aegis:aegis@postgres:5432/aegisai",
    )

    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def production_settings(**overrides) -> Settings:
    base = {
        "environment": "production",
        "auth_mode": "jwt",
        "allow_dev_api_keys": False,
        "auto_create_schema": False,
        "jwt_issuer": "https://issuer.example.com",
        "jwt_audience": "sentinel-aegis",
        "jwt_jwks_url": "https://issuer.example.com/jwks",
        "database_url": "postgresql+asyncpg://aegis:aegis@postgres:5432/aegisai",
    }
    return Settings(**{**base, **overrides})


def test_valid_production_config_has_no_problems():
    assert production_config_problems(production_settings()) == []


def test_local_config_is_never_blocked():
    assert production_config_problems(Settings(environment="local")) == []


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"allow_dev_api_keys": True}, "AEGIS_ALLOW_DEV_API_KEYS"),
        ({"auth_mode": "hybrid"}, "AEGIS_AUTH_MODE"),
        ({"jwt_issuer": None}, "AEGIS_JWT_ISSUER"),
        ({"jwt_jwks_url": None, "jwt_jwks_json": None}, "JWKS source"),
        ({"cors_allow_origins": ["*"]}, "Wildcard CORS"),
        ({"auto_create_schema": True}, "AEGIS_AUTO_CREATE_SCHEMA"),
        ({"database_url": "sqlite+aiosqlite:///./x.db"}, "SQLite"),
        ({"security_headers_enabled": False}, "Security headers"),
    ],
)
def test_unsafe_production_settings_are_reported(overrides, expected):
    problems = production_config_problems(production_settings(**overrides))

    assert any(expected in problem for problem in problems)


def test_production_preflight_reports_every_problem_at_once():
    settings = production_settings(allow_dev_api_keys=True, auth_mode="hybrid")

    with pytest.raises(UnsafeConfigurationError) as error:
        verify_production_config(settings)

    assert "AEGIS_ALLOW_DEV_API_KEYS" in str(error.value)
    assert "AEGIS_AUTH_MODE" in str(error.value)


def test_literal_values_are_not_treated_as_secret_references():
    assert is_secret_reference("sk-live-1234") is False
    assert resolve_secret("sk-live-1234") == "sk-live-1234"
    assert resolve_secret(None) is None


def test_env_secret_references_resolve(monkeypatch):
    monkeypatch.setenv("PROVIDER_TOKEN", "resolved-from-env")

    assert resolve_secret("secret://env/PROVIDER_TOKEN") == "resolved-from-env"


def test_file_secret_references_resolve(tmp_path):
    (tmp_path / "openai_api_key").write_text("resolved-from-file\n")
    settings = Settings(secrets_file_dir=str(tmp_path))

    assert resolve_secret("secret://file/openai_api_key", settings) == "resolved-from-file"


def test_file_secret_references_reject_path_traversal(tmp_path):
    settings = Settings(secrets_file_dir=str(tmp_path))

    with pytest.raises(SecretResolutionError):
        resolve_secret("secret://file/../../etc/passwd", settings)


def test_missing_secrets_fail_loudly(tmp_path):
    settings = Settings(secrets_file_dir=str(tmp_path))

    with pytest.raises(SecretResolutionError):
        resolve_secret("secret://file/absent", settings)
    with pytest.raises(SecretResolutionError):
        resolve_secret("secret://nope/whatever", settings)


def test_settings_secrets_are_resolved_in_place(tmp_path, monkeypatch):
    (tmp_path / "openai").write_text("sk-resolved")
    monkeypatch.setenv("ANTHROPIC_TOKEN", "anthropic-resolved")
    settings = Settings(
        secrets_file_dir=str(tmp_path),
        openai_api_key="secret://file/openai",
        anthropic_api_key="secret://env/ANTHROPIC_TOKEN",
        redis_url="redis://localhost:6379/0",
    )

    resolved = resolve_settings_secrets(settings)

    assert set(resolved) == {"openai_api_key", "anthropic_api_key"}
    assert settings.openai_api_key == "sk-resolved"
    assert settings.anthropic_api_key == "anthropic-resolved"
    # A literal setting is left exactly as configured.
    assert settings.redis_url == "redis://localhost:6379/0"


def test_aws_json_secret_selects_a_single_key(monkeypatch, tmp_path):
    from app.core import secrets as secrets_module

    secrets_module._fetch_aws_secret.cache_clear()
    monkeypatch.setattr(
        secrets_module,
        "_fetch_aws_secret",
        lambda secret_id, region: json.dumps({"openai_key": "sk-aws", "other": "no"}),
    )
    settings = Settings(aws_secrets_region="us-east-1")

    assert resolve_secret("secret://aws/providers#openai_key", settings) == "sk-aws"
