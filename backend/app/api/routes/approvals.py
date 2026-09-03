from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.policies.service import decide_approval, list_approvals
from app.schemas.policies import ApprovalDecision, ApprovalRead

router = APIRouter(prefix="/approvals", tags=["approvals"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[ApprovalRead])
async def list_approvals_route(
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> list[ApprovalRead]:
    return await list_approvals(session, identity)


@router.post("/{approval_id}/decide", response_model=ApprovalRead)
async def decide_approval_route(
    approval_id: str,
    payload: ApprovalDecision,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> ApprovalRead:
    approval = await decide_approval(session, identity, approval_id, payload)
    if approval is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    return approval
