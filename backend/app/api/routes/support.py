from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.schemas.support import SupportChatRequest, SupportChatResponse
from app.support.agent import SupportAgent

router = APIRouter(prefix="/support", tags=["support-agent"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.post("/chat", response_model=SupportChatResponse)
async def chat(
    payload: SupportChatRequest,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> SupportChatResponse:
    agent = SupportAgent()
    return await agent.run(payload, identity, session)
