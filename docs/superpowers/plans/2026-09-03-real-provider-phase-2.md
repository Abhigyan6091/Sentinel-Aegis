# Real Provider Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real OpenAI and Anthropic provider adapters behind the existing LLM provider interface while preserving deterministic local mode for tests and demos.

**Architecture:** Extend `app.ai.providers` with a provider factory, provider configuration errors, HTTP-based OpenAI Responses API and Anthropic Messages API adapters, retry behavior, and normalized token/model metadata. `SupportAgent` will use the factory by default.

**Tech Stack:** FastAPI backend, Pydantic settings, httpx async clients, pytest with mocked transports.

**Spec:** `docs/production-roadmap.md` Phase P2.

## Global Constraints

- Local provider remains the default and requires no external keys.
- OpenAI and Anthropic providers are selected by environment settings.
- Tests must not make live network calls.
- Provider failures must be explicit and safe.
- Support Agent continues to consume `LLMProvider.generate(...)`.

---

### Task 1: Provider Selection

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/ai/providers.py`
- Test: `backend/tests/test_providers.py`

**Interfaces:**
- Produces: `create_llm_provider(settings=None) -> LLMProvider`.

- [ ] Write failing tests for local, OpenAI, Anthropic, and unknown provider selection.
- [ ] Implement provider settings and factory.
- [ ] Run focused tests.

### Task 2: OpenAI And Anthropic HTTP Adapters

**Files:**
- Modify: `backend/app/ai/providers.py`
- Test: `backend/tests/test_providers.py`

**Interfaces:**
- Produces: `OpenAIProvider.generate(...)` and `AnthropicProvider.generate(...)`.

- [ ] Write mocked HTTP response tests for both providers.
- [ ] Implement request/response mapping and token normalization.
- [ ] Run focused tests.

### Task 3: Retry And Agent Wiring

**Files:**
- Modify: `backend/app/ai/providers.py`
- Modify: `backend/app/support/agent.py`
- Modify: `.env.example`
- Modify: `README.md`
- Modify local ignored: `summarizer.md`

- [ ] Write mocked retry test for transient provider failures.
- [ ] Wire `SupportAgent` to `create_llm_provider`.
- [ ] Document provider environment settings.
- [ ] Run full verification and commit.
