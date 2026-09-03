from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def make_client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'redteam.db'}")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_campaign_api_runs_attacks_through_runtime(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.post(
        "/api/v1/red-team/campaigns",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "name": "Smoke Campaign",
            "categories": ["prompt_injection", "tool_abuse", "rag_poisoning"],
            "attack_count": 3,
            "mutation_depth": 1,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["campaign"]["name"] == "Smoke Campaign"
    assert body["score"]["attacks_executed"] == 3
    assert body["score"]["successful_attacks"] == 0
    assert body["score"]["overall"] == 100
    assert len(body["results"]) == 3
    assert all(result["trace"] for result in body["results"])


def test_latest_campaign_and_findings_are_tenant_scoped(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    client.post(
        "/api/v1/red-team/campaigns",
        headers={"x-api-key": "dev-aegis-key"},
        json={"name": "Tenant Demo", "attack_count": 2, "mutation_depth": 1},
    )

    latest = client.get(
        "/api/v1/red-team/campaigns/latest",
        headers={"x-api-key": "dev-aegis-key"},
    )
    other_latest = client.get(
        "/api/v1/red-team/campaigns/latest",
        headers={"x-api-key": "dev-other-key"},
    )
    findings = client.get(
        "/api/v1/red-team/findings",
        headers={"x-api-key": "dev-aegis-key"},
    )

    assert latest.status_code == 200
    assert latest.json()["campaign"]["tenant_id"] == "tenant-demo"
    assert other_latest.status_code == 404
    assert findings.status_code == 200
    assert findings.json() == []


def test_attack_catalog_lists_deterministic_seeds(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    response = client.get("/api/v1/red-team/attacks", headers={"x-api-key": "dev-aegis-key"})

    assert response.status_code == 200
    categories = {attack["category"] for attack in response.json()}
    assert {"prompt_injection", "tool_abuse", "rag_poisoning"} <= categories
