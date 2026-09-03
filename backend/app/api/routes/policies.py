from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.policies.service import activate_policy, create_policy, list_policies
from app.schemas.policies import PolicyCreate, PolicyRead

router = APIRouter(prefix="/policies", tags=["policies"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
async def create_policy_route(
    payload: PolicyCreate,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> PolicyRead:
    return await create_policy(session, identity, payload)


@router.get("", response_model=list[PolicyRead])
async def list_policies_route(
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> list[PolicyRead]:
    return await list_policies(session, identity)


@router.post("/{policy_id}/activate", response_model=PolicyRead)
async def activate_policy_route(
    policy_id: str,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> PolicyRead:
    policy = await activate_policy(session, identity, policy_id)
    if policy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy
