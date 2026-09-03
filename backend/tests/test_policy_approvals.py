from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def make_client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path / 'policy.db'}")
    get_settings.cache_clear()
    return TestClient(create_app())


def test_policy_crud_and_activation_is_tenant_scoped(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    created = client.post(
        "/api/v1/policies",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "name": "Strict Tool Policy",
            "document": {
                "tools": {
                    "search_customer": {
                        "risk": "MEDIUM",
                        "allowed_roles": ["admin"],
                        "require_approval": False,
                    },
                    "refund_order": {
                        "risk": "HIGH",
                        "allowed_roles": ["admin"],
                        "require_approval": True,
                    },
                }
            },
        },
    )
    assert created.status_code == 201
    policy_id = created.json()["id"]
    assert created.json()["version"] == 1
    assert created.json()["status"] == "draft"

    activated = client.post(
        f"/api/v1/policies/{policy_id}/activate",
        headers={"x-api-key": "dev-aegis-key"},
    )
    assert activated.status_code == 200
    assert activated.json()["status"] == "active"

    other_tenant = client.get("/api/v1/policies", headers={"x-api-key": "dev-other-key"})
    same_tenant = client.get("/api/v1/policies", headers={"x-api-key": "dev-aegis-key"})

    assert other_tenant.status_code == 200
    assert other_tenant.json() == []
    assert same_tenant.status_code == 200
    assert same_tenant.json()[0]["id"] == policy_id


def test_active_policy_controls_support_agent_tool_authorization(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    created = client.post(
        "/api/v1/policies",
        headers={"x-api-key": "dev-aegis-key"},
        json={
            "name": "Deny Customer Search",
            "document": {
                "tools": {
                    "search_customer": {
                        "risk": "HIGH",
                        "allowed_roles": ["admin"],
                        "require_approval": False,
                    }
                }
            },
        },
    )
    client.post(
        f"/api/v1/policies/{created.json()['id']}/activate",
        headers={"x-api-key": "dev-aegis-key"},
    )

    response = client.post(
        "/api/v1/support/chat",
        headers={"x-api-key": "dev-aegis-key"},
        json={"message": "Show customer CUST-001 profile details."},
    )

    assert response.status_code == 200
    assert response.json()["tool_calls"][0]["decision"] == "DENY"


def test_high_risk_tool_call_creates_approval_request(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)

    chat = client.post(
        "/api/v1/support/chat",
        headers={"x-api-key": "dev-aegis-key"},
        json={"message": "Please refund order ORD-1001 for customer CUST-001."},
    )
    approvals = client.get(
        "/api/v1/approvals",
        headers={"x-api-key": "dev-aegis-key"},
    )

    assert chat.status_code == 200
    assert chat.json()["tool_calls"][0]["decision"] == "REQUIRE_APPROVAL"
    assert approvals.status_code == 200
    assert approvals.json()[0]["tool_name"] == "refund_order"
    assert approvals.json()[0]["status"] == "pending"
    assert approvals.json()[0]["request_id"] == chat.json()["request_id"]


def test_approval_decision_updates_status(monkeypatch, tmp_path):
    client = make_client(monkeypatch, tmp_path)
    client.post(
        "/api/v1/support/chat",
        headers={"x-api-key": "dev-aegis-key"},
        json={"message": "Please refund order ORD-1001 for customer CUST-001."},
    )
    approval = client.get("/api/v1/approvals", headers={"x-api-key": "dev-aegis-key"}).json()[0]

    decided = client.post(
        f"/api/v1/approvals/{approval['id']}/decide",
        headers={"x-api-key": "dev-aegis-key"},
        json={"decision": "approved", "reason": "Manager reviewed the refund."},
    )

    assert decided.status_code == 200
    assert decided.json()["status"] == "approved"
    assert decided.json()["decision_reason"] == "Manager reviewed the refund."
