from prometheus_client import CollectorRegistry, Counter, generate_latest

registry = CollectorRegistry()

requests_total = Counter(
    "sentinel_aegis_requests_total",
    "Runtime requests processed by Sentinel Aegis.",
    ["tenant_id", "decision"],
    registry=registry,
)
guardrail_blocks_total = Counter(
    "sentinel_aegis_guardrail_blocks_total",
    "Runtime requests blocked by guardrails.",
    ["tenant_id", "guardrail"],
    registry=registry,
)
campaigns_total = Counter(
    "sentinel_aegis_campaigns_total",
    "Red-team campaigns executed.",
    ["tenant_id"],
    registry=registry,
)
attack_results_total = Counter(
    "sentinel_aegis_attack_results_total",
    "Red-team attack results by outcome.",
    ["tenant_id", "outcome"],
    registry=registry,
)


def render_metrics() -> bytes:
    return generate_latest(registry)
