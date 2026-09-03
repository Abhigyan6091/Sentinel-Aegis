"""Secret resolution for production deployments.

Settings may hold a reference instead of a literal value, so credentials never live in
environment variables, compose files, or images. A reference looks like:

    secret://file/openai_api_key          -> reads {secrets_file_dir}/openai_api_key
    secret://aws/openai-api-key           -> AWS Secrets Manager, whole secret string
    secret://aws/support-agent#openai_key -> one key from a JSON secret
    secret://env/OPENAI_API_KEY           -> another environment variable

Anything without the `secret://` prefix is already a literal and is returned unchanged,
so local development keeps working with no secrets backend at all.
"""

import json
import os
import re
from functools import lru_cache
from pathlib import Path

from app.core.config import Settings, get_settings

# A URI scheme, not a credential.
SECRET_PREFIX = "secret://"  # nosec B105
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,255}$")

# Settings whose values may be secret references.
SECRET_SETTINGS = (
    "openai_api_key",
    "anthropic_api_key",
    "database_url",
    "redis_url",
    "jwt_jwks_json",
)


class SecretResolutionError(RuntimeError):
    """Raised when a secret reference cannot be resolved."""


def is_secret_reference(value: str | None) -> bool:
    return isinstance(value, str) and value.startswith(SECRET_PREFIX)


def resolve_secret(value: str | None, settings: Settings | None = None) -> str | None:
    """Resolve one value, returning literals unchanged."""
    if not is_secret_reference(value):
        return value

    settings = settings or get_settings()
    reference = value[len(SECRET_PREFIX) :]
    provider, _, name = reference.partition("/")
    if not name:
        raise SecretResolutionError(f"secret reference is missing a name: {value!r}")

    if provider == "env":
        return _resolve_env(name)
    if provider == "file":
        return _resolve_file(name, settings)
    if provider == "aws":
        return _resolve_aws(name, settings)
    raise SecretResolutionError(f"unknown secret provider: {provider!r}")


def resolve_settings_secrets(settings: Settings) -> list[str]:
    """Resolve every secret-bearing setting in place; returns the names resolved."""
    resolved: list[str] = []
    for name in SECRET_SETTINGS:
        current = getattr(settings, name, None)
        if not is_secret_reference(current):
            continue
        object.__setattr__(settings, name, resolve_secret(current, settings))
        resolved.append(name)
    return resolved


def _resolve_env(name: str) -> str:
    value = os.environ.get(name)
    if value is None:
        raise SecretResolutionError(f"environment variable {name!r} is not set")
    return value


def _resolve_file(name: str, settings: Settings) -> str:
    if not _SAFE_NAME.match(name) or ".." in name:
        raise SecretResolutionError(f"unsafe secret file name: {name!r}")
    path = Path(settings.secrets_file_dir) / name
    if not path.is_file():
        raise SecretResolutionError(f"secret file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def _resolve_aws(name: str, settings: Settings) -> str:
    secret_name, _, json_key = name.partition("#")
    payload = _fetch_aws_secret(
        f"{settings.aws_secrets_prefix}{secret_name}",
        settings.aws_secrets_region,
    )
    if not json_key:
        return payload
    try:
        document = json.loads(payload)
    except json.JSONDecodeError as error:
        raise SecretResolutionError(
            f"AWS secret {secret_name!r} is not JSON but a key was requested"
        ) from error
    if json_key not in document:
        raise SecretResolutionError(f"AWS secret {secret_name!r} has no key {json_key!r}")
    return str(document[json_key])


@lru_cache(maxsize=64)
def _fetch_aws_secret(secret_id: str, region: str | None) -> str:
    try:
        import boto3  # noqa: PLC0415 - optional dependency, only needed in AWS deployments
    except ImportError as error:
        raise SecretResolutionError(
            "AWS secrets provider requires boto3; install the 'aws' extra."
        ) from error

    client = boto3.client("secretsmanager", region_name=region)
    try:
        response = client.get_secret_value(SecretId=secret_id)
    except Exception as error:  # noqa: BLE001 - surfaced as a clear configuration failure
        raise SecretResolutionError(f"could not read AWS secret {secret_id!r}: {error}") from error

    if "SecretString" in response:
        return response["SecretString"]
    raise SecretResolutionError(f"AWS secret {secret_id!r} has no string value")
