import time
from dataclasses import dataclass, field


@dataclass
class InMemoryRateLimiter:
    limit: int
    window_seconds: int
    _hits: dict[str, list[float]] = field(default_factory=dict)

    async def allow(self, key: str) -> bool:
        now = time.monotonic()
        window_started_at = now - self.window_seconds
        recent_hits = [hit for hit in self._hits.get(key, []) if hit > window_started_at]

        if len(recent_hits) >= self.limit:
            self._hits[key] = recent_hits
            return False

        recent_hits.append(now)
        self._hits[key] = recent_hits
        return True
