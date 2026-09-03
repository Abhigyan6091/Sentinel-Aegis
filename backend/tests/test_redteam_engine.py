from app.redteam.attacks import AttackCategory, AttackGenerator
from app.redteam.evaluator import SecurityEvaluator
from app.redteam.scoring import SecurityScorer
from app.schemas.support import SupportChatResponse
from app.security.runtime import Decision


def test_attack_generator_creates_bounded_variants_with_lineage():
    generator = AttackGenerator.default()

    variants = generator.generate(
        categories=[AttackCategory.PROMPT_INJECTION],
        attack_count=2,
        mutation_depth=2,
    )

    assert len(variants) == 2
    assert variants[0].attack_id.startswith("ATK-")
    assert variants[1].parent_attack_id == variants[0].attack_id
    assert variants[1].mutation_strategy == "benign_wrapper"


def test_evaluator_uses_structured_block_signal_for_prompt_injection():
    response = SupportChatResponse(
        request_id="req-1",
        answer="Request blocked by Sentinel Aegis input guardrails.",
        decision=Decision.BLOCK,
        blocked=True,
        guardrails=[],
        context_documents=[],
        allowed_context=[],
        tool_calls=[],
        trace=[],
        tokens={"input": 0, "output": 0},
    )
    variant = AttackGenerator.default().generate(
        categories=[AttackCategory.PROMPT_INJECTION],
        attack_count=1,
        mutation_depth=1,
    )[0]

    result = SecurityEvaluator().evaluate(variant, response)

    assert result.blocked is True
    assert result.successful_attack is False
    assert result.false_negative is False


def test_evaluator_flags_tool_abuse_when_high_risk_tool_is_allowed():
    response = SupportChatResponse(
        request_id="req-2",
        answer="Refund processed.",
        decision=Decision.ALLOW,
        blocked=False,
        guardrails=[],
        context_documents=[],
        allowed_context=[],
        tool_calls=[
            {
                "tool_name": "refund_order",
                "decision": "ALLOW",
                "risk": "HIGH",
                "reason": "Allowed",
                "executed": True,
                "result": {"status": "refunded"},
            }
        ],
        trace=[],
        tokens={"input": 5, "output": 2},
    )
    variant = AttackGenerator.default().generate(
        categories=[AttackCategory.TOOL_ABUSE],
        attack_count=1,
        mutation_depth=1,
    )[0]

    result = SecurityEvaluator().evaluate(variant, response)

    assert result.successful_attack is True
    assert result.false_negative is True
    assert result.finding is not None
    assert result.finding.severity == "CRITICAL"


def test_security_scorer_derives_scores_from_results():
    generator = AttackGenerator.default()
    variants = generator.generate(
        categories=[AttackCategory.PROMPT_INJECTION],
        attack_count=2,
        mutation_depth=1,
    )
    evaluator = SecurityEvaluator()
    blocked_response = SupportChatResponse(
        request_id="req-3",
        answer="blocked",
        decision=Decision.BLOCK,
        blocked=True,
        guardrails=[],
        context_documents=[],
        allowed_context=[],
        tool_calls=[],
        trace=[],
        tokens={"input": 0, "output": 0},
    )
    allowed_response = SupportChatResponse(
        request_id="req-4",
        answer="allowed",
        decision=Decision.ALLOW,
        blocked=False,
        guardrails=[],
        context_documents=[],
        allowed_context=[],
        tool_calls=[],
        trace=[],
        tokens={"input": 1, "output": 1},
    )
    results = [
        evaluator.evaluate(variants[0], blocked_response),
        evaluator.evaluate(variants[1], allowed_response),
    ]

    score = SecurityScorer().score(results)

    assert score.overall == 50
    assert score.attack_success_rate == 0.5
    assert score.attacks_executed == 2
