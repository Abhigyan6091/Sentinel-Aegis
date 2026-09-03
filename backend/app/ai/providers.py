from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings


class ToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, str] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    tool_requests: list[ToolRequest] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = "local"
    model: str = "local-deterministic"


class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        message: str,
        trusted_instructions: str,
        retrieved_context: list[str],
    ) -> LLMResponse:
        raise NotImplementedError


class LocalProvider(LLMProvider):
    async def generate(
        self,
        message: str,
        trusted_instructions: str,
        retrieved_context: list[str],
    ) -> LLMResponse:
        del trusted_instructions
        lowered = message.lower()
        tool_requests: list[ToolRequest] = []

        if "refund" in lowered and "ord-" in lowered:
            tool_requests.append(
                ToolRequest(
                    tool_name="refund_order",
                    arguments={"order_id": "ORD-1001", "customer_id": "CUST-001"},
                )
            )
            content = "I can prepare a refund review, but this action needs approval."
        elif "profile" in lowered or "cust-001" in lowered:
            tool_requests.append(
                ToolRequest(tool_name="search_customer", arguments={"customer_id": "CUST-001"})
            )
            content = "Customer CUST-001 is Priya Rao. Customer SSN: 123-45-6789."
        elif retrieved_context:
            content = f"Based on trusted support content: {retrieved_context[0]}"
        else:
            content = "I can help with order lookup, ticket creation, and support policy questions."

        return LLMResponse(
            content=content,
            tool_requests=tool_requests,
            input_tokens=max(1, len(message.split())),
            output_tokens=max(1, len(content.split())),
        )


class ProviderConfigError(RuntimeError):
    pass


class ProviderRuntimeError(RuntimeError):
    pass


class HttpLLMProvider(LLMProvider):
    provider_name: str
    retryable_statuses = {408, 409, 429, 500, 502, 503, 504}

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 30,
        max_retries: int = 2,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.max_retries = max(0, max_retries)
        self.client = client or httpx.AsyncClient(base_url=base_url, timeout=timeout_seconds)

    async def _post_json(
        self,
        path: str,
        payload: dict[str, Any],
        headers: dict[str, str],
    ) -> dict[str, Any]:
        last_response: httpx.Response | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(path, json=payload, headers=headers)
            except httpx.HTTPError as exc:
                if attempt >= self.max_retries:
                    raise ProviderRuntimeError(
                        f"{self.provider_name} request failed: {exc}"
                    ) from exc
                continue

            if response.status_code < 400:
                return response.json()

            last_response = response
            if response.status_code not in self.retryable_statuses or attempt >= self.max_retries:
                break

        status_code = last_response.status_code if last_response is not None else "unknown"
        raise ProviderRuntimeError(f"{self.provider_name} request failed with {status_code}")


class OpenAIProvider(HttpLLMProvider):
    provider_name = "OpenAI"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30,
        max_retries: int = 2,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://api.openai.com",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            client=client,
        )

    async def generate(
        self,
        message: str,
        trusted_instructions: str,
        retrieved_context: list[str],
    ) -> LLMResponse:
        data = await self._post_json(
            "/v1/responses",
            {
                "model": self.model,
                "instructions": trusted_instructions,
                "input": build_provider_input(message, retrieved_context),
            },
            {"authorization": f"Bearer {self.api_key}"},
        )
        usage = data.get("usage", {})
        return LLMResponse(
            content=extract_openai_text(data),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            provider="openai",
            model=self.model,
        )


class AnthropicProvider(HttpLLMProvider):
    provider_name = "Anthropic"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30,
        max_retries: int = 2,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url="https://api.anthropic.com",
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            client=client,
        )

    async def generate(
        self,
        message: str,
        trusted_instructions: str,
        retrieved_context: list[str],
    ) -> LLMResponse:
        data = await self._post_json(
            "/v1/messages",
            {
                "model": self.model,
                "max_tokens": 800,
                "system": trusted_instructions,
                "messages": [
                    {
                        "role": "user",
                        "content": build_provider_input(message, retrieved_context),
                    }
                ],
            },
            {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        usage = data.get("usage", {})
        return LLMResponse(
            content=extract_anthropic_text(data),
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            provider="anthropic",
            model=self.model,
        )


def build_provider_input(message: str, retrieved_context: list[str]) -> str:
    if not retrieved_context:
        return message
    context = "\n\n".join(f"- {item}" for item in retrieved_context)
    return f"Context:\n{context}\n\nUser request:\n{message}"


def extract_openai_text(data: dict[str, Any]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    fragments: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                fragments.append(text)
    return "\n".join(fragments)


def extract_anthropic_text(data: dict[str, Any]) -> str:
    fragments = [
        item["text"]
        for item in data.get("content", [])
        if item.get("type") == "text" and isinstance(item.get("text"), str)
    ]
    return "\n".join(fragments)


def create_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "local":
        return LocalProvider()
    if provider == "openai":
        if not settings.openai_api_key:
            raise ProviderConfigError("OPENAI_API_KEY is required for the OpenAI provider")
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ProviderConfigError("ANTHROPIC_API_KEY is required for the Anthropic provider")
        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
            timeout_seconds=settings.llm_timeout_seconds,
            max_retries=settings.llm_max_retries,
        )
    raise ProviderConfigError(f"Unsupported LLM provider: {settings.llm_provider}")
