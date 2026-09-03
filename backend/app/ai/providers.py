from abc import ABC, abstractmethod

from pydantic import BaseModel, Field


class ToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, str] = Field(default_factory=dict)


class LLMResponse(BaseModel):
    content: str
    tool_requests: list[ToolRequest] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


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
