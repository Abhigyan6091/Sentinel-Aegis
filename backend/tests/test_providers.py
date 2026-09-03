import json

import httpx
import pytest

from app.ai.providers import (
    AnthropicProvider,
    LLMResponse,
    LocalProvider,
    OpenAIProvider,
    ProviderConfigError,
    ProviderRuntimeError,
    create_llm_provider,
)
from app.core.config import Settings


def settings(**overrides) -> Settings:
    values = {
        "llm_provider": "local",
        "openai_api_key": None,
        "anthropic_api_key": None,
        "openai_model": "gpt-4.1-mini",
        "anthropic_model": "claude-3-5-sonnet-latest",
        "llm_timeout_seconds": 10,
        "llm_max_retries": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_provider_factory_defaults_to_local_provider():
    provider = create_llm_provider(settings())

    assert isinstance(provider, LocalProvider)


def test_provider_factory_selects_openai_provider():
    provider = create_llm_provider(settings(llm_provider="openai", openai_api_key="sk-test"))

    assert isinstance(provider, OpenAIProvider)


def test_provider_factory_requires_openai_key():
    with pytest.raises(ProviderConfigError, match="OPENAI_API_KEY"):
        create_llm_provider(settings(llm_provider="openai", openai_api_key=None))


def test_provider_factory_selects_anthropic_provider():
    provider = create_llm_provider(
        settings(llm_provider="anthropic", anthropic_api_key="sk-ant-test")
    )

    assert isinstance(provider, AnthropicProvider)


def test_provider_factory_rejects_unknown_provider():
    with pytest.raises(ProviderConfigError, match="Unsupported LLM provider"):
        create_llm_provider(settings(llm_provider="other"))


@pytest.mark.asyncio
async def test_openai_provider_maps_responses_api_payload():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == "/v1/responses"
        assert request.headers["authorization"] == "Bearer sk-test"
        assert body["model"] == "gpt-4.1-mini"
        assert body["instructions"].startswith("Trusted")
        assert "Context:" in body["input"]
        return httpx.Response(
            200,
            json={
                "output_text": "Provider answer",
                "usage": {"input_tokens": 11, "output_tokens": 7},
            },
        )

    provider = OpenAIProvider(
        api_key="sk-test",
        model="gpt-4.1-mini",
        client=httpx.AsyncClient(
            base_url="https://api.openai.com",
            transport=httpx.MockTransport(handler),
        ),
    )

    result = await provider.generate("Hello", "Trusted instructions", ["Context item"])

    assert result == LLMResponse(
        content="Provider answer",
        input_tokens=11,
        output_tokens=7,
        provider="openai",
        model="gpt-4.1-mini",
    )


@pytest.mark.asyncio
async def test_anthropic_provider_maps_messages_api_payload():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert request.url.path == "/v1/messages"
        assert request.headers["x-api-key"] == "sk-ant-test"
        assert body["model"] == "claude-3-5-sonnet-latest"
        assert body["system"].startswith("Trusted")
        assert body["messages"][0]["role"] == "user"
        return httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "Anthropic answer"}],
                "usage": {"input_tokens": 9, "output_tokens": 4},
            },
        )

    provider = AnthropicProvider(
        api_key="sk-ant-test",
        model="claude-3-5-sonnet-latest",
        client=httpx.AsyncClient(
            base_url="https://api.anthropic.com",
            transport=httpx.MockTransport(handler),
        ),
    )

    result = await provider.generate("Hello", "Trusted instructions", ["Context item"])

    assert result == LLMResponse(
        content="Anthropic answer",
        input_tokens=9,
        output_tokens=4,
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
    )


@pytest.mark.asyncio
async def test_openai_provider_retries_transient_failures():
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(500, json={"error": {"message": "temporary"}})
        return httpx.Response(
            200,
            json={
                "output_text": "Recovered",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    provider = OpenAIProvider(
        api_key="sk-test",
        model="gpt-4.1-mini",
        max_retries=1,
        client=httpx.AsyncClient(
            base_url="https://api.openai.com",
            transport=httpx.MockTransport(handler),
        ),
    )

    result = await provider.generate("Hello", "Trusted instructions", [])

    assert attempts == 2
    assert result.content == "Recovered"


@pytest.mark.asyncio
async def test_provider_raises_runtime_error_after_retry_budget():
    provider = OpenAIProvider(
        api_key="sk-test",
        model="gpt-4.1-mini",
        max_retries=0,
        client=httpx.AsyncClient(
            base_url="https://api.openai.com",
            transport=httpx.MockTransport(lambda request: httpx.Response(500)),
        ),
    )

    with pytest.raises(ProviderRuntimeError, match="OpenAI request failed"):
        await provider.generate("Hello", "Trusted instructions", [])
