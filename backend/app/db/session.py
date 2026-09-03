from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import Settings, get_settings
from app.db.base import Base
from app.models import foundation  # noqa: F401

_engines: dict[str, AsyncEngine] = {}
_sessionmakers: dict[str, async_sessionmaker[AsyncSession]] = {}
_initialized_urls: set[str] = set()


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    settings = settings or get_settings()
    if settings.database_url not in _engines:
        _engines[settings.database_url] = create_async_engine(settings.database_url)
    return _engines[settings.database_url]


def get_sessionmaker(settings: Settings | None = None) -> async_sessionmaker[AsyncSession]:
    settings = settings or get_settings()
    if settings.database_url not in _sessionmakers:
        _sessionmakers[settings.database_url] = async_sessionmaker(
            bind=get_engine(settings),
            expire_on_commit=False,
        )
    return _sessionmakers[settings.database_url]


async def ensure_schema(settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    if not settings.auto_create_schema or settings.database_url in _initialized_urls:
        return

    async with get_engine(settings).begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    _initialized_urls.add(settings.database_url)


async def get_session() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    await ensure_schema(settings)
    sessionmaker = get_sessionmaker(settings)
    async with sessionmaker() as session:
        yield session
