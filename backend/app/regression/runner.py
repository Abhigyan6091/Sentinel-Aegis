"""Replays committed regression cases against the live runtime.

This runner is deliberately separate from the campaign runner: campaigns explore a
generated attack space and are expected to surface new findings, while the regression
suite replays a fixed, committed set and must stay green.
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.identity import RequestIdentity
from app.redteam.evaluator import SecurityEvaluator
from app.regression.fixtures import FixtureStore, RegressionCase
from app.schemas.redteam import DefenseMode
from app.schemas.support import SupportChatRequest
from app.support.agent import SupportAgent


class RegressionCaseResult(BaseModel):
    case_id: str
    title: str
    category: str
    severity: str
    expected_mitigated: bool
    mitigated: bool
    passed: bool
    detection_signals: list[str]
    reason: str


class RegressionSuiteResult(BaseModel):
    defense_mode: DefenseMode
    tenant_id: str
    total: int
    passed: int
    failed: int
    started_at: datetime
    completed_at: datetime
    cases: list[RegressionCaseResult] = Field(default_factory=list)

    @property
    def is_green(self) -> bool:
        return self.failed == 0


class RegressionSuiteRunner:
    def __init__(
        self,
        store: FixtureStore | None = None,
        agent: SupportAgent | None = None,
        evaluator: SecurityEvaluator | None = None,
    ) -> None:
        self.store = store or FixtureStore()
        self.agent = agent or SupportAgent()
        self.evaluator = evaluator or SecurityEvaluator()

    async def run(
        self,
        identity: RequestIdentity,
        session: AsyncSession | None = None,
        defense_mode: DefenseMode = DefenseMode.LAYERED,
        case_ids: list[str] | None = None,
    ) -> RegressionSuiteResult:
        started_at = datetime.now(timezone.utc)
        cases = self._select(case_ids)
        results = [
            await self._run_case(case, identity, session, defense_mode) for case in cases
        ]
        passed = sum(1 for result in results if result.passed)

        return RegressionSuiteResult(
            defense_mode=defense_mode,
            tenant_id=identity.tenant_id,
            total=len(results),
            passed=passed,
            failed=len(results) - passed,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            cases=results,
        )

    def _select(self, case_ids: list[str] | None) -> list[RegressionCase]:
        cases = self.store.load_all()
        if case_ids is None:
            return cases
        wanted = set(case_ids)
        return [case for case in cases if case.case_id in wanted]

    async def _run_case(
        self,
        case: RegressionCase,
        identity: RequestIdentity,
        session: AsyncSession | None,
        defense_mode: DefenseMode,
    ) -> RegressionCaseResult:
        chat_request = SupportChatRequest(
            message=case.payload,
            application_id=identity.application_id,
            conversation_id=f"regression:{case.case_id}",
        )
        if defense_mode == DefenseMode.NO_DEFENSE:
            response = await self.agent.run_without_defenses(chat_request, identity)
        else:
            response = await self.agent.run(chat_request, identity, session)

        evaluation = self.evaluator.evaluate(case.to_variant(), response)
        mitigated = not evaluation.successful_attack
        passed = mitigated == case.expected_mitigated

        return RegressionCaseResult(
            case_id=case.case_id,
            title=case.title,
            category=case.category.value,
            severity=case.severity,
            expected_mitigated=case.expected_mitigated,
            mitigated=mitigated,
            passed=passed,
            detection_signals=evaluation.detection_signals,
            reason=(
                "Runtime produced the expected defensive outcome."
                if passed
                else (
                    "Regression: the runtime no longer mitigates this attack."
                    if case.expected_mitigated
                    else "Case expected an unmitigated outcome but the runtime blocked it."
                )
            ),
        )
