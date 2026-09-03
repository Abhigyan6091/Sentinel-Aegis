from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings


@dataclass(frozen=True)
class SecurityEventEnvelope:
    tenant_id: str
    event_type: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryEventBus:
    def __init__(self) -> None:
        self.events: list[SecurityEventEnvelope] = []

    async def publish(self, tenant_id: str, event_type: str, payload: dict[str, Any]) -> None:
        self.events.append(
            SecurityEventEnvelope(tenant_id=tenant_id, event_type=event_type, payload=payload)
        )

    def clear(self) -> None:
        self.events.clear()


class RedpandaEventBus(MemoryEventBus):
    """Redpanda-ready placeholder that keeps local behavior deterministic."""


_memory_event_bus = MemoryEventBus()
_redpanda_event_bus = RedpandaEventBus()


def get_event_bus() -> MemoryEventBus:
    if get_settings().event_bus == "redpanda":
        return _redpanda_event_bus
    return _memory_event_bus
