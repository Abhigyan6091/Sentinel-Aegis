from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.models.foundation import ApprovalRequest, Policy
from app.schemas.policies import ApprovalDecision, PolicyCreate
from app.security.policy import PolicyEngine, ToolPolicy
from app.security.runtime import Risk


async def create_policy(
    session: AsyncSession,
    identity: RequestIdentity,
    payload: PolicyCreate,
) -> Policy:
    version = await next_policy_version(session, identity.tenant_id, payload.name)
    policy = Policy(
        tenant_id=identity.tenant_id,
        application_id=payload.application_id or identity.application_id,
        name=payload.name,
        document=payload.document,
        status="draft",
        version=version,
    )
    session.add(policy)
    await session.commit()
    await session.refresh(policy)
    return policy


async def list_policies(session: AsyncSession, identity: RequestIdentity) -> list[Policy]:
    result = await session.scalars(
        select(Policy)
        .where(Policy.tenant_id == identity.tenant_id)
        .order_by(Policy.created_at.desc())
    )
    return list(result)


async def activate_policy(
    session: AsyncSession,
    identity: RequestIdentity,
    policy_id: str,
) -> Policy | None:
    policy = await session.scalar(
        select(Policy).where(Policy.id == policy_id, Policy.tenant_id == identity.tenant_id)
    )
    if policy is None:
        return None
    await session.execute(
        update(Policy)
        .where(Policy.tenant_id == identity.tenant_id, Policy.name == policy.name)
        .values(status="inactive")
    )
    policy.status = "active"
    await session.commit()
    await session.refresh(policy)
    return policy


async def active_policy_engine(
    session: AsyncSession | None,
    identity: RequestIdentity,
) -> PolicyEngine:
    if session is None:
        return PolicyEngine.default()
    policy = await session.scalar(
        select(Policy)
        .where(Policy.tenant_id == identity.tenant_id, Policy.status == "active")
        .order_by(Policy.updated_at.desc())
    )
    if policy is None:
        return PolicyEngine.default()
    return PolicyEngine.from_document(policy.document)


async def record_approval_request(
    session: AsyncSession | None,
    identity: RequestIdentity,
    request_id: str,
    tool_name: str,
    arguments: dict[str, str],
    risk: str,
) -> ApprovalRequest | None:
    if session is None:
        return None
    approval = ApprovalRequest(
        tenant_id=identity.tenant_id,
        request_id=request_id,
        application_id=identity.application_id,
        tool_name=tool_name,
        arguments=arguments,
        risk=risk,
        status="pending",
    )
    session.add(approval)
    await session.commit()
    await session.refresh(approval)
    return approval


async def list_approvals(session: AsyncSession, identity: RequestIdentity) -> list[ApprovalRequest]:
    result = await session.scalars(
        select(ApprovalRequest)
        .where(ApprovalRequest.tenant_id == identity.tenant_id)
        .order_by(ApprovalRequest.created_at.desc())
    )
    return list(result)


async def decide_approval(
    session: AsyncSession,
    identity: RequestIdentity,
    approval_id: str,
    payload: ApprovalDecision,
) -> ApprovalRequest | None:
    approval = await session.scalar(
        select(ApprovalRequest).where(
            ApprovalRequest.id == approval_id,
            ApprovalRequest.tenant_id == identity.tenant_id,
        )
    )
    if approval is None:
        return None
    approval.status = payload.decision
    approval.decision_reason = payload.reason
    approval.decided_by = identity.user_id
    await session.commit()
    await session.refresh(approval)
    return approval


async def next_policy_version(session: AsyncSession, tenant_id: str, name: str) -> int:
    policies = await session.scalars(
        select(Policy).where(Policy.tenant_id == tenant_id, Policy.name == name)
    )
    versions = [policy.version for policy in policies]
    return max(versions, default=0) + 1


def tool_policies_from_document(document: dict) -> dict[str, ToolPolicy]:
    tools: dict[str, ToolPolicy] = {}
    for tool_name, policy in document.get("tools", {}).items():
        tools[tool_name] = ToolPolicy(
            risk=Risk(str(policy.get("risk", "MEDIUM"))),
            allowed_roles=[str(role) for role in policy.get("allowed_roles", [])],
            require_approval=bool(policy.get("require_approval", False)),
        )
    return tools
