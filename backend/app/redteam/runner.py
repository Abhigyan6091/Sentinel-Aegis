from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.observability.service import record_campaign_result
from app.redteam.attacks import AttackGenerator
from app.redteam.evaluator import SecurityEvaluator
from app.redteam.scoring import SecurityScorer
from app.schemas.redteam import (
    BenchmarkCreate,
    BenchmarkResponse,
    BenchmarkRun,
    CampaignAttackResult,
    CampaignCreate,
    CampaignRunResponse,
    CampaignSummary,
    DefenseMode,
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

    def get(self, tenant_id: str, campaign_id: str) -> CampaignRunResponse | None:
        for campaign in self._campaigns.get(tenant_id, []):
            if campaign.campaign.campaign_id == campaign_id:
                return campaign
        return None

    def findings(self, tenant_id: str):
        campaigns = self._campaigns.get(tenant_id, [])
        return [finding for campaign in campaigns for finding in campaign.findings]

    def clear(self) -> None:
        self._campaigns.clear()


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
        campaign_id = new_campaign_id()
        attack_results: list[CampaignAttackResult] = []
        evaluations = []
        findings = []

        for variant in variants:
            # Each attack is its own conversation so multi-turn state from one attack
            # cannot block the next and mask an unrelated defense's behavior.
            chat_request = SupportChatRequest(
                message=variant.payload,
                application_id=identity.application_id,
                conversation_id=f"{campaign_id}:{variant.attack_id}",
            )
            if request.defense_mode == DefenseMode.NO_DEFENSE:
                runtime_response = await self.agent.run_without_defenses(chat_request, identity)
            else:
                runtime_response = await self.agent.run(chat_request, identity, session)
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
                campaign_id=campaign_id,
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
            defense_mode=request.defense_mode,
        )
        campaign_store.add(identity.tenant_id, response)
        await record_campaign_result(session, identity, response)
        return response


class BenchmarkRunner:
    async def run(
        self,
        request: BenchmarkCreate,
        identity: RequestIdentity,
        session: AsyncSession | None = None,
    ) -> BenchmarkResponse:
        runs: list[BenchmarkRun] = []
        for mode in request.defense_modes:
            campaign = await CampaignRunner().run(
                CampaignCreate(
                    name=f"{request.name} - {mode.value}",
                    categories=request.categories,
                    attack_count=request.attack_count,
                    mutation_depth=request.mutation_depth,
                    defense_mode=mode,
                ),
                identity,
                session,
            )
            runs.append(
                BenchmarkRun(
                    defense_mode=mode,
                    score=campaign.score,
                    findings_count=len(campaign.findings),
                    attack_success_rate=campaign.score.attack_success_rate,
                )
            )
        return BenchmarkResponse(name=request.name, tenant_id=identity.tenant_id, runs=runs)
