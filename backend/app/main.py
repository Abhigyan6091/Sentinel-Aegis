import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.hardening import install_hardening
from app.core.preflight import verify_production_config
from app.core.secrets import resolve_settings_secrets

logger = logging.getLogger("sentinel_aegis")


def create_app() -> FastAPI:
    settings = get_settings()
    resolved = resolve_settings_secrets(settings)
    if resolved:
        logger.info("resolved secret references for: %s", ", ".join(resolved))
    verify_production_config(settings)

    app = FastAPI(
        title=settings.app_name,
        # Interactive docs describe every route and schema: useful locally, an
        # unnecessary disclosure on a production surface.
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
    )
    install_hardening(app, settings)
    app.include_router(api_router)
    return app


app = create_app()
