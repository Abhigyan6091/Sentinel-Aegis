"""Finding lifecycle: triage, remediation tracking, and regression promotion."""

from datetime import datetime, timezone

from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.models.foundation import Finding
from app.redteam.attacks import AttackCategory
from app.regression.fixtures import (
    FixtureStore,
    RegressionCase,
    build_regression_case,
    case_id_for,
)
from app.schemas.findings import (
    ALLOWED_TRANSITIONS,
    RESOLVED_STATUSES,
    FindingStatus,
    FindingUpdate,
    RegressionCasePromotion,
)


async def list_findings(
    session: AsyncSession,
    tenant_id: str,
    statuses: list[FindingStatus] | None = None,
    limit: int = 100,
) -> list[Finding]:
    query = select(Finding).where(Finding.tenant_id == tenant_id)
    if statuses:
        query = query.where(Finding.status.in_([item.value for item in statuses]))
    result = await session.scalars(query.order_by(Finding.created_at.desc()).limit(limit))
    return list(result)


async def get_finding(session: AsyncSession, tenant_id: str, finding_id: str) -> Finding:
    finding = await session.scalar(
        select(Finding).where(Finding.id == finding_id, Finding.tenant_id == tenant_id)
    )
    if finding is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )
    return finding


async def update_finding(
    session: AsyncSession,
    identity: RequestIdentity,
    finding_id: str,
    update: FindingUpdate,
) -> Finding:
    finding = await get_finding(session, identity.tenant_id, finding_id)

    if update.status is not None:
        current = FindingStatus(finding.status)
        if update.status != current and update.status not in ALLOWED_TRANSITIONS[current]:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=f"Cannot move finding from {current.value} to {update.status.value}",
            )
        finding.status = update.status.value
        finding.decided_by = update.decided_by or identity.user_id
        finding.resolved_at = (
            datetime.now(timezone.utc) if update.status in RESOLVED_STATUSES else None
        )

    if update.remediation is not None:
        finding.remediation = update.remediation
    if update.reproduction_steps is not None:
        finding.reproduction_steps = update.reproduction_steps

    await session.commit()
    await session.refresh(finding)
    return finding


async def promote_to_regression_case(
    session: AsyncSession,
    identity: RequestIdentity,
    finding_id: str,
    promotion: RegressionCasePromotion,
    store: FixtureStore | None = None,
) -> RegressionCase:
    """Turn a finding into a committed fixture the regression suite replays."""
    finding = await get_finding(session, identity.tenant_id, finding_id)
    payload = promotion.payload or _stored_payload(finding)
    if not payload:
        raise HTTPException(
            status_code=http_status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Finding has no recorded attack payload; supply one to promote it.",
        )

    case = build_regression_case(
        case_id=case_id_for(finding.category, finding.attack_id or finding.id),
        title=finding.title,
        category=AttackCategory(finding.category),
        severity=finding.severity,
        payload=payload,
        expected_behavior=(
            promotion.expected_behavior
            or _stored_expected_behavior(finding)
            or finding.recommendation
        ),
        detection_signals=_stored_signals(finding),
        source_finding_id=finding.id,
        source_campaign_id=finding.campaign_id,
        remediation=promotion.remediation or finding.remediation or finding.recommendation,
    )

    (store or FixtureStore()).save(case)
    finding.regression_case_id = case.case_id
    if FindingStatus(finding.status) == FindingStatus.OPEN:
        finding.status = FindingStatus.TRIAGED.value
    await session.commit()
    return case


def _stored_payload(finding: Finding) -> str | None:
    value = (finding.evidence or {}).get("payload")
    return value if isinstance(value, str) else None


def _stored_expected_behavior(finding: Finding) -> str | None:
    value = (finding.evidence or {}).get("expected_behavior")
    return value if isinstance(value, str) else None


def _stored_signals(finding: Finding) -> list[str]:
    value = (finding.evidence or {}).get("detection_signals")
    return [str(item) for item in value] if isinstance(value, list) else []
