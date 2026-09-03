import json
from uuid import uuid4

from fastapi import Header, HTTPException, status
from jwt import PyJWKClient, PyJWTError, decode, get_unverified_header
from jwt.algorithms import RSAAlgorithm

from app.core.config import get_settings
from app.core.identity import RequestIdentity


def _extract_token(
    x_api_key: str | None,
    authorization: str | None,
) -> str | None:
    if x_api_key:
        return x_api_key
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return None


def _identity_for_token(token: str, request_id: str) -> RequestIdentity | None:
    settings = get_settings()
    for tenant_id, configured_token in settings.api_keys.items():
        if token == configured_token:
            suffix = tenant_id.removeprefix("tenant-")
            return RequestIdentity(
                request_id=request_id,
                user_id=f"user-{suffix}",
                tenant_id=tenant_id,
                application_id=None,
                roles=["support_agent"],
            )
    return None


def _identity_for_jwt(token: str, request_id: str) -> RequestIdentity:
    settings = get_settings()
    if not settings.jwt_issuer or not settings.jwt_audience:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT issuer and audience are not configured",
        )

    try:
        key = _jwt_signing_key(token)
        claims = decode(
            token,
            key=key,
            algorithms=settings.jwt_algorithms,
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            leeway=settings.jwt_clock_skew_seconds,
        )
    except (PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT credentials",
        ) from exc

    tenant_id = claims.get("tenant_id") or claims.get("tid")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT tenant claim is required",
        )

    roles = claims.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]

    return RequestIdentity(
        request_id=request_id,
        user_id=str(claims["sub"]),
        tenant_id=str(tenant_id),
        application_id=claims.get("application_id"),
        roles=[str(role) for role in roles],
    )


def _jwt_signing_key(token: str):
    settings = get_settings()
    if settings.jwt_jwks_json:
        jwks = json.loads(settings.jwt_jwks_json)
        header = get_unverified_header(token)
        key_id = header.get("kid")
        keys = jwks.get("keys", [])
        if key_id:
            matches = [key for key in keys if key.get("kid") == key_id]
        else:
            matches = keys
        if not matches:
            raise ValueError("No matching JWKS key")
        return RSAAlgorithm.from_jwk(json.dumps(matches[0]))

    if settings.jwt_jwks_url:
        return PyJWKClient(settings.jwt_jwks_url).get_signing_key_from_jwt(token).key

    raise ValueError("JWKS configuration is required")


def require_any_role(identity: RequestIdentity, allowed_roles: set[str]) -> RequestIdentity:
    if set(identity.roles).intersection(allowed_roles):
        return identity
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient role",
    )


def _dev_keys_enabled() -> bool:
    settings = get_settings()
    return settings.auth_mode != "jwt" and settings.allow_dev_api_keys


async def get_current_identity(
    x_api_key: str | None = Header(default=None),
    authorization: str | None = Header(default=None),
    x_request_id: str | None = Header(default=None),
) -> RequestIdentity:
    request_id = x_request_id or str(uuid4())
    token = _extract_token(x_api_key, authorization)
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API credentials",
        )

    if authorization and authorization.lower().startswith("bearer "):
        if token in get_settings().api_keys.values():
            if not _dev_keys_enabled():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Development API keys are disabled",
                )
            identity = _identity_for_token(token, request_id)
        else:
            identity = _identity_for_jwt(token, request_id)
    else:
        if not _dev_keys_enabled():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Development API keys are disabled",
            )
        identity = _identity_for_token(token, request_id)

    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials",
        )

    return identity
