# Policy Approval Phase 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add policy CRUD/versioning and an approval queue for high-risk tool actions.

**Architecture:** Reuse the existing `Policy` table for active tool policy documents and add a dedicated `approval_requests` table. The support agent loads tenant active policy documents when a DB session exists, falls back to defaults otherwise, and records approval requests when tool authorization returns `REQUIRE_APPROVAL`.

**Tech Stack:** FastAPI, SQLAlchemy async, Pydantic schemas, Next.js server-rendered pages, pytest.

**Spec:** `docs/production-roadmap.md` Phase P4.

## Global Constraints

- Existing default support-agent behavior must remain compatible.
- Policy documents must be tenant-scoped.
- Approval requests must be tenant-scoped and auditable.
- High-risk tool calls must not execute before approval.

---

### Task 1: Backend Policy CRUD

- [ ] Add failing tests for create/list/activate policy behavior.
- [ ] Implement policy schemas, service, routes, and router wiring.
- [ ] Run focused tests.

### Task 2: Approval Queue

- [ ] Add failing tests for support-agent approval-request creation.
- [ ] Add approval model, migration, schemas, routes, and support-agent recording.
- [ ] Run focused tests.

### Task 3: Frontend And Docs

- [ ] Add policies and approvals API client methods.
- [ ] Add `/policies` and `/approvals` pages.
- [ ] Update README, production roadmap, and local ignored `summarizer.md`.
- [ ] Run full verification, commit, and push.
