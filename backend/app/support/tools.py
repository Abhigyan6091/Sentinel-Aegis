from pydantic import BaseModel, Field


class ToolExecutionResult(BaseModel):
    tool_name: str
    status: str
    data: dict[str, str] = Field(default_factory=dict)


class MockSupportTools:
    async def execute(self, tool_name: str, arguments: dict[str, str]) -> ToolExecutionResult:
        if tool_name == "search_customer":
            return ToolExecutionResult(
                tool_name=tool_name,
                status="ok",
                data={
                    "customer_id": arguments.get("customer_id", "CUST-001"),
                    "name": "Priya Rao",
                    "email": "priya.rao@example.com",
                },
            )
        if tool_name == "get_order":
            return ToolExecutionResult(
                tool_name=tool_name,
                status="ok",
                data={"order_id": arguments.get("order_id", "ORD-1001"), "status": "delivered"},
            )
        if tool_name == "create_ticket":
            return ToolExecutionResult(
                tool_name=tool_name,
                status="ok",
                data={"ticket_id": "TICK-9001", "status": "created"},
            )
        return ToolExecutionResult(tool_name=tool_name, status="not_executed", data={})
