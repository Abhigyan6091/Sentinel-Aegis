# Sentinel Aegis Deployment Guide

Date: 2026-09-03

This guide takes a clean environment to a running Sentinel Aegis deployment. It covers
local Docker Compose, a Kubernetes production deployment, secrets, and the safety checks
that run before the service accepts traffic.

## 1. Prerequisites

| Component | Version | Notes |
| --- | --- | --- |
| Python | 3.12+ | Backend runtime |
| Node | 20+ | Console build |
| PostgreSQL | 16 | Primary datastore; SQLite is rejected in production |
| Redis | 7 | Rate limiting |
| Qdrant | 1.12+ | Vector store when `AEGIS_RAG_VECTOR_STORE=qdrant` |
| Kubernetes | 1.28+ | For the manifests in `infra/k8s` |

## 2. Local deployment (Docker Compose)

```bash
cp .env.example .env          # then edit any values you need
docker compose up --build
```

Services: API on `:8000`, console on `:3000`, Prometheus on `:9090`, Grafana on `:3001`,
Postgres on `:5432`, Qdrant on `:6333`, Redpanda on `:9092`.

Verify:

```bash
curl -s localhost:8000/health
curl -s -H "x-api-key: dev-aegis-key" localhost:8000/api/v1/findings
```

## 3. Configuration

All backend settings use the `AEGIS_` prefix. See `.env.example` for the full list. The
settings that matter most for a production deployment:

| Setting | Production value | Why |
| --- | --- | --- |
| `AEGIS_ENVIRONMENT` | `production` | Enables the preflight checks and HSTS, hides API docs |
| `AEGIS_AUTH_MODE` | `jwt` | Rejects static development keys |
| `AEGIS_ALLOW_DEV_API_KEYS` | `false` | Development keys grant full tenant access |
| `AEGIS_AUTO_CREATE_SCHEMA` | `false` | Schema changes go through reviewed migrations |
| `AEGIS_CORS_ALLOW_ORIGINS` | explicit list | Wildcards are rejected |
| `AEGIS_MAX_REQUEST_BYTES` | `1000000` | Bodies above the limit are refused with 413 |
| `AEGIS_JWT_ISSUER` / `_AUDIENCE` / `_JWKS_URL` | your IdP | Required for JWT validation |

### Preflight checks

`create_app()` calls `verify_production_config()` before serving. When
`AEGIS_ENVIRONMENT=production`, an unsafe setting **fails the boot** rather than
serving traffic — the pod will crash-loop with every problem listed at once. This is
intentional: a misconfigured production deployment is an incident, not a warning.

## 4. Secrets

Never put credentials in the ConfigMap, the compose file, or the image. Any secret-bearing
setting accepts a reference instead of a literal:

```
secret://file/database_url            # {AEGIS_SECRETS_FILE_DIR}/database_url
secret://env/OPENAI_API_KEY           # another environment variable
secret://aws/providers                # AWS Secrets Manager, whole secret string
secret://aws/providers#openai_key     # one key from a JSON secret
```

References are resolved once at startup. A missing or unreadable secret fails the boot
loudly rather than silently running without a credential. Values without the `secret://`
prefix are treated as literals, so local development needs no secrets backend.

Resolvable settings: `database_url`, `redis_url`, `openai_api_key`, `anthropic_api_key`,
`jwt_jwks_json`.

For AWS, install the extra and set the region:

```bash
pip install ".[aws]"
export AEGIS_SECRETS_PROVIDER=aws
export AEGIS_AWS_SECRETS_REGION=us-east-1
export AEGIS_AWS_SECRETS_PREFIX=sentinel-aegis/
```

In Kubernetes, prefer projecting secrets to files (External Secrets Operator or Vault
Agent write into `/run/secrets`) and use `secret://file/...` references.

## 5. Kubernetes deployment

Manifests live in `infra/k8s`:

| File | Purpose |
| --- | --- |
| `namespace.yaml` | `sentinel-aegis` namespace |
| `configmap.yaml` | Non-secret configuration |
| `secret.example.yaml` | Template — generate the real Secret at deploy time |
| `deployment.yaml` | Backend Deployment with a migration init container |
| `service.yaml` | ClusterIP service |
| `networkpolicy.yaml` | Default-deny ingress and egress |
| `poddisruptionbudget.yaml` | Keeps one replica during voluntary disruption |

```bash
kubectl apply -f infra/k8s/namespace.yaml
kubectl apply -f infra/k8s/configmap.yaml
# Create the Secret from your secrets manager, not from the example file:
kubectl -n sentinel-aegis create secret generic sentinel-aegis-secrets \
  --from-literal=database_url="postgresql+asyncpg://aegis:...@postgres:5432/aegisai" \
  --from-literal=redis_url="redis://redis:6379/0" \
  --from-literal=anthropic_api_key="..."
kubectl apply -f infra/k8s/service.yaml
kubectl apply -f infra/k8s/networkpolicy.yaml
kubectl apply -f infra/k8s/poddisruptionbudget.yaml
kubectl apply -f infra/k8s/deployment.yaml

kubectl -n sentinel-aegis rollout status deployment/sentinel-aegis-backend
```

Migrations run in an init container, so the schema is fully applied before any new pod
serves traffic. With `maxUnavailable: 0` the old pods keep serving until the new ones are
ready, which means **migrations must be backward compatible with the previous release**:
add columns before you read them, and drop them only in a later release.

### Container security posture

The image runs as uid 10001 with no shell access to a writable root filesystem. The
Deployment sets `runAsNonRoot`, `readOnlyRootFilesystem`, `allowPrivilegeEscalation:
false`, drops all capabilities, and mounts an `emptyDir` at `/tmp` for scratch space.
The production image contains no test or lint tooling.

## 6. Database backup and restore

### Backup

Take a nightly logical backup plus continuous WAL archiving for point-in-time recovery.

```bash
# Nightly logical backup (compressed custom format)
pg_dump --format=custom --compress=9 \
  --dbname="$DATABASE_URL" \
  --file="aegisai-$(date +%F).dump"

# Verify the dump is readable before trusting it
pg_restore --list "aegisai-$(date +%F).dump" > /dev/null
```

Store dumps encrypted, off-cluster, with a retention period matching your data policy.
Findings, traces, and security events contain attack payloads and redacted customer
context — treat backups at the same sensitivity as the live database.

### Restore

```bash
# 1. Stop writers
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=0

# 2. Restore into a fresh database
createdb aegisai_restored
pg_restore --dbname=aegisai_restored --clean --if-exists aegisai-2026-09-03.dump

# 3. Confirm the schema is at the expected revision
AEGIS_DATABASE_URL=postgresql+asyncpg://.../aegisai_restored alembic current

# 4. Point the service at the restored database and scale back up
kubectl -n sentinel-aegis scale deployment/sentinel-aegis-backend --replicas=2
```

**Rehearse restores.** A backup that has never been restored is not a backup. Restore to
a scratch database monthly and confirm `alembic current` matches the deployed revision.

### Migration smoke test

Before promoting a release, prove the schema can be built, reverted, and rebuilt:

```bash
cd backend
AEGIS_DATABASE_URL=postgresql+asyncpg://... python -m app.cli.migration_check
```

This runs `upgrade head` → `downgrade base` → `upgrade head`. A migration that cannot be
reversed is a deploy that cannot be rolled back. CI runs this on every change.

## 7. Continuous security gates

CI blocks a merge when any of these fail:

| Gate | Command | Blocks on |
| --- | --- | --- |
| Regression suite | `python -m app.cli.regression_suite` | A previously fixed attack works again |
| Security gate | `python -m app.cli.security_gate` | New findings or a score below threshold |
| Migration smoke test | `python -m app.cli.migration_check` | Irreversible migrations |
| Dependency audit | `pip-audit --strict`, `npm audit --audit-level=high` | Known vulnerable dependencies |
| Static analysis | `bandit -r app` | Insecure code patterns |
| Container scan | Trivy image scan | CRITICAL/HIGH fixable CVEs in the image |
| Secret scan | Trivy filesystem scan | Committed credentials and misconfiguration |

Gate and regression reports are uploaded as build artifacts on every run.

## 8. Post-deploy verification

```bash
# Health and security headers
curl -sI https://api.example.com/health | grep -Ei 'content-security-policy|x-frame|strict-transport'

# API docs must be hidden in production
curl -s -o /dev/null -w '%{http_code}\n' https://api.example.com/docs   # expect 404

# Development keys must be rejected
curl -s -o /dev/null -w '%{http_code}\n' \
  -H 'x-api-key: dev-aegis-key' https://api.example.com/api/v1/findings # expect 401

# Regression suite against the deployed build
kubectl -n sentinel-aegis exec deploy/sentinel-aegis-backend -- \
  python -m app.cli.regression_suite
```

See `docs/runbook.md` for deploy, rollback, backup, and incident procedures.
