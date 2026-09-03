# AegisAI Phase 1 Foundation Design

Date: 2026-09-03

## Purpose

Phase 1 creates the local foundation for AegisAI, a production-oriented AI application security and red-teaming platform. This phase does not attempt to implement the full runtime guardrail system or red-team engine. It establishes a runnable monorepo, core service boundaries, local infrastructure, identity primitives, persistence, and the first dashboard shell so later phases can add security behavior without reworking the base.

## Scope

Phase 1 includes:

- A monorepo layout for backend, frontend, infrastructure, documentation, and CI.
- A FastAPI backend with typed configuration, health endpoints, request identity extraction, basic authentication, and database connectivity.
- PostgreSQL schema management using Alembic migrations.
- Core SQLAlchemy models for tenants, users, applications, policies, guardrails, campaigns, attacks, results, findings, traces, tool calls, security events, and evaluation runs.
- A Redis-backed rate limiter abstraction with a deterministic local fallback for tests.
- A Next.js, TypeScript, Tailwind CSS frontend shell with security-console navigation.
- Docker Compose services for frontend, backend, postgres, redis, qdrant, redpanda, prometheus, and grafana.
- `.env.example`, project README, and GitHub Actions for backend and frontend checks.
- Focused tests for configuration, authentication, tenant-aware model fields, and rate limiting.

Phase 1 excludes:

- Real LLM provider calls.
- RAG ingestion/retrieval behavior.
- Agent tool execution.
- Guardrail detection logic beyond typed interfaces needed by the foundation.
- Attack generation, mutation, evaluation, scoring, or dashboard metrics.
- Production deployment concerns beyond local Docker and CI checks.

## Repository Layout

```text
.
├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── package.json
│   └── Dockerfile
├── infra/
│   ├── prometheus/
│   └── grafana/
├── docs/
├── .github/workflows/
├── docker-compose.yml
├── .env.example
└── README.md
```

The backend owns security-domain behavior and persistence. The frontend consumes backend APIs and does not invent metrics or security results. Infrastructure files remain lightweight and local-development-oriented.

## Backend Architecture

The backend will be a single FastAPI service. It will expose:

- `GET /health` for basic liveness.
- `GET /ready` for dependency-aware readiness.
- `GET /api/v1/me` to return authenticated identity context.
- `GET /api/v1/applications` and `POST /api/v1/applications` for the first tenant-scoped resource flow.

Core modules:

- `app/core/config.py`: Pydantic settings loaded from environment variables.
- `app/core/identity.py`: request identity model containing `request_id`, `user_id`, `tenant_id`, `application_id`, and roles.
- `app/core/security.py`: API-key/JWT-style authentication dependency. Phase 1 accepts configured development API keys and a simple bearer-token shape from env; provider-specific identity integrations are outside this phase.
- `app/db/session.py`: async SQLAlchemy engine/session creation.
- `app/models/`: ORM models with tenant fields where applicable.
- `app/services/rate_limit.py`: interface and Redis implementation with test fallback.

Security decisions should fail closed where the foundation already has enough information. For example, missing auth returns `401`, missing tenant context returns `403`, and malformed resource creation returns `422`.

## Data Model

All security objects that belong to a customer or app include `tenant_id`. Application-specific records also include `application_id` where meaningful.

Minimum models:

- `Tenant`: organization boundary.
- `User`: authenticated principal, roles, tenant.
- `Application`: registered AI application under a tenant.
- `Policy`: declarative policy document stored as JSON.
- `Guardrail`: configured guardrail metadata.
- `AttackCampaign`: campaign config and status.
- `Attack`: canonical attack seed or scenario.
- `AttackVariant`: generated or mutated attack with optional parent lineage.
- `AttackResult`: observed result and evaluation summary.
- `Finding`: vulnerability-management record.
- `Trace`: request or attack trace envelope.
- `ToolCall`: audited tool authorization/execution record.
- `SecurityEvent`: structured security event stream record.
- `EvaluationRun`: benchmark/security gate run.

Migrations are the source of truth. The application must not rely on manually created tables.

## Frontend Architecture

The frontend will use Next.js with TypeScript and Tailwind CSS. shadcn/ui-compatible component structure will be prepared, but Phase 1 will keep dependencies practical and only add components needed for the shell.

First screen:

- Persistent left navigation with the final product sections: Dashboard, Applications, Attack Campaigns, Attack Explorer, Findings, Policies, Traces, Guardrails, Evaluations, Observability, Settings.
- Dashboard overview cards wired to backend status or clearly marked empty states.
- Applications page for listing and creating registered applications.

The UI must look like a focused security operations product, not a marketing landing page. Any metric shown in Phase 1 must either come from a real backend endpoint or be presented as an empty state.

## Local Infrastructure

`docker-compose.yml` will provide:

- `backend`: FastAPI app.
- `frontend`: Next.js app.
- `postgres`: primary relational store.
- `redis`: rate limiting and future cache.
- `qdrant`: reserved for Phase 2 RAG.
- `redpanda`: reserved for Phase 8 event streaming.
- `prometheus`: reserved for metrics scraping.
- `grafana`: reserved for dashboards.

Services that are not actively used in Phase 1 should still start with stable defaults, but application code should not pretend to use them before their phase arrives.

## Configuration

`.env.example` will include:

- Backend app settings.
- Database URL.
- Redis URL.
- Development auth token/API key settings.
- Frontend API base URL.
- Reserved environment variable names for future OpenAI, Anthropic, and local provider configuration.

No secrets will be committed.

## CI

GitHub Actions will run:

- Backend install, lint, and tests.
- Frontend install, lint, typecheck, and build.

The AegisAI security gate will be introduced in Phase 10 after the red-team engine and evaluation runner exist.

## Testing Strategy

Phase 1 tests focus on behavior that can regress quickly:

- Settings load required defaults and environment overrides.
- Auth rejects missing/invalid credentials and returns identity for valid credentials.
- Tenant-scoped resources cannot be read across tenants.
- Rate limiting allows requests under the configured limit and blocks requests over it.
- Migrations create the expected tables.

Tests should use deterministic local dependencies where possible. Redis/Postgres integration can run under Docker Compose or test containers if the local environment supports it; otherwise, unit-level fallbacks cover the foundation behavior.

## Risks And Tradeoffs

- The brief requests many infrastructure components. Phase 1 will include compose services for the required stack but only wire application code to Postgres and Redis initially. This keeps the setup honest and avoids fake integrations.
- JWT-style auth in Phase 1 is intentionally simple. It provides identifiable request context without committing to an enterprise identity provider too early.
- The database model will start broad but shallow. Later phases can add columns and indexes based on actual guardrail, RAG, and red-team workflows.
- The frontend shell will show product structure before all pages have real data. Empty states must be explicit, and no security metrics may be hard-coded.

## Definition Of Done

Phase 1 is complete when:

- `docker compose up` starts the local stack.
- Backend health/readiness endpoints work.
- Backend tests pass.
- Frontend builds and renders the dashboard/application shell.
- Core database migrations run successfully.
- Authentication and tenant context are enforced on protected endpoints.
- README explains local setup, architecture, current limitations, and the phased roadmap.
- CI checks are present for backend and frontend.
