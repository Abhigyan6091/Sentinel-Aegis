from fastapi.testclient import TestClient

from app.main import create_app


def test_me_rejects_missing_credentials():
    response = TestClient(create_app()).get("/api/v1/me")

    assert response.status_code == 401


def test_me_rejects_invalid_api_key():
    response = TestClient(create_app()).get("/api/v1/me", headers={"x-api-key": "wrong"})

    assert response.status_code == 401


def test_me_returns_identity_for_valid_api_key():
    client = TestClient(create_app())

    response = client.get("/api/v1/me", headers={"x-api-key": "dev-aegis-key"})

    assert response.status_code == 200
    assert response.json() == {
        "request_id": response.json()["request_id"],
        "user_id": "user-demo",
        "tenant_id": "tenant-demo",
        "application_id": None,
        "roles": ["support_agent"],
    }
