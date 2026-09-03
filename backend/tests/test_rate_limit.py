import pytest

from app.services.rate_limit import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_under_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)

    assert await limiter.allow("tenant-demo:user-demo") is True
    assert await limiter.allow("tenant-demo:user-demo") is True


@pytest.mark.asyncio
async def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)

    assert await limiter.allow("tenant-demo:user-demo") is True
    assert await limiter.allow("tenant-demo:user-demo") is True
    assert await limiter.allow("tenant-demo:user-demo") is False
