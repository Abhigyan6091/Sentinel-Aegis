# Sentinel Aegis Production Roadmap

Date: 2026-09-03

The reduced 5-phase MVP is complete. The next work turns Sentinel Aegis from a strong local portfolio MVP into a production-grade AI application security platform.

## Phase P1: Production Identity And Tenant Isolation

Goal: replace development-only auth with production identity boundaries.

Status: core JWT authentication is implemented. Organization, project, role-membership management, and route-by-route role policy rollout remain future P1 expansion work.

- Add JWT issuer validation with JWKS discovery.
- Add configurable issuer, audience, algorithm, and clock-skew settings.
- Add organization, project, role, and membership models.
- Enforce tenant ownership on every persisted object and query path.
- Add permission checks for admin, security analyst, developer, and read-only roles.
- Add audit tests proving cross-tenant reads and writes fail.

Exit criteria:

- Every API path has authenticated identity and authorization coverage.
- CI includes tenant isolation regression tests.
- Development API keys remain available only behind explicit local settings.

## Phase P2: Real Provider Layer

Goal: support real LLM providers while keeping deterministic local mode for tests.

Status: core OpenAI and Anthropic adapters are implemented with environment selection, timeout settings, retry settings, mocked tests, and normalized provider/model/token metadata. Per-application provider config, durable cost analytics, and circuit-breaker state remain future P2 expansion work.

- Add OpenAI provider behind the existing provider interface.
- Add Anthropic provider behind the same interface.
- Add provider selection by environment and per-application config.
- Add timeout, retry, rate-limit, and circuit-breaker behavior.
- Add token, cost, latency, and model metadata accounting.
- Add provider failure tests and deterministic fixtures.

Exit criteria:

- Local tests never require external provider keys.
- Production mode can run against configured provider credentials.
- Observability records provider latency, model, tokens, and cost.

## Phase P3: Qdrant-Backed RAG And Data Security

Goal: replace local fixtures with a real document-ingestion and retrieval path.

Status: core document ingestion, chunk metadata, deterministic embeddings, tenant-scoped retrieval, support-agent RAG mode, and a Qdrant-compatible HTTP vector store are implemented. Production embedding providers, ingestion jobs, and retention workflows remain future P3 expansion work.

- Add document upload and ingestion APIs.
- Add embedding provider abstraction.
- Store chunks and metadata in PostgreSQL.
- Index embeddings in Qdrant.
- Add tenant-scoped vector search.
- Add poisoned-document detection and source trust metadata.
- Add data retention and deletion paths.

Exit criteria:

- Support Agent retrieval uses Qdrant in production mode.
- Tests prove tenant-scoped retrieval isolation.
- RAG poisoning scenarios can be seeded through ingestion, not hardcoded fixtures.

## Phase P4: Policy Center And Approval Workflows

Goal: make runtime policy configurable and auditable.

Status: core policy CRUD/versioning, activation, active-policy tool authorization, approval-request persistence, approval decisions, and console pages are implemented. OPA/Rego, full role-management UI, and execution-after-approval workflows remain future P4 expansion work.

- Add policy CRUD APIs.
- Add policy versioning and activation controls.
- Add approval queue models and APIs for high-risk tool actions.
- Add frontend pages for policies, guardrails, approvals, and role-aware review.
- Add durable mock-tool state for refunds, tickets, and email actions.
- Evaluate OPA/Rego integration after the CRUD workflow is stable.

Exit criteria:

- High-risk tool calls create reviewable approval records.
- Policies can be changed without code edits.
- Policy changes and approval decisions are audit logged.

## Phase P5: Advanced Guardrails And Benchmark Modes

Goal: compare layered defenses with measurable tradeoffs.

- Add secret and credential detection.
- Add classifier-based prompt-injection detector.
- Add optional LLM-judge evaluator.
- Add Microsoft Presidio-based PII option.
- Add multi-turn attack state and session memory.
- Add benchmark modes:
  - No Defense
  - Rules Only
  - Classifier
  - LLM Judge
  - Layered Defense
- Add before/after comparison charts.

Exit criteria:

- Campaigns can run against multiple defense configurations.
- Reports show security, latency, false-positive, false-negative, and cost tradeoffs.
- CI has regression coverage for each defense mode.

## Phase P6: Full Observability And Event Streaming

Goal: move from summary counters to production operations telemetry.

- Add OpenTelemetry instrumentation for API, provider, RAG, guardrails, tools, and campaigns.
- Export traces to an OTLP-compatible collector.
- Add Grafana dashboards for security posture, latency, provider cost, and attack outcomes.
- Stream security events through Redpanda.
- Add durable event consumers for async report generation.
- Add alert thresholds for failing security gates and critical findings.

Exit criteria:

- Local Docker Compose includes working dashboards.
- Production traces correlate request, tool, provider, retrieval, and guardrail spans.
- Security events can be consumed asynchronously.

## Phase P7: Regression Automation And Security Research Workflow

Goal: turn findings into repeatable tests and reviewable work items.

- Convert security-gate findings into durable regression fixtures.
- Add a regression-suite runner separate from exploratory campaigns.
- Store campaign reports and gate reports as artifacts.
- Add finding lifecycle APIs for open, triaged, fixed, accepted-risk, and closed.
- Add evidence fields, reproduction steps, and remediation tracking.
- Add import/export support for JSON and Markdown reports.

Exit criteria:

- A discovered finding can become a failing regression test.
- The regression test passes only after the mitigation is improved.
- Security reports are reproducible from committed fixtures.

## Phase P8: Deployment And Production Hardening

Goal: prepare a deployable, secure production service.

- Add Kubernetes manifests or Terraform-backed deployment docs.
- Add secrets-manager integration.
- Add secure CORS, headers, request-size limits, and structured error handling.
- Add database backup/restore guidance.
- Add migration smoke tests.
- Add SAST/dependency/container scanning in CI.
- Add production runbook and incident-response notes.

Exit criteria:

- A clean environment can deploy Sentinel Aegis from documented steps.
- CI blocks unsafe dependencies and container regressions.
- Operators have runbooks for deploy, rollback, backup, and incident triage.

## Recommended Build Order

1. P1 Production Identity And Tenant Isolation.
2. P2 Real Provider Layer.
3. P3 Qdrant-Backed RAG And Data Security.
4. P4 Policy Center And Approval Workflows.
5. P5 Advanced Guardrails And Benchmark Modes.
6. P6 Full Observability And Event Streaming.
7. P7 Regression Automation And Security Research Workflow.
8. P8 Deployment And Production Hardening.
