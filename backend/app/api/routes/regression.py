from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.core.security import get_current_identity
from app.db.session import get_session
from app.regression.fixtures import FixtureStore, RegressionCase, build_regression_case
from app.regression.runner import RegressionSuiteResult, RegressionSuiteRunner
from app.reports.artifacts import ArtifactStore
from app.reports.service import regression_report_markdown
from app.schemas.regression import RegressionCaseCreate, RegressionSuiteRequest

router = APIRouter(prefix="/regression", tags=["regression"])
CurrentIdentity = Annotated[RequestIdentity, Depends(get_current_identity)]
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


@router.get("/cases", response_model=list[RegressionCase])
async def list_cases_route(identity: CurrentIdentity) -> list[RegressionCase]:
    del identity
    return FixtureStore().load_all()


@router.post("/cases", response_model=RegressionCase, status_code=status.HTTP_201_CREATED)
async def create_case_route(
    payload: RegressionCaseCreate,
    identity: CurrentIdentity,
) -> RegressionCase:
    del identity
    case = build_regression_case(
        case_id=payload.case_id,
        title=payload.title,
        category=payload.category,
        severity=payload.severity,
        payload=payload.payload,
        expected_behavior=payload.expected_behavior,
        detection_signals=[],
        remediation=payload.remediation,
    )
    case.expected_mitigated = payload.expected_mitigated
    FixtureStore().save(case)
    return case


@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_route(case_id: str, identity: CurrentIdentity) -> None:
    del identity
    try:
        deleted = FixtureStore().delete(case_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regression case not found",
        )


@router.post("/runs", response_model=RegressionSuiteResult, status_code=status.HTTP_201_CREATED)
async def run_suite_route(
    payload: RegressionSuiteRequest,
    identity: CurrentIdentity,
    session: DatabaseSession,
) -> RegressionSuiteResult:
    result = await RegressionSuiteRunner().run(
        identity,
        session,
        defense_mode=payload.defense_mode,
        case_ids=payload.case_ids,
    )
    if payload.store_artifact:
        ArtifactStore().write(
            f"regression-{identity.tenant_id}-{result.defense_mode.value}.md",
            regression_report_markdown(result),
        )
    return result
