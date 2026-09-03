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
    auth_mode: str = "hybrid"
    allow_dev_api_keys: bool = True
    jwt_issuer: str | None = None
    jwt_audience: str | None = None
    jwt_jwks_url: str | None = None
    jwt_jwks_json: str | None = None
    jwt_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])
    jwt_clock_skew_seconds: int = 30
    llm_provider: str = "local"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-3-5-sonnet-latest"
    llm_timeout_seconds: float = 30
    llm_max_retries: int = 2
    support_retriever: str = "fixture"
    rag_vector_store: str = "memory"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "sentinel_aegis_chunks"
    embedding_dimensions: int = 32
    rag_chunk_size: int = 700
    rag_chunk_overlap: int = 100
    telemetry_enabled: bool = True
    otlp_endpoint: str | None = None
    event_bus: str = "memory"
    regression_fixtures_dir: str = "./regression/cases"
    report_artifacts_dir: str = "./artifacts"
    cors_allow_origins: list[str] = Field(default_factory=list)
    cors_allow_credentials: bool = False
    cors_allow_methods: list[str] = Field(
        default_factory=lambda: ["GET", "POST", "PATCH", "DELETE", "OPTIONS"]
    )
    cors_allow_headers: list[str] = Field(
        default_factory=lambda: ["authorization", "content-type", "x-api-key", "x-request-id"]
    )
    max_request_bytes: int = 1_000_000
    hsts_max_age_seconds: int = 31_536_000
    security_headers_enabled: bool = True
    secrets_provider: str = "env"
    secrets_file_dir: str = "/run/secrets"
    aws_secrets_region: str | None = None
    aws_secrets_prefix: str = "sentinel-aegis/"
    redpanda_bootstrap_servers: str = "redpanda:9092"
    security_events_topic: str = "sentinel-aegis.security-events"
    api_keys: dict[str, str] = Field(
        default_factory=lambda: {
            "tenant-demo": "dev-aegis-key",
            "tenant-other": "dev-other-key",
        }
    )

    model_config = SettingsConfigDict(env_prefix="AEGIS_", env_file=".env", extra="ignore")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
