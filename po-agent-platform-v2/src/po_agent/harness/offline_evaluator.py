"""Offline/shadow evaluation and deterministic regression gate.

Candidates are evaluated against versioned eval cases without mutating runtime
configuration. Promotion remains a separate human-approved operation.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable, Protocol


class EvalOutcome(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    baseline: EvalOutcome
    candidate: EvalOutcome
    notes: tuple[str, ...] = ()

    @property
    def improved(self) -> bool:
        return self.baseline is EvalOutcome.FAIL and self.candidate is EvalOutcome.PASS

    @property
    def regressed(self) -> bool:
        return self.baseline is EvalOutcome.PASS and self.candidate is EvalOutcome.FAIL


@dataclass(frozen=True)
class EvaluationReport:
    candidate_id: str
    results: tuple[CaseResult, ...]

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def improvements(self) -> int:
        return sum(r.improved for r in self.results)

    @property
    def regressions(self) -> int:
        return sum(r.regressed for r in self.results)

    @property
    def candidate_passes(self) -> int:
        return sum(r.candidate is EvalOutcome.PASS for r in self.results)

    @property
    def candidate_pass_rate(self) -> float:
        applicable = [r for r in self.results if r.candidate is not EvalOutcome.NOT_APPLICABLE]
        if not applicable:
            return 0.0
        return sum(r.candidate is EvalOutcome.PASS for r in applicable) / len(applicable)


class CaseRunner(Protocol):
    def __call__(self, case: object, candidate: object | None) -> EvalOutcome: ...


class OfflineEvaluator:
    """Run baseline and proposed candidate on exactly the same eval corpus."""

    def __init__(self, runner: CaseRunner) -> None:
        self.runner = runner

    def evaluate(self, candidate_id: str, candidate: object, cases: Iterable[object]) -> EvaluationReport:
        results: list[CaseResult] = []
        for index, case in enumerate(cases):
            case_id = str(getattr(case, "case_id", getattr(case, "eval_id", index)))
            baseline = self.runner(case, None)
            proposed = self.runner(case, candidate)
            results.append(CaseResult(case_id=case_id, baseline=baseline, candidate=proposed))
        return EvaluationReport(candidate_id=candidate_id, results=tuple(results))


@dataclass(frozen=True)
class RegressionPolicy:
    """Conservative default: zero regressions and measurable improvement."""

    max_regressions: int = 0
    min_improvements: int = 1
    min_pass_rate: float = 0.0


@dataclass(frozen=True)
class GateDecision:
    candidate_id: str
    passed: bool
    status: str
    reasons: tuple[str, ...] = field(default_factory=tuple)
    requires_human_approval: bool = True


class RegressionGate:
    def __init__(self, policy: RegressionPolicy | None = None) -> None:
        self.policy = policy or RegressionPolicy()

    def decide(self, report: EvaluationReport) -> GateDecision:
        reasons: list[str] = []
        if report.regressions > self.policy.max_regressions:
            reasons.append(f"regressions={report.regressions} > {self.policy.max_regressions}")
        if report.improvements < self.policy.min_improvements:
            reasons.append(f"improvements={report.improvements} < {self.policy.min_improvements}")
        if report.candidate_pass_rate < self.policy.min_pass_rate:
            reasons.append(
                f"pass_rate={report.candidate_pass_rate:.3f} < {self.policy.min_pass_rate:.3f}"
            )
        passed = not reasons
        return GateDecision(
            candidate_id=report.candidate_id,
            passed=passed,
            status="ready_for_approval" if passed else "rejected_by_regression_gate",
            reasons=tuple(reasons),
            requires_human_approval=True,
        )
