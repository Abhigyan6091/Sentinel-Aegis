from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.findings.service import (
    get_finding,
    list_findings,
    promote_to_regression_case,
    update_finding,
)
from app.regression.fixtures import RegressionCase
from app.schemas.findings import (
    FindingRecord,
    FindingStatus,
    FindingUpdate,
    RegressionCasePromotion,
)

router = APIRouter(prefix="/findings", tags=["findings"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("", response_model=list[FindingRecord])
async def list_findings_route(
    identity: CurrentIdentity,
    session: DatabaseSession,
    status: Annotated[list[FindingStatus] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[FindingRecord]:
    findings = await list_findings(session, identity.tenant_id, status, limit)
    return [FindingRecord.model_validate(finding) for finding in findings]


@router.get("/{finding_id}", response_model=FindingRecord)
async def get_finding_route(
    finding_id: str,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> FindingRecord:
    return FindingRecord.model_validate(
        await get_finding(session, identity.tenant_id, finding_id)
    )


@router.patch("/{finding_id}", response_model=FindingRecord)
async def update_finding_route(
    finding_id: str,
    payload: FindingUpdate,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> FindingRecord:
    return FindingRecord.model_validate(
        await update_finding(session, identity, finding_id, payload)
    )


@router.post("/{finding_id}/regression-case", response_model=RegressionCase, status_code=201)
async def promote_finding_route(
    finding_id: str,
    payload: RegressionCasePromotion,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> RegressionCase:
    return await promote_to_regression_case(session, identity, finding_id, payload)
