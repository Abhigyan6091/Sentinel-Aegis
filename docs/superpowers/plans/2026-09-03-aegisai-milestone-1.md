# AegisAI Milestone 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the runnable AegisAI foundation: FastAPI backend, tenant-aware persistence, basic auth, rate limiting, frontend security-console shell, Docker Compose, CI, and documentation.

**Architecture:** A single FastAPI backend owns identity, tenancy, persistence, and security-domain APIs. A Next.js frontend consumes real backend status/application APIs and renders empty states instead of invented security metrics. Compose starts the full local platform stack while application code only wires dependencies used in this milestone.

**Tech Stack:** Python 3.12, FastAPI, Pydantic Settings, SQLAlchemy async, Alembic, pytest, Next.js 15, TypeScript, Tailwind CSS, lucide-react, Docker Compose, PostgreSQL, Redis, Qdrant, Redpanda, Prometheus, Grafana.

**Spec:** `docs/superpowers/specs/2026-09-03-aegisai-phase-1-design.md`

## Global Constraints

- Do not hard-code secrets or security results.
- Every tenant-owned object must include `tenant_id`.
- Protected endpoints must fail closed for missing or invalid identity.
- Frontend metrics must come from backend APIs or be explicit empty states.
- Migrations are the source of truth for database schema.
- Docker Compose must remain practical for local development.
- The roadmap is reduced to five milestones.

---

### Task 1: Backend Project, Config, Auth, And Rate Limiting

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/routes/health.py`
- Create: `backend/app/api/routes/identity.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/identity.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/services/rate_limit.py`
- Create: `backend/tests/test_config.py`
- Create: `backend/tests/test_auth.py`
- Create: `backend/tests/test_rate_limit.py`

**Interfaces:**
- Produces: `Settings`, `get_settings()`, `RequestIdentity`, `get_current_identity()`, `InMemoryRateLimiter.allow()`.
- Consumes: environment variables prefixed with `AEGIS_`.

- [ ] **Step 1: Write failing backend tests**

```python
# backend/tests/test_auth.py
from fastapi.testclient import TestClient
from app.main import create_app


def test_me_rejects_missing_credentials():
    response = TestClient(create_app()).get("/api/v1/me")
    assert response.status_code == 401


def test_me_returns_identity_for_valid_api_key():
    client = TestClient(create_app())
    response = client.get("/api/v1/me", headers={"x-api-key": "dev-aegis-key"})
    assert response.status_code == 200
    assert response.json()["tenant_id"] == "tenant-demo"
```

```python
# backend/tests/test_rate_limit.py
import pytest
from app.services.rate_limit import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    assert await limiter.allow("user-1") is True
    assert await limiter.allow("user-1") is True
    assert await limiter.allow("user-1") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && pytest tests/test_auth.py tests/test_rate_limit.py -q`
Expected: FAIL because `app.main` and `app.services.rate_limit` do not exist.

- [ ] **Step 3: Implement minimal backend foundation**

Create FastAPI app factory, settings, identity extraction from `x-api-key` or bearer token, and an in-memory rate limiter.

- [ ] **Step 4: Run task tests to verify they pass**

Run: `cd backend && pytest tests/test_config.py tests/test_auth.py tests/test_rate_limit.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add backend foundation"
```

### Task 2: Database Models, Migration, And Tenant-Scoped Applications API

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/20260903_0001_foundation.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/foundation.py`
- Create: `backend/app/schemas/applications.py`
- Create: `backend/app/api/routes/applications.py`
- Create: `backend/tests/test_applications.py`

**Interfaces:**
- Consumes: `RequestIdentity` from Task 1.
- Produces: `GET /api/v1/applications`, `POST /api/v1/applications`, SQLAlchemy `Base`, async session dependency.

- [ ] **Step 1: Write failing tenant isolation test**

```python
from fastapi.testclient import TestClient
from app.main import create_app


def test_applications_are_scoped_to_authenticated_tenant():
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/test_applications.py -q`
Expected: FAIL because the applications API does not exist.

- [ ] **Step 3: Implement models, migration, and applications API**

Use SQLite for fast local tests by default and PostgreSQL via `AEGIS_DATABASE_URL` in Compose. Define all minimum tables in the first Alembic migration.

- [ ] **Step 4: Run migration and API tests**

Run: `cd backend && pytest tests/test_applications.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend
git commit -m "feat: add tenant scoped persistence"
```

### Task 3: Frontend Security Console Shell

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/app/globals.css`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/applications/page.tsx`
- Create: `frontend/components/sidebar.tsx`
- Create: `frontend/components/status-card.tsx`
- Create: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: backend `GET /health` and `GET /api/v1/applications`.
- Produces: dashboard shell and applications page with real empty states.

- [ ] **Step 1: Create frontend app shell**

Use compact dark security-console styling, lucide icons in navigation, and no invented metrics.

- [ ] **Step 2: Run frontend verification**

Run: `cd frontend && npm install && npm run lint && npm run typecheck && npm run build`
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend
git commit -m "feat: add frontend console shell"
```

### Task 4: Local Infrastructure, CI, And Documentation

**Files:**
- Create: `.env.example`
- Create: `.gitignore`
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `infra/prometheus/prometheus.yml`
- Create: `infra/grafana/provisioning/datasources/prometheus.yml`
- Create: `.github/workflows/ci.yml`
- Create: `README.md`

**Interfaces:**
- Consumes: backend/frontend app commands.
- Produces: local stack and CI workflow.

- [ ] **Step 1: Add Docker and environment files**

Compose includes frontend, backend, postgres, redis, qdrant, redpanda, prometheus, and grafana with local defaults.

- [ ] **Step 2: Add CI workflow**

Run backend pytest plus frontend lint, typecheck, and build.

- [ ] **Step 3: Write README**

Document project overview, architecture, reduced five-milestone roadmap, setup, testing, limitations, and current APIs.

- [ ] **Step 4: Run final verification**

Run: `cd backend && pytest -q`
Run: `cd frontend && npm run lint && npm run typecheck && npm run build`
Run: `docker compose config`
Expected: all commands exit 0.

- [ ] **Step 5: Commit**

```bash
git add .env.example .gitignore docker-compose.yml backend/Dockerfile frontend/Dockerfile infra .github README.md docs
git commit -m "chore: add local platform infrastructure"
```
