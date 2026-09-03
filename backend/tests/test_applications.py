from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_applications_are_scoped_to_authenticated_tenant(monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    get_settings.cache_clear()
    client = TestClient(create_app())

    first = client.post(
        "/api/v1/applications",
        headers={"x-api-key": "dev-aegis-key"},
        json={"name": "Support Agent", "description": "Demo target"},
    )
    assert first.status_code == 201

    other = client.get("/api/v1/applications", headers={"x-api-key": "dev-other-key"})
    assert other.status_code == 200
    assert other.json() == []

    original = client.get("/api/v1/applications", headers={"x-api-key": "dev-aegis-key"})
    assert original.status_code == 200
    assert original.json()[0]["name"] == "Support Agent"
