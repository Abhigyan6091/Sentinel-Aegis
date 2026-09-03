from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.redteam.attacks import AttackGenerator
from app.redteam.evaluator import SecurityEvaluator
from app.redteam.scoring import SecurityScorer
from app.schemas.redteam import (
    CampaignAttackResult,
    CampaignCreate,
    CampaignRunResponse,
    CampaignSummary,
    new_campaign_id,
)
from app.schemas.support import SupportChatRequest
from app.support.agent import SupportAgent


class CampaignStore:
    def __init__(self) -> None:
        self._campaigns: dict[str, list[CampaignRunResponse]] = {}

    def add(self, tenant_id: str, campaign: CampaignRunResponse) -> None:
        self._campaigns.setdefault(tenant_id, []).append(campaign)

    def latest(self, tenant_id: str) -> CampaignRunResponse | None:
        campaigns = self._campaigns.get(tenant_id, [])
        return campaigns[-1] if campaigns else None

    def findings(self, tenant_id: str):
        campaigns = self._campaigns.get(tenant_id, [])
        return [finding for campaign in campaigns for finding in campaign.findings]


campaign_store = CampaignStore()


class CampaignRunner:
    def __init__(
        self,
        generator: AttackGenerator | None = None,
        evaluator: SecurityEvaluator | None = None,
        scorer: SecurityScorer | None = None,
        agent: SupportAgent | None = None,
    ) -> None:
        self.generator = generator or AttackGenerator.default()
        self.evaluator = evaluator or SecurityEvaluator()
        self.scorer = scorer or SecurityScorer()
        self.agent = agent or SupportAgent()

    async def run(
        self,
        request: CampaignCreate,
        identity: RequestIdentity,
        session: AsyncSession | None = None,
    ) -> CampaignRunResponse:
        started_at = datetime.now(timezone.utc)
        variants = self.generator.generate(
            categories=request.categories,
            attack_count=request.attack_count,
            mutation_depth=request.mutation_depth,
        )
        attack_results: list[CampaignAttackResult] = []
        evaluations = []
        findings = []

        for variant in variants:
            runtime_response = await self.agent.run(
                SupportChatRequest(message=variant.payload, application_id=identity.application_id),
                identity,
                session,
            )
            evaluation = self.evaluator.evaluate(variant, runtime_response)
            evaluations.append(evaluation)
            if evaluation.finding is not None:
                findings.append(evaluation.finding)
            attack_results.append(
                CampaignAttackResult(
                    variant=variant,
                    runtime=runtime_response,
                    evaluation=evaluation,
                    trace=[step.model_dump() for step in runtime_response.trace],
                )
            )

        completed_at = datetime.now(timezone.utc)
        response = CampaignRunResponse(
            campaign=CampaignSummary(
                campaign_id=new_campaign_id(),
                tenant_id=identity.tenant_id,
                application_id=identity.application_id,
                name=request.name,
                status="completed",
                attack_count=len(variants),
                mutation_depth=request.mutation_depth,
                started_at=started_at,
                completed_at=completed_at,
            ),
            score=self.scorer.score(evaluations),
            results=attack_results,
            findings=findings,
        )
        campaign_store.add(identity.tenant_id, response)
        return response
