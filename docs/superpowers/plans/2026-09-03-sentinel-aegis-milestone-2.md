# Sentinel Aegis Milestone 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first real Secure Demo App: a deterministic Enterprise Support Agent that runs through runtime security controls before responding.

**Architecture:** The backend gets provider, RAG, guardrail, policy, tool, and orchestration modules with typed Pydantic results. The support chat route invokes one runtime pipeline: input guardrails, retrieval, context firewall, local LLM provider, tool authorization, mock tool execution, output guardrails, and audit persistence. The frontend adds a support-agent page that calls real backend APIs and does not invent security metrics.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy async, pytest, Next.js 15, TypeScript, Tailwind CSS, lucide-react.

**Spec:** `docs/superpowers/specs/2026-09-03-aegisai-phase-1-design.md`

## Global Constraints

- No real destructive external actions.
- If no external API key is available, deterministic local provider behavior must keep tests and demos working.
- Retrieved documents are untrusted and pass through a context firewall.
- The LLM never directly executes tools; every requested tool call goes through policy authorization.
- High-risk actions such as refunds and email require approval or denial.
- Output guardrails redact PII before returning text to the user.
- Important security decisions must be observable in structured response metadata and persisted audit tables where available.

---

### Task 1: Runtime Security Primitives

**Files:**
- Create: `backend/app/security/runtime.py`
- Create: `backend/app/security/guardrails.py`
- Create: `backend/app/security/policy.py`
- Create: `backend/app/security/context_firewall.py`
- Test: `backend/tests/test_runtime_security.py`

**Interfaces:**
- Produces: `GuardrailResult`, `PromptInjectionDetector.evaluate()`, `PIIDetector.evaluate()`, `redact_pii()`, `PolicyEngine.authorize_tool()`, `ContextFirewall.inspect()`.
- Consumes: plain text user input, retrieved document dictionaries, and tool request names.

- [ ] Write tests for prompt injection blocking, PII redaction, high-risk tool approval, and malicious document isolation.
- [ ] Run `cd backend && python3 -m pytest tests/test_runtime_security.py -q` and verify RED import failures.
- [ ] Implement the runtime primitives with deterministic local rules and structured decisions.
- [ ] Rerun the focused test and verify PASS.

### Task 2: Enterprise Support Agent Pipeline

**Files:**
- Create: `backend/app/ai/providers.py`
- Create: `backend/app/support/documents.py`
- Create: `backend/app/support/tools.py`
- Create: `backend/app/support/agent.py`
- Create: `backend/app/schemas/support.py`
- Create: `backend/app/api/routes/support.py`
- Modify: `backend/app/api/router.py`
- Test: `backend/tests/test_support_agent.py`

**Interfaces:**
- Consumes: runtime primitives from Task 1 and authenticated identity from Milestone 1.
- Produces: `POST /api/v1/support/chat`, `SupportAgent.run()`, deterministic mock tool results, trace steps, guardrail decisions, and audit records.

- [ ] Write tests proving prompt injection is blocked, refund requests require approval, malicious RAG instructions are isolated, and PII output is redacted.
- [ ] Run `cd backend && python3 -m pytest tests/test_support_agent.py -q` and verify RED failures.
- [ ] Implement the local LLM provider, local document retriever, mock tools, support agent orchestrator, and FastAPI route.
- [ ] Rerun focused and full backend tests and verify PASS.

### Task 3: Support Agent Frontend

**Files:**
- Create: `frontend/app/support/page.tsx`
- Create: `frontend/components/support-chat.tsx`
- Modify: `frontend/components/sidebar.tsx`
- Modify: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: `POST /api/v1/support/chat`.
- Produces: a usable support-agent demo page with response text, guardrail decisions, tool decisions, and trace steps.

- [ ] Add a client-side support chat component with deterministic sample prompts.
- [ ] Add Support Agent to the navigation.
- [ ] Run `cd frontend && npm run lint && npm run typecheck && npm run build` and verify PASS.

### Task 4: Documentation, Verification, And Push

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-09-03-sentinel-aegis-milestone-2.md`

**Interfaces:**
- Consumes: implemented backend/frontend behavior.
- Produces: README instructions for the Enterprise Support Agent demo.

- [ ] Document the new route, demo prompts, and security behaviors.
- [ ] Run backend tests/lint, frontend lint/typecheck/build, and `docker compose config`.
- [ ] Commit Milestone 2 and push `main` to GitHub.
