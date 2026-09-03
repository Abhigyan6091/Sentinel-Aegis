import re
from collections import OrderedDict
from time import perf_counter

from app.security.runtime import Decision, GuardrailResult, Risk, latency_ms

_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
_SECRET_RE = re.compile(
    r"\b(?:sk-proj|sk|AKIA|ghp|xoxb|xoxp)[A-Za-z0-9_-]{10,}\b",
    re.IGNORECASE,
)
_INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
    re.compile(r"reveal\s+(the\s+)?(system|developer)\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(dan|developer|system)", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions", re.IGNORECASE),
)


def redact_pii(text: str) -> str:
    redacted = _SSN_RE.sub("[REDACTED_SSN]", text)
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    return _CREDIT_CARD_RE.sub("[REDACTED_PAYMENT_CARD]", redacted)


def redact_secrets(text: str) -> str:
    return _SECRET_RE.sub("[REDACTED_SECRET]", text)


class PromptInjectionDetector:
    guardrail = "prompt_injection"

    async def evaluate(self, text: str) -> GuardrailResult:
        started_at = perf_counter()
        normalized = " ".join(text.split())
        for pattern in _INJECTION_PATTERNS:
            if pattern.search(normalized):
                return GuardrailResult(
                    decision=Decision.BLOCK,
                    risk=Risk.CRITICAL,
                    confidence=0.93,
                    reason=(
                        "Instruction hierarchy override or system prompt extraction attempt "
                        "detected."
                    ),
                    guardrail=self.guardrail,
                    latency_ms=latency_ms(started_at),
                )

        risk = Risk.MEDIUM if "system prompt" in normalized.lower() else Risk.LOW
        decision = Decision.WARN if risk == Risk.MEDIUM else Decision.ALLOW
        return GuardrailResult(
            decision=decision,
            risk=risk,
            confidence=0.62 if decision == Decision.WARN else 0.82,
            reason="No direct prompt injection pattern detected.",
            guardrail=self.guardrail,
            latency_ms=latency_ms(started_at),
        )


class PIIDetector:
    guardrail = "pii"

    async def evaluate(self, text: str) -> GuardrailResult:
        started_at = perf_counter()
        if _SSN_RE.search(text) or _CREDIT_CARD_RE.search(text):
            return GuardrailResult(
                decision=Decision.SANITIZE,
                risk=Risk.HIGH,
                confidence=0.96,
                reason="Sensitive personal or payment data detected.",
                guardrail=self.guardrail,
                latency_ms=latency_ms(started_at),
            )
        if _EMAIL_RE.search(text):
            return GuardrailResult(
                decision=Decision.SANITIZE,
                risk=Risk.MEDIUM,
                confidence=0.9,
                reason="Email address detected.",
                guardrail=self.guardrail,
                latency_ms=latency_ms(started_at),
            )
        return GuardrailResult(
            decision=Decision.ALLOW,
            risk=Risk.LOW,
            confidence=0.85,
            reason="No PII pattern detected.",
            guardrail=self.guardrail,
            latency_ms=latency_ms(started_at),
        )


class SecretDetector:
    guardrail = "secret"

    async def evaluate(self, text: str) -> GuardrailResult:
        started_at = perf_counter()
        if _SECRET_RE.search(text):
            return GuardrailResult(
                decision=Decision.SANITIZE,
                risk=Risk.CRITICAL,
                confidence=0.94,
                reason="Credential-like secret detected.",
                guardrail=self.guardrail,
                latency_ms=latency_ms(started_at),
            )
        return GuardrailResult(
            decision=Decision.ALLOW,
            risk=Risk.LOW,
            confidence=0.86,
            reason="No credential-like secret detected.",
            guardrail=self.guardrail,
            latency_ms=latency_ms(started_at),
        )


class MultiTurnPromptInjectionDetector:
    """Tracks one conversation so overrides split across turns are still detected."""

    guardrail = "multi_turn_prompt_injection"
    history_window = 4

    def __init__(self) -> None:
        self.history: list[str] = []

    async def evaluate(self, text: str) -> GuardrailResult:
        started_at = perf_counter()
        normalized = " ".join([*self.history, text]).lower()
        self.history.append(text)
        self.history = self.history[-self.history_window :]
        has_fragmented_override = (
            "ignore" in normalized
            and "previous instructions" in normalized
            and "system prompt" in normalized
        )
        if has_fragmented_override:
            return GuardrailResult(
                decision=Decision.BLOCK,
                risk=Risk.CRITICAL,
                confidence=0.88,
                reason="Fragmented multi-turn instruction override detected.",
                guardrail=self.guardrail,
                latency_ms=latency_ms(started_at),
            )
        return GuardrailResult(
            decision=Decision.ALLOW,
            risk=Risk.LOW,
            confidence=0.78,
            reason="No multi-turn prompt injection pattern detected.",
            guardrail=self.guardrail,
            latency_ms=latency_ms(started_at),
        )


class ConversationMemory:
    """Holds multi-turn detector state per conversation, scoped by tenant.

    Turns from different tenants, chat sessions, or red-team attacks must never share
    history: one tenant's earlier turn would otherwise block another's unrelated request.
    """

    def __init__(self, max_conversations: int = 512) -> None:
        self._detectors: OrderedDict[
            tuple[str, str], MultiTurnPromptInjectionDetector
        ] = OrderedDict()
        self._max_conversations = max_conversations

    def detector(self, tenant_id: str, conversation_id: str) -> MultiTurnPromptInjectionDetector:
        key = (tenant_id, conversation_id)
        detector = self._detectors.pop(key, None) or MultiTurnPromptInjectionDetector()
        self._detectors[key] = detector
        while len(self._detectors) > self._max_conversations:
            self._detectors.popitem(last=False)
        return detector

    def clear(self) -> None:
        self._detectors.clear()


_conversation_memory = ConversationMemory()


def get_conversation_memory() -> ConversationMemory:
    return _conversation_memory
