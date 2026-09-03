# Sentinel Aegis Milestone 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic red-team evaluation plane that sends attack traffic through the same support-agent runtime pipeline as normal traffic.

**Architecture:** Backend red-team modules define attack seeds, generate bounded variants, run campaigns through `SupportAgent.run()`, evaluate outcomes from structured guardrail/tool/context signals, calculate transparent scores, and persist findings for actual failures. Frontend pages consume real campaign/attack/finding APIs and show empty states or measured results only.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy async, pytest, Next.js 15, TypeScript, Tailwind CSS, lucide-react.

**Spec:** `docs/superpowers/specs/2026-09-03-aegisai-phase-1-design.md`

## Global Constraints

- Red-team attacks must pass through the same runtime security pipeline as real user traffic.
- Attack execution must be bounded by `attack_count`, `mutation_depth`, and deterministic local execution.
- Evaluations cannot rely solely on string matching; use structured response signals such as `blocked`, guardrail decisions, tool authorization decisions, context firewall actions, and output guardrail decisions.
- Security scores must be computed from measured results, not hard-coded.
- Findings are created only when an attack is evaluated as successful.
- No attack may target real external systems or trigger real destructive actions.

---

### Task 1: Attack Generator, Evaluator, And Scoring

**Files:**
- Create: `backend/app/redteam/__init__.py`
- Create: `backend/app/redteam/attacks.py`
- Create: `backend/app/redteam/evaluator.py`
- Create: `backend/app/redteam/scoring.py`
- Create: `backend/tests/test_redteam_engine.py`

**Interfaces:**
- Produces: `AttackSeed`, `AttackVariant`, `AttackGenerator.generate()`, `SecurityEvaluator.evaluate()`, `SecurityScorer.score()`.
- Consumes: `SupportChatResponse` from Milestone 2.

- [ ] Write tests proving generator creates bounded variants with lineage, evaluator uses structured runtime signals, and scorer derives transparent scores from results.
- [ ] Run `cd backend && python3 -m pytest tests/test_redteam_engine.py -q` and verify RED import failures.
- [ ] Implement deterministic seeds, variant generation, evaluator, and scoring.
- [ ] Rerun focused tests and verify PASS.

### Task 2: Campaign Runner And API

**Files:**
- Create: `backend/app/redteam/runner.py`
- Create: `backend/app/schemas/redteam.py`
- Create: `backend/app/api/routes/redteam.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_redteam_api.py`

**Interfaces:**
- Consumes: attack generator/evaluator/scorer and `SupportAgent`.
- Produces: `POST /api/v1/red-team/campaigns`, `GET /api/v1/red-team/campaigns/latest`, `GET /api/v1/red-team/attacks`, `GET /api/v1/red-team/findings`.

- [ ] Write tests proving campaign API runs attacks through runtime, returns metrics, records trace-like steps, and creates no findings for blocked attacks.
- [ ] Run `cd backend && python3 -m pytest tests/test_redteam_api.py -q` and verify RED failures.
- [ ] Implement runner and routes with in-process deterministic campaign history.
- [ ] Rerun focused and full backend tests and verify PASS.

### Task 3: Red-Team Frontend Pages

**Files:**
- Create: `frontend/app/campaigns/page.tsx`
- Create: `frontend/app/attacks/page.tsx`
- Create: `frontend/app/findings/page.tsx`
- Create: `frontend/components/campaign-runner.tsx`
- Modify: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: red-team campaign, attack, and finding APIs.
- Produces: usable campaign runner, attack explorer, and findings list backed by real API responses.

- [ ] Add API client methods for red-team routes.
- [ ] Add campaign runner UI that starts deterministic campaigns and displays measured metrics.
- [ ] Add attack explorer and findings pages with real empty states.
- [ ] Run frontend lint, typecheck, and build and verify PASS.

### Task 4: Documentation, Verification, And Push

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: implemented red-team behavior.
- Produces: demo instructions for Milestone 3.

- [ ] Document red-team routes, sample campaign request, and scoring methodology.
- [ ] Run backend tests/lint, frontend lint/typecheck/build, `docker compose config`, and HTTP smoke tests.
- [ ] Commit Milestone 3 and push `main` to GitHub.
