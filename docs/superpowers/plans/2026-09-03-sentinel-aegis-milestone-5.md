# Sentinel Aegis Milestone 5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic CI security gate that runs Sentinel Aegis red-team checks and fails builds when security thresholds are missed.

**Architecture:** Reuse the existing red-team runner and scoring model. Add a small gate evaluator that compares campaign output against thresholds, expose it through a Python module CLI, and wire the CLI into GitHub Actions.

**Tech Stack:** FastAPI backend internals, Pydantic models, pytest, GitHub Actions.

**Spec:** Existing reduced roadmap in `README.md` and `summarizer.md`.

## Global Constraints

- Keep the gate deterministic and local by default.
- Do not require OpenAI, Anthropic, Qdrant, Redis, Postgres, or Docker for CI security gating.
- Preserve commits as `Abhigyan6091 <abhigyan.sharma6091@gmail.com>`.
- Use tests before implementation changes.

---

### Task 1: Security Gate Evaluator

**Files:**
- Create: `backend/tests/test_security_gate.py`
- Create: `backend/app/redteam/security_gate.py`

**Interfaces:**
- Produces: `GateThresholds`, `GateResult`, `evaluate_security_gate(campaign, thresholds)`.

- [ ] **Step 1:** Write failing tests for pass/fail threshold evaluation.
- [ ] **Step 2:** Run `python3 -m pytest tests/test_security_gate.py -q` and confirm import failure.
- [ ] **Step 3:** Implement the evaluator models and comparison logic.
- [ ] **Step 4:** Run the focused tests and confirm pass.

### Task 2: CI CLI

**Files:**
- Modify: `backend/tests/test_security_gate.py`
- Create: `backend/app/cli/__init__.py`
- Create: `backend/app/cli/security_gate.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: `python -m app.cli.security_gate --min-score 100 --max-attack-success-rate 0 --max-findings 0`.

- [ ] **Step 1:** Add a failing subprocess test for the CLI JSON output.
- [ ] **Step 2:** Implement the CLI around `CampaignRunner`.
- [ ] **Step 3:** Add the CI workflow step.
- [ ] **Step 4:** Run focused tests and lint.

### Task 3: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `summarizer.md`

- [ ] **Step 1:** Document the CI gate command and current reduced-project completion status.
- [ ] **Step 2:** Run backend tests, backend lint, frontend lint, frontend typecheck, frontend build, and Docker Compose config.
- [ ] **Step 3:** Commit and push to `origin/main`.
