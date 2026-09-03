# Sentinel Aegis Milestone 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real observability for runtime and red-team flows: Prometheus metrics, persisted traces/events/results, observability APIs, and dashboard pages backed by measured data.

**Architecture:** Backend observability lives in a small service layer called from the Support Agent and Campaign Runner. Runtime requests persist trace envelopes and security events; campaigns persist attack results, evaluation runs, and findings when applicable. Frontend Observability, Traces, and Dashboard views consume API summaries rather than displaying hard-coded metrics.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy async, prometheus-client, pytest, Next.js 15, TypeScript, Tailwind CSS, Recharts, lucide-react.

**Spec:** `docs/superpowers/specs/2026-09-03-aegisai-phase-1-design.md`

## Global Constraints

- Every important security decision must be observable.
- Metrics must be generated from runtime/campaign execution, not hard-coded.
- Trace records must avoid storing unnecessary sensitive input or output content.
- Tenant-scoped observability APIs must only return data for the authenticated tenant.
- Prometheus must scrape a real `/metrics` endpoint.
- Frontend charts must use real API data or honest empty states.

---

### Task 1: Backend Metrics And Trace Persistence

**Files:**
- Create: `backend/app/observability/metrics.py`
- Create: `backend/app/observability/service.py`
- Create: `backend/app/api/routes/observability.py`
- Modify: `backend/app/support/agent.py`
- Modify: `backend/app/api/router.py`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/test_observability.py`

**Interfaces:**
- Produces: `record_support_response()`, `record_campaign_result()`, `GET /metrics`, `GET /api/v1/observability/summary`, `GET /api/v1/observability/traces`.
- Consumes: `SupportChatResponse`, `AttackEvaluation`, SQLAlchemy session, and `RequestIdentity`.

- [ ] Write failing tests proving support chat persists traces/events, `/metrics` exposes counters, and observability summary is tenant scoped.
- [ ] Run `cd backend && python3 -m pytest tests/test_observability.py -q` and verify RED failures.
- [ ] Implement metrics registry, trace persistence, summary APIs, and route wiring.
- [ ] Rerun focused and full backend tests and verify PASS.

### Task 2: Campaign Persistence

**Files:**
- Modify: `backend/app/redteam/runner.py`
- Modify: `backend/app/observability/service.py`
- Test: `backend/tests/test_observability.py`

**Interfaces:**
- Consumes: campaign run responses.
- Produces: persisted attack results, evaluation runs, and findings for observed successful attacks.

- [ ] Extend tests to assert campaign runs persist attack results and evaluation metrics.
- [ ] Run the focused test and verify RED failure.
- [ ] Implement campaign persistence through the observability service.
- [ ] Rerun focused and full backend tests and verify PASS.

### Task 3: Frontend Observability And Trace Views

**Files:**
- Create: `frontend/app/observability/page.tsx`
- Create: `frontend/app/traces/page.tsx`
- Create: `frontend/components/observability-charts.tsx`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/package.json`

**Interfaces:**
- Consumes: observability summary and traces APIs.
- Produces: dashboard metrics, trend charts, security event view, and trace list backed by real backend data.

- [ ] Add typed frontend API methods for observability summary and traces.
- [ ] Add Recharts-based charts and metric panels.
- [ ] Update Dashboard, Observability, and Traces pages.
- [ ] Run frontend lint, typecheck, and build and verify PASS.

### Task 4: Documentation, Summary, Verification, And Push

**Files:**
- Modify: `README.md`
- Modify: `summarizer.md`

**Interfaces:**
- Consumes: implemented observability behavior.
- Produces: updated docs describing implemented and remaining observability work.

- [ ] Document `/metrics`, observability APIs, trace persistence, and remaining gaps.
- [ ] Run backend tests/lint, frontend lint/typecheck/build, `docker compose config`, and HTTP smoke tests.
- [ ] Commit Milestone 4 and push `main` to GitHub.
