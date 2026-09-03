from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.observability.metrics import render_metrics
from app.observability.service import build_summary, list_traces

router = APIRouter(tags=["observability"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("/metrics")
async def metrics_endpoint() -> Response:
    return Response(content=render_metrics(), media_type="text/plain; version=0.0.4")


@router.get("/api/v1/observability/summary")
async def read_summary(
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> dict[str, int | float]:
    return await build_summary(session, identity.tenant_id)


@router.get("/api/v1/observability/traces")
async def read_traces(identity: CurrentIdentity, session: DatabaseSession):
    traces = await list_traces(session, identity.tenant_id)
    return [
        {
            "id": trace.id,
            "request_id": trace.request_id,
            "application_id": trace.application_id,
            "spans": trace.spans,
            "created_at": trace.created_at,
        }
        for trace in traces
    ]
