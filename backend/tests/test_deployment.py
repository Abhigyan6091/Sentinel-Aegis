"""Phase P8: the deployment manifests and operator docs must stay honest.

These assert the security posture the deployment guide promises, so a manifest edit that
quietly drops a control fails CI instead of shipping.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
K8S_DIR = REPO_ROOT / "infra" / "k8s"
DOCS_DIR = REPO_ROOT / "docs"


def load_manifest(name: str) -> dict:
    return yaml.safe_load((K8S_DIR / name).read_text())


@pytest.mark.parametrize(
    "name",
    [
        "namespace.yaml",
        "configmap.yaml",
        "secret.example.yaml",
        "deployment.yaml",
        "service.yaml",
        "networkpolicy.yaml",
        "poddisruptionbudget.yaml",
    ],
)
def test_kubernetes_manifests_are_valid_yaml(name):
    manifest = load_manifest(name)

    assert manifest["apiVersion"]
    assert manifest["kind"]
    assert manifest["metadata"]["name"]


def test_deployment_runs_as_non_root_with_a_read_only_root_filesystem():
    spec = load_manifest("deployment.yaml")["spec"]["template"]["spec"]

    assert spec["securityContext"]["runAsNonRoot"] is True
    assert spec["securityContext"]["runAsUser"] == 10001

    for container in [*spec["containers"], *spec["initContainers"]]:
        security = container["securityContext"]
        assert security["allowPrivilegeEscalation"] is False
        assert security["readOnlyRootFilesystem"] is True
        assert security["capabilities"]["drop"] == ["ALL"]


def test_deployment_applies_migrations_before_serving_traffic():
    spec = load_manifest("deployment.yaml")["spec"]

    init_container = spec["template"]["spec"]["initContainers"][0]
    assert init_container["command"] == ["alembic", "upgrade", "head"]
    # Old pods keep serving until the new ones are ready.
    assert spec["strategy"]["rollingUpdate"]["maxUnavailable"] == 0


def test_deployment_has_health_probes():
    container = load_manifest("deployment.yaml")["spec"]["template"]["spec"]["containers"][0]

    assert container["readinessProbe"]["httpGet"]["path"] == "/health"
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"


def test_production_configmap_disables_development_credentials():
    data = load_manifest("configmap.yaml")["data"]

    assert data["AEGIS_ENVIRONMENT"] == "production"
    assert data["AEGIS_ALLOW_DEV_API_KEYS"] == "false"
    assert data["AEGIS_AUTH_MODE"] == "jwt"
    assert data["AEGIS_AUTO_CREATE_SCHEMA"] == "false"
    assert "*" not in data["AEGIS_CORS_ALLOW_ORIGINS"]


def test_configmap_holds_no_credentials():
    """Secrets belong in the Secret or a secrets manager, never in a ConfigMap."""
    data = load_manifest("configmap.yaml")["data"]

    for key, value in data.items():
        if key.endswith(("_API_KEY", "_PASSWORD", "_SECRET")):
            pytest.fail(f"ConfigMap key {key} looks like a credential")
        assert "://aegis:" not in value, f"ConfigMap key {key} embeds a database password"


def test_secrets_are_mounted_as_files_and_referenced_indirectly():
    spec = load_manifest("deployment.yaml")["spec"]["template"]["spec"]
    container = spec["containers"][0]
    env = {item["name"]: item.get("value") for item in container["env"]}

    assert env["AEGIS_ANTHROPIC_API_KEY"] == "secret://file/anthropic_api_key"
    assert env["AEGIS_DATABASE_URL"] == "secret://file/database_url"

    mount = next(m for m in container["volumeMounts"] if m["name"] == "secrets")
    assert mount["readOnly"] is True
    assert mount["mountPath"] == "/run/secrets"


def test_network_policy_denies_by_default():
    spec = load_manifest("networkpolicy.yaml")["spec"]

    assert set(spec["policyTypes"]) == {"Ingress", "Egress"}
    assert spec["ingress"], "an empty ingress list would deny the ingress controller too"
    assert spec["egress"]


def test_backend_dockerfile_runs_unprivileged_without_test_tooling():
    dockerfile = (REPO_ROOT / "backend" / "Dockerfile").read_text()

    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    # Installing the dev extra would ship pytest and ruff into production.
    assert '".[dev]"' not in dockerfile


def test_compose_backend_is_hardened():
    compose = yaml.safe_load((REPO_ROOT / "docker-compose.yml").read_text())
    backend = compose["services"]["backend"]

    assert backend["read_only"] is True
    assert "no-new-privileges:true" in backend["security_opt"]


def test_ci_blocks_unsafe_dependencies_and_container_regressions():
    workflow = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text())
    steps = [
        step
        for job in workflow["jobs"].values()
        for step in job["steps"]
    ]
    rendered = yaml.safe_dump(steps)

    assert "pip-audit" in rendered
    assert "bandit" in rendered
    assert "npm audit" in rendered
    assert "trivy-action" in rendered
    assert "app.cli.regression_suite" in rendered
    assert "app.cli.migration_check" in rendered

    # A scanner that cannot fail the build is not a gate.
    trivy_steps = [
        step for step in steps if "trivy-action" in str(step.get("uses", ""))
    ]
    assert trivy_steps
    assert all(step["with"]["exit-code"] == "1" for step in trivy_steps)


@pytest.mark.parametrize(
    ("document", "sections"),
    [
        (
            "deployment.md",
            [
                "## 2. Local deployment",
                "## 4. Secrets",
                "## 5. Kubernetes deployment",
                "## 6. Database backup and restore",
                "Migration smoke test",
            ],
        ),
        (
            "runbook.md",
            ["## Deploy", "## Rollback", "## Backup and restore", "## Incident triage"],
        ),
    ],
)
def test_operator_documentation_covers_required_procedures(document, sections):
    content = (DOCS_DIR / document).read_text()

    for section in sections:
        assert section in content, f"{document} is missing '{section}'"
