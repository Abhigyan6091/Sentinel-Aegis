from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from typing import Any


@dataclass(frozen=True)
class SpanRecord:
    name: str
    tenant_id: str
    attributes: dict[str, Any]
    duration_ms: int
    started_at: datetime


class LocalTelemetry:
    def __init__(self) -> None:
        self.spans: list[SpanRecord] = []

    def clear(self) -> None:
        self.spans.clear()

    def start_span(self, name: str, tenant_id: str, **attributes):
        return SpanContext(self, name, tenant_id, attributes)

    def record(
        self,
        name: str,
        tenant_id: str,
        attributes: dict[str, Any],
        started_at: datetime,
        started_perf: float,
    ) -> None:
        self.spans.append(
            SpanRecord(
                name=name,
                tenant_id=tenant_id,
                attributes=attributes,
                duration_ms=int((perf_counter() - started_perf) * 1000),
                started_at=started_at,
            )
        )


@dataclass
class SpanContext:
    telemetry: LocalTelemetry
    name: str
    tenant_id: str
    attributes: dict[str, Any]
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_perf: float = field(default_factory=perf_counter)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if exc is not None:
            self.attributes["error"] = str(exc)
        self.telemetry.record(
            self.name,
            self.tenant_id,
            self.attributes,
            self.started_at,
            self.started_perf,
        )


_telemetry = LocalTelemetry()


def get_telemetry() -> LocalTelemetry:
    return _telemetry
