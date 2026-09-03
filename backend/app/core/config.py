from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AegisAI"
    environment: str = "local"
    database_url: str = "sqlite+aiosqlite:///./aegisai.db"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_schema: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    api_keys: dict[str, str] = Field(
        default_factory=lambda: {
            "tenant-demo": "dev-aegis-key",
            "tenant-other": "dev-other-key",
        }
    )

    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
