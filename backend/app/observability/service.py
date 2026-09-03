from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.models.foundation import (
    Application,
    Attack,
    AttackCampaign,
    AttackResult,
    EvaluationRun,
    Finding,
    SecurityEvent,
    Trace,
)
from app.observability import metrics
from app.redteam.evaluator import AttackEvaluation, FindingCandidate
from app.redteam.scoring import SecurityScore
from app.schemas.redteam import CampaignRunResponse
from app.schemas.support import SupportChatResponse, TraceStep
from app.security.runtime import Decision


async def record_support_response(
    session: AsyncSession | None,
    identity: RequestIdentity,
    response: SupportChatResponse,
) -> None:
    metrics.requests_total.labels(
        tenant_id=identity.tenant_id,
        decision=response.decision.value,
    ).inc()
    for guardrail in response.guardrails:
        if guardrail.decision == Decision.BLOCK:
            metrics.guardrail_blocks_total.labels(
                tenant_id=identity.tenant_id,
                guardrail=guardrail.guardrail,
            ).inc()

    if session is None:
        return

    await persist_trace(session, identity, response.request_id, response.trace)


async def persist_trace(
    session: AsyncSession,
    identity: RequestIdentity,
    request_id: str,
    trace: list[TraceStep],
) -> None:
    session.add(
        Trace(
            tenant_id=identity.tenant_id,
            request_id=request_id,
            application_id=identity.application_id,
            spans=[step.model_dump() for step in trace],
        )
    )
    await session.commit()


async def record_campaign_result(
    session: AsyncSession | None,
    identity: RequestIdentity,
    campaign: CampaignRunResponse,
) -> None:
    metrics.campaigns_total.labels(tenant_id=identity.tenant_id).inc()
    for result in campaign.results:
        outcome = "successful" if result.evaluation.successful_attack else "mitigated"
        metrics.attack_results_total.labels(tenant_id=identity.tenant_id, outcome=outcome).inc()

    if session is None:
        return

    application_id = await ensure_application(session, identity)
    await ensure_campaign(session, identity, campaign, application_id)

    session.add(
        EvaluationRun(
            tenant_id=identity.tenant_id,
            application_id=application_id,
            campaign_id=campaign.campaign.campaign_id,
            mode="rules_and_signals",
            metrics=campaign.score.model_dump(),
            status="completed",
        )
    )
    for result in campaign.results:
        await ensure_attack(session, identity, result.evaluation)
        await persist_attack_result(
            session,
            identity,
            application_id,
            campaign.campaign.campaign_id,
            result.evaluation,
        )
        if result.evaluation.finding is not None:
            # The payload and observed signals travel with the finding so it can later
            # be promoted into a replayable regression fixture without the campaign.
            await persist_finding(
                session,
                identity,
                application_id,
                campaign.campaign.campaign_id,
                result.evaluation.finding,
                evidence={
                    "payload": result.variant.payload,
                    "expected_behavior": result.variant.expected_behavior,
                    "detection_signals": result.evaluation.detection_signals,
                    "defense_mode": campaign.defense_mode.value,
                },
            )
    await session.commit()


async def ensure_application(session: AsyncSession, identity: RequestIdentity) -> str:
    application_id = identity.application_id or "enterprise-support-agent"
    existing = await session.scalar(
        select(Application).where(
            Application.id == application_id,
            Application.tenant_id == identity.tenant_id,
        )
    )
    if existing is None:
        session.add(
            Application(
                id=application_id,
                tenant_id=identity.tenant_id,
                name="Enterprise Support Agent",
                description="Deterministic support target used by Sentinel Aegis.",
                status="active",
            )
        )
        await session.flush()
    return application_id


async def ensure_campaign(
    session: AsyncSession,
    identity: RequestIdentity,
    campaign: CampaignRunResponse,
    application_id: str,
) -> None:
    existing = await session.scalar(
        select(AttackCampaign).where(
            AttackCampaign.id == campaign.campaign.campaign_id,
            AttackCampaign.tenant_id == identity.tenant_id,
        )
    )
    if existing is not None:
        return
    session.add(
        AttackCampaign(
            id=campaign.campaign.campaign_id,
            tenant_id=identity.tenant_id,
            application_id=application_id,
            name=campaign.campaign.name,
            config={
                "attack_count": campaign.campaign.attack_count,
                "mutation_depth": campaign.campaign.mutation_depth,
            },
            status=campaign.campaign.status,
        )
    )
    await session.flush()


async def ensure_attack(
    session: AsyncSession,
    identity: RequestIdentity,
    evaluation: AttackEvaluation,
) -> None:
    existing = await session.scalar(
        select(Attack).where(
            Attack.id == evaluation.attack_id,
            Attack.tenant_id == identity.tenant_id,
        )
    )
    if existing is not None:
        return
    session.add(
        Attack(
            id=evaluation.attack_id,
            tenant_id=identity.tenant_id,
            category=evaluation.category.value,
            severity=evaluation.severity,
            payload="[campaign payload redacted]",
            expected_behavior=(
                "Sentinel Aegis should detect, block, sanitize, or gate unsafe behavior."
            ),
            metadata_={"source": "runtime_campaign"},
        )
    )
    await session.flush()


async def persist_attack_result(
    session: AsyncSession,
    identity: RequestIdentity,
    application_id: str,
    campaign_id: str,
    evaluation: AttackEvaluation,
) -> None:
    session.add(
        AttackResult(
            tenant_id=identity.tenant_id,
            campaign_id=campaign_id,
            attack_id=evaluation.attack_id,
            application_id=application_id,
            result="successful" if evaluation.successful_attack else "mitigated",
            signals={"items": evaluation.detection_signals},
            latency_ms=evaluation.latency_ms,
        )
    )


async def persist_finding(
    session: AsyncSession,
    identity: RequestIdentity,
    application_id: str,
    campaign_id: str,
    finding: FindingCandidate,
    evidence: dict | None = None,
) -> None:
    session.add(
        Finding(
            id=f"{campaign_id}-{finding.finding_id}",
            tenant_id=identity.tenant_id,
            application_id=application_id,
            attack_id=finding.attack_id,
            campaign_id=campaign_id,
            severity=finding.severity,
            title=finding.title,
            category=finding.category,
            affected_component=finding.affected_component,
            description=finding.description,
            impact=finding.impact,
            root_cause=finding.root_cause,
            recommendation=finding.recommendation,
            status=finding.status.lower(),
            evidence=evidence or {},
            reproduction_steps=[],
        )
    )


async def build_summary(session: AsyncSession, tenant_id: str) -> dict[str, int | float]:
    request_count = await count_rows(session, Trace, tenant_id)
    security_events = await count_rows(session, SecurityEvent, tenant_id)
    attack_results = await count_rows(session, AttackResult, tenant_id)
    campaigns = await count_rows(session, EvaluationRun, tenant_id)
    findings = await count_rows(session, Finding, tenant_id)
    guardrail_blocks = await count_events(session, tenant_id, "PROMPT_INJECTION_DETECTED")
    pii_redactions = await count_events(session, tenant_id, "PII_REDACTED")
    latest_score = await latest_evaluation_score(session, tenant_id)

    return {
        "request_count": request_count,
        "security_events": security_events,
        "attack_results": attack_results,
        "campaigns": campaigns,
        "findings": findings,
        "guardrail_blocks": guardrail_blocks,
        "pii_redactions": pii_redactions,
        "latest_score": latest_score,
    }


async def count_rows(session: AsyncSession, model, tenant_id: str) -> int:
    value = await session.scalar(
        select(func.count()).select_from(model).where(model.tenant_id == tenant_id)
    )
    return int(value or 0)


async def count_events(session: AsyncSession, tenant_id: str, event_type: str) -> int:
    value = await session.scalar(
        select(func.count())
        .select_from(SecurityEvent)
        .where(SecurityEvent.tenant_id == tenant_id, SecurityEvent.event_type == event_type)
    )
    return int(value or 0)


async def latest_evaluation_score(session: AsyncSession, tenant_id: str) -> int:
    run = await session.scalar(
        select(EvaluationRun)
        .where(EvaluationRun.tenant_id == tenant_id)
        .order_by(EvaluationRun.created_at.desc())
    )
    if run is None:
        return 0
    score = SecurityScore.model_validate(run.metrics)
    return score.overall


async def list_traces(session: AsyncSession, tenant_id: str) -> list[Trace]:
    result = await session.scalars(
        select(Trace)
        .where(Trace.tenant_id == tenant_id)
        .order_by(Trace.created_at.desc())
        .limit(50)
    )
    return list(result)
