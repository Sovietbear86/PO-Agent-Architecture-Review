"""Controlled learning loop for PO Agent Platform v2.

The loop is deliberately fail-closed: a candidate can be recommended only after
baseline/candidate evidence passes the promotion gate. Production promotion is
never performed here; explicit human approval remains a separate action.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional


class GateDecision(str, Enum):
    RECOMMEND = "recommend"
    REJECT = "reject"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class EvaluationSnapshot:
    total_cases: int
    passed_cases: int
    false_green_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def pass_rate(self) -> float:
        return self.passed_cases / self.total_cases if self.total_cases else 0.0


@dataclass(frozen=True)
class PromotionDecision:
    decision: GateDecision
    reasons: List[str]
    baseline: EvaluationSnapshot
    candidate: EvaluationSnapshot
    requires_human_approval: bool = True


class PromotionGate:
    """Compare a candidate with an immutable baseline and fail closed."""

    def __init__(self, min_cases: int = 8, min_pass_rate_delta: float = 0.0):
        self.min_cases = min_cases
        self.min_pass_rate_delta = min_pass_rate_delta

    def evaluate(
        self,
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
    ) -> PromotionDecision:
        reasons: List[str] = []
        if baseline.total_cases < self.min_cases or candidate.total_cases < self.min_cases:
            return PromotionDecision(
                GateDecision.INSUFFICIENT_EVIDENCE,
                ["evaluation sample is smaller than the required baseline"],
                baseline,
                candidate,
            )
        if candidate.false_green_count > 0:
            reasons.append("candidate produced false-green results")
        if candidate.error_count > baseline.error_count:
            reasons.append("candidate increased execution errors")
        if candidate.pass_rate < baseline.pass_rate + self.min_pass_rate_delta:
            reasons.append("candidate did not preserve/improve baseline pass rate")
        if candidate.total_cases != baseline.total_cases:
            reasons.append("baseline and candidate were evaluated on different case counts")

        decision = GateDecision.REJECT if reasons else GateDecision.RECOMMEND
        return PromotionDecision(decision, reasons, baseline, candidate)


class LearningLoop:
    """Orchestrates candidate comparison without production mutation."""

    def __init__(self, gate: Optional[PromotionGate] = None):
        self.gate = gate or PromotionGate()

    def compare(
        self,
        baseline: EvaluationSnapshot,
        candidate: EvaluationSnapshot,
    ) -> PromotionDecision:
        return self.gate.evaluate(baseline, candidate)

    def can_promote(self, decision: PromotionDecision, human_approved: bool = False) -> bool:
        """Promotion requires both a green gate and an explicit human decision."""
        return decision.decision == GateDecision.RECOMMEND and human_approved


__all__ = [
    "EvaluationSnapshot",
    "GateDecision",
    "LearningLoop",
    "PromotionDecision",
    "PromotionGate",
]
