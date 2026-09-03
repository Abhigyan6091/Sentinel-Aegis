import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jwt.algorithms import RSAAlgorithm

from app.core.config import get_settings
from app.core.identity import RequestIdentity
from app.core.security import require_any_role
from app.main import create_app


def make_jwt_config(monkeypatch, issuer: str = "https://issuer.example") -> rsa.RSAPrivateKey:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    public_jwk["kid"] = "test-key"

    monkeypatch.setenv("AEGIS_AUTH_MODE", "jwt")
    monkeypatch.setenv("AEGIS_ALLOW_DEV_API_KEYS", "false")
    monkeypatch.setenv("AEGIS_JWT_ISSUER", issuer)
    monkeypatch.setenv("AEGIS_JWT_AUDIENCE", "sentinel-aegis")
    monkeypatch.setenv("AEGIS_JWT_JWKS_JSON", json.dumps({"keys": [public_jwk]}))
    get_settings.cache_clear()
    return key


def encode_token(
    key: rsa.RSAPrivateKey,
    *,
    issuer: str = "https://issuer.example",
    tenant_id: str = "tenant-production",
    roles: list[str] | None = None,
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "user-production",
            "iss": issuer,
            "aud": "sentinel-aegis",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=5),
            "tenant_id": tenant_id,
            "application_id": "app-production",
            "roles": roles or ["security_analyst"],
        },
        key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )


def test_me_accepts_valid_jwt_identity(monkeypatch):
    key = make_jwt_config(monkeypatch)
    token = encode_token(key)
    client = TestClient(create_app())

    response = client.get("/api/v1/me", headers={"authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["user_id"] == "user-production"
    assert response.json()["tenant_id"] == "tenant-production"
    assert response.json()["application_id"] == "app-production"
    assert response.json()["roles"] == ["security_analyst"]


def test_me_rejects_jwt_with_wrong_issuer(monkeypatch):
    key = make_jwt_config(monkeypatch)
    token = encode_token(key, issuer="https://evil.example")
    client = TestClient(create_app())

    response = client.get("/api/v1/me", headers={"authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid JWT credentials"


def test_dev_api_keys_can_be_disabled_for_production(monkeypatch):
    make_jwt_config(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/api/v1/me", headers={"x-api-key": "dev-aegis-key"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Development API keys are disabled"


def test_jwt_auth_mode_rejects_dev_api_keys_even_when_allowed(monkeypatch):
    key = make_jwt_config(monkeypatch)
    del key
    monkeypatch.setenv("AEGIS_ALLOW_DEV_API_KEYS", "true")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/api/v1/me", headers={"x-api-key": "dev-aegis-key"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Development API keys are disabled"


def test_jwt_tenants_are_isolated_on_application_apis(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'jwt.db'}")
    key = make_jwt_config(monkeypatch)
    client = TestClient(create_app())
    first_token = encode_token(key, tenant_id="tenant-production-a")
    second_token = encode_token(key, tenant_id="tenant-production-b")

    created = client.post(
        "/api/v1/applications",
        headers={"authorization": f"Bearer {first_token}"},
        json={"name": "Production Agent", "description": "Tenant A"},
    )
    assert created.status_code == 201

    other = client.get(
        "/api/v1/applications",
        headers={"authorization": f"Bearer {second_token}"},
    )
    original = client.get(
        "/api/v1/applications",
        headers={"authorization": f"Bearer {first_token}"},
    )

    assert other.status_code == 200
    assert other.json() == []
    assert original.status_code == 200
    assert original.json()[0]["name"] == "Production Agent"


def test_role_authorization_accepts_matching_role():
    identity = RequestIdentity(
        request_id="request",
        user_id="user",
        tenant_id="tenant",
        roles=["security_analyst"],
    )

    assert require_any_role(identity, {"security_analyst", "admin"}) == identity


def test_role_authorization_rejects_missing_role():
    identity = RequestIdentity(
        request_id="request",
        user_id="user",
        tenant_id="tenant",
        roles=["viewer"],
    )

    with pytest.raises(HTTPException) as exc:
        require_any_role(identity, {"security_analyst", "admin"})

    assert exc.value.status_code == 403
    assert exc.value.detail == "Insufficient role"
