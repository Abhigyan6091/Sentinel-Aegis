import re

from pydantic import BaseModel

from app.security.runtime import Decision, Risk

_UNTRUSTED_INSTRUCTION_RE = re.compile(
    r"(ignore|disregard|override|call\s+\w+_order|reveal\s+the\s+system)",
    re.IGNORECASE,
)


class DocumentDecision(BaseModel):
    document_id: str
    source: str
    tenant_id: str
    action: Decision
    risk: Risk
    trust_score: float
    sensitivity: str
    contains_instructions: bool
    reason: str
    content: str


class ContextFirewallResult(BaseModel):
    documents: list[DocumentDecision]
    allowed_context: list[str]


class ContextFirewall:
    def inspect(self, documents: list[dict]) -> ContextFirewallResult:
        decisions: list[DocumentDecision] = []
        allowed_context: list[str] = []

        for document in documents:
            content = str(document.get("content", ""))
            trust_score = float(document.get("trust_score", 0.0))
            contains_instructions = bool(_UNTRUSTED_INSTRUCTION_RE.search(content))
            action = Decision.ALLOW
            risk = Risk.LOW
            reason = "Document allowed as untrusted reference context."

            if contains_instructions:
                action = Decision.ISOLATE
                risk = Risk.HIGH
                reason = "Retrieved document contains instruction-like content."
            elif trust_score < 0.4:
                action = Decision.SANITIZE
                risk = Risk.MEDIUM
                reason = "Low-trust document allowed only as sanitized context."
                content = content[:500]

            decision = DocumentDecision(
                document_id=str(document["document_id"]),
                source=str(document.get("source", "unknown")),
                tenant_id=str(document["tenant_id"]),
                action=action,
                risk=risk,
                trust_score=trust_score,
                sensitivity=str(document.get("sensitivity", "PUBLIC")),
                contains_instructions=contains_instructions,
                reason=reason,
                content=content,
            )
            decisions.append(decision)

            if action in {Decision.ALLOW, Decision.SANITIZE}:
                allowed_context.append(content)

        return ContextFirewallResult(documents=decisions, allowed_context=allowed_context)
