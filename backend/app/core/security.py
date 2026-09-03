from uuid import uuid4

from fastapi import Header, HTTPException, status

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

    identity = _identity_for_token(token, request_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials",
        )

    return identity
