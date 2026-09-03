from app.core.config import Settings


def test_settings_default_to_local_development_values():
    settings = Settings()

    assert settings.app_name == "AegisAI"
    assert settings.environment == "local"
    assert settings.rate_limit_requests == 100
    assert "tenant-demo" in settings.api_keys
