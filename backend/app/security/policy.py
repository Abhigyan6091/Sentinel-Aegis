from pydantic import BaseModel

from app.security.runtime import Decision, Risk


class ToolPolicy(BaseModel):
    risk: Risk
    allowed_roles: list[str]
    require_approval: bool = False


class PolicyDecision(BaseModel):
    decision: Decision
    risk: Risk
    reason: str
    policy: str


class PolicyEngine:
    def __init__(self, tools: dict[str, ToolPolicy]) -> None:
        self.tools = tools

    @classmethod
    def default(cls) -> "PolicyEngine":
        return cls(
            tools={
                "search_customer": ToolPolicy(
                    risk=Risk.MEDIUM,
                    allowed_roles=["support_agent", "admin"],
                ),
                "get_order": ToolPolicy(risk=Risk.LOW, allowed_roles=["support_agent", "admin"]),
                "create_ticket": ToolPolicy(
                    risk=Risk.MEDIUM,
                    allowed_roles=["support_agent", "admin"],
                ),
                "refund_order": ToolPolicy(
                    risk=Risk.HIGH,
                    allowed_roles=["admin"],
                    require_approval=True,
                ),
                "send_email": ToolPolicy(
                    risk=Risk.HIGH,
                    allowed_roles=["admin"],
                    require_approval=True,
                ),
            }
        )

    def authorize_tool(
        self,
        tool_name: str,
        roles: list[str],
        tenant_id: str,
    ) -> PolicyDecision:
        policy = self.tools.get(tool_name)
        if policy is None:
            return PolicyDecision(
                decision=Decision.DENY,
                risk=Risk.CRITICAL,
                reason=f"Tool {tool_name} is not registered for tenant {tenant_id}.",
                policy="tool_authorization",
            )

        if policy.require_approval:
            return PolicyDecision(
                decision=Decision.REQUIRE_APPROVAL,
                risk=policy.risk,
                reason=f"Tool {tool_name} is high risk and requires explicit human approval.",
                policy="tool_authorization",
            )

        if not set(roles).intersection(policy.allowed_roles):
            return PolicyDecision(
                decision=Decision.DENY,
                risk=policy.risk,
                reason=f"Role set is not allowed to use {tool_name}.",
                policy="tool_authorization",
            )

        return PolicyDecision(
            decision=Decision.ALLOW,
            risk=policy.risk,
            reason=f"Tool {tool_name} allowed by role policy.",
            policy="tool_authorization",
        )
