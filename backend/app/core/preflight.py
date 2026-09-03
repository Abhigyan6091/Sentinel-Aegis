"""Startup checks that refuse unsafe production configurations.

A misconfigured production deployment is a security incident, not a warning: these
checks fail the boot rather than serving traffic with development credentials or an
open CORS policy.
"""

from app.core.config import Settings


class UnsafeConfigurationError(RuntimeError):
    """Raised when production settings would expose the service."""


def production_config_problems(settings: Settings) -> list[str]:
    """Return every production safety violation, so operators fix them in one pass."""
    if not settings.is_production:
        return []

    problems: list[str] = []

    if settings.allow_dev_api_keys:
        problems.append(
            "AEGIS_ALLOW_DEV_API_KEYS must be false in production; "
            "static development keys grant full tenant access."
        )
    if settings.auth_mode != "jwt":
        problems.append("AEGIS_AUTH_MODE must be 'jwt' in production.")
    if not settings.jwt_issuer or not settings.jwt_audience:
        problems.append("AEGIS_JWT_ISSUER and AEGIS_JWT_AUDIENCE must be set in production.")
    if not settings.jwt_jwks_url and not settings.jwt_jwks_json:
        problems.append("A JWKS source must be configured in production.")
    if "*" in settings.cors_allow_origins:
        problems.append("Wildcard CORS origins are not allowed in production.")
    if settings.cors_allow_credentials and not settings.cors_allow_origins:
        problems.append("CORS credentials require an explicit origin allowlist.")
    if settings.auto_create_schema:
        problems.append(
            "AEGIS_AUTO_CREATE_SCHEMA must be false in production; "
            "use alembic migrations so schema changes are reviewed."
        )
    if settings.database_url.startswith("sqlite"):
        problems.append("SQLite is not supported in production; use PostgreSQL.")
    if not settings.security_headers_enabled:
        problems.append("Security headers must stay enabled in production.")

    return problems


def verify_production_config(settings: Settings) -> None:
    problems = production_config_problems(settings)
    if problems:
        formatted = "\n".join(f"  - {problem}" for problem in problems)
        raise UnsafeConfigurationError(
            f"Refusing to start with an unsafe production configuration:\n{formatted}"
        )
