from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.rag.service import RagService
from app.schemas.rag import (
    RagDocumentIngest,
    RagDocumentIngested,
    RagSearchRequest,
    RagSearchResponse,
)

router = APIRouter(prefix="/rag", tags=["rag"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "/documents",
    response_model=RagDocumentIngested,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_document(
    payload: RagDocumentIngest,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> RagDocumentIngested:
    document, chunks = await RagService(session).ingest_document(payload, identity)
    return RagDocumentIngested(
        document_id=document.id,
        chunk_count=len(chunks),
        source=document.source,
        created_at=document.created_at,
    )


@router.post("/search", response_model=RagSearchResponse)
async def search_documents(
    payload: RagSearchRequest,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> RagSearchResponse:
    results = await RagService(session).search(payload, identity)
    return RagSearchResponse(results=results)
