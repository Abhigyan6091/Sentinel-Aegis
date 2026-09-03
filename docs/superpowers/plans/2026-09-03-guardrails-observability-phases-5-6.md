# Guardrails And Observability Phases 5-6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add advanced local guardrails, benchmark defense modes, and production-shaped observability/event streaming hooks.

**Architecture:** Extend the existing deterministic runtime with secret detection, multi-turn prompt-injection state, and defense-mode configuration. Add benchmark APIs over the existing campaign runner and add lightweight telemetry/event abstractions that work locally while exposing OpenTelemetry/Redpanda-ready configuration and Grafana provisioning.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy-independent local services, pytest, Grafana provisioning JSON.

**Spec:** `docs/production-roadmap.md` Phases P5 and P6.

## Global Constraints

- Existing default demo behavior must stay unchanged.
- No live external LLM, Redpanda, or OpenTelemetry collector is required for tests.
- Benchmark modes must be deterministic.
- Security events and spans must stay tenant scoped.

---

### Task 1: Advanced Guardrails

- [ ] Add failing tests for secret redaction and multi-turn injection blocking.
- [ ] Implement `SecretDetector`, secret redaction, and in-memory multi-turn state.
- [ ] Run focused tests.

### Task 2: Benchmark Modes

- [ ] Add failing tests for benchmark mode API output.
- [ ] Implement defense modes and benchmark route.
- [ ] Run focused tests.

### Task 3: Observability And Event Streaming

- [ ] Add failing tests for telemetry spans, event publish, and Grafana provisioning.
- [ ] Implement local telemetry/event bus and Grafana dashboard provisioning.
- [ ] Update docs/local summary, verify, commit, and push.
