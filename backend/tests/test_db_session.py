import asyncio

import pytest

from app.core.config import Settings
from app.db import session as db_session


@pytest.mark.asyncio
async def test_ensure_schema_is_safe_for_concurrent_first_requests(tmp_path):
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'concurrent.db'}"
    settings = Settings(database_url=database_url)
    db_session._initialized_urls.discard(database_url)

    await asyncio.gather(
        db_session.ensure_schema(settings),
        db_session.ensure_schema(settings),
    )

    assert database_url in db_session._initialized_urls
