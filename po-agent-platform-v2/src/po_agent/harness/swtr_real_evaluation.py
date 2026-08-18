"""Bounded real-case SWTR shadow evaluation.

This module compares a baseline PO-agent decision with a candidate decision on
immutable snapshots captured from the read-only SWTR/AS21 boundary.  It has no
AS21 write capability and no promotion authority: the strongest positive
outcome is ``APPROVAL_REQUIRED`` for later governed handling.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
import math
import time
from typing import Callable, Mapping, Protocol

from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot


class RealShadowEvaluationError(RuntimeError):
    """Base failure for real SWTR shadow evaluation."""


class RealShadowBudgetExceeded(RealShadowEvaluationError):
    """Evaluation budget was exceeded before completion."""


class ShadowDecision(str, Enum):
    """Terminal comparison decision for one real task."""

    IMPROVED = "improved"
    EQUIVALENT = "equivalent"
    REGRESSED = "regressed"
    BLOCKED = "blocked"


class ShadowRunVerdict(str, Enum):
    """Run-level verdict.  Never grants production mutation authority."""

    NO_ACTION = "no_action"
    APPROVAL_REQUIRED = "approval_required"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AgentObservation:
    """Normalized output of one agent execution on a detached snapshot."""

    answer: str
    score: float
    grounded: bool
    hallucination: bool = False
    wrong_skill: bool = False
    provider_error: bool = False
    latency_ms: float = 0.0
    llm_calls: int = 0

    def __post_init__(self) -> None:
        if not self.answer.strip():
            raise ValueError("answer must not be empty")
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise ValueError("score must be numeric")
        if not math.isfinite(float(self.score)):
            raise ValueError("score must be finite")
        if self.latency_ms < 0:
            raise ValueError("latency_ms must be non-negative")
        if self.llm_calls < 0:
            raise ValueError("llm_calls must be non-negative")


class SnapshotAgent(Protocol):
    """Read-only callable used by the evaluator."""

    def __call__(self, snapshot: Mapping[str, object]) -> AgentObservation:
        ...


@dataclass(frozen=True, slots=True)
class RealShadowPolicy:
    """Safety and quality gates for one bounded real-case run."""

    max_cases: int = 30
    max_total_llm_calls: int = 200
    max_elapsed_seconds: float = 300.0
    min_score_delta: float = 0.05
    min_improved_cases: int = 2
    max_regressed_cases: int = 0
    reject_on_hallucination: bool = True
    reject_on_provider_error: bool = True
    reject_on_wrong_skill: bool = True

    def __post_init__(self) -> None:
        if self.max_cases <= 0:
            raise ValueError("max_cases must be positive")
        if self.max_total_llm_calls <= 0:
            raise ValueError("max_total_llm_calls must be positive")
        if self.max_elapsed_seconds <= 0:
            raise ValueError("max_elapsed_seconds must be positive")
        if self.min_score_delta < 0:
            raise ValueError("min_score_delta must be non-negative")
        if self.min_improved_cases <= 0:
            raise ValueError("min_improved_cases must be positive")
        if self.max_regressed_cases < 0:
            raise ValueError("max_regressed_cases must be non-negative")


@dataclass(frozen=True, slots=True)
class RealShadowCaseEvidence:
    task_key: str
    content_sha256: str
    baseline: AgentObservation
    candidate: AgentObservation
    decision: ShadowDecision
    score_delta: float
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class RealShadowRunEvidence:
    batch_sha256: str
    baseline_id: str
    candidate_id: str
    cases: tuple[RealShadowCaseEvidence, ...]
    verdict: ShadowRunVerdict
    improved_cases: int
    equivalent_cases: int
    regressed_cases: int
    blocked_cases: int
    total_llm_calls: int
    elapsed_ms: float
    run_sha256: str


class SWTRRealShadowEvaluator:
    """Compare baseline/candidate behavior on a real read-only SWTR corpus.

    Invariants:
    * accepts only immutable ``SWTRShadowBatch`` input;
    * agents receive detached dictionaries, never an adapter or source object;
    * fail-closed on provider errors, hallucinations and wrong-skill routing;
    * bounded by task, LLM-call and wall-clock budgets;
    * emits evidence only; never promotes, rolls back or mutates AS21.
    """

    def __init__(self, policy: RealShadowPolicy | None = None) -> None:
        self._policy = policy or RealShadowPolicy()

    @property
    def policy(self) -> RealShadowPolicy:
        return self._policy

    @staticmethod
    def _validate_identity(value: str, field: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field} must not be empty")
        return normalized

    def _blocked(self, observation: AgentObservation) -> bool:
        return (
            (self._policy.reject_on_provider_error and observation.provider_error)
            or (self._policy.reject_on_hallucination and observation.hallucination)
            or (self._policy.reject_on_wrong_skill and observation.wrong_skill)
            or not observation.grounded
        )

    def _compare(
        self,
        baseline: AgentObservation,
        candidate: AgentObservation,
    ) -> tuple[ShadowDecision, float]:
        if self._blocked(candidate):
            return ShadowDecision.BLOCKED, float(candidate.score - baseline.score)
        delta = float(candidate.score - baseline.score)
        if delta >= self._policy.min_score_delta:
            return ShadowDecision.IMPROVED, delta
        if delta <= -self._policy.min_score_delta:
            return ShadowDecision.REGRESSED, delta
        return ShadowDecision.EQUIVALENT, delta

    @staticmethod
    def _case_digest(
        case: SWTRTaskSnapshot,
        baseline: AgentObservation,
        candidate: AgentObservation,
        decision: ShadowDecision,
    ) -> str:
        material = {
            "task_key": case.task_key,
            "content_sha256": case.content_sha256,
            "baseline": baseline.__dict__ if hasattr(baseline, "__dict__") else {
                name: getattr(baseline, name) for name in baseline.__slots__
            },
            "candidate": candidate.__dict__ if hasattr(candidate, "__dict__") else {
                name: getattr(candidate, name) for name in candidate.__slots__
            },
            "decision": decision.value,
        }
        canonical = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(canonical.encode("utf-8")).hexdigest()

    def evaluate(
        self,
        batch: SWTRShadowBatch,
        *,
        baseline_id: str,
        candidate_id: str,
        baseline_agent: SnapshotAgent,
        candidate_agent: SnapshotAgent,
    ) -> RealShadowRunEvidence:
        baseline_id = self._validate_identity(baseline_id, "baseline_id")
        candidate_id = self._validate_identity(candidate_id, "candidate_id")
        if baseline_id == candidate_id:
            raise ValueError("baseline_id and candidate_id must differ")
        if not batch.cases:
            raise ValueError("real shadow batch must contain at least one case")
        if len(batch.cases) > self._policy.max_cases:
            raise RealShadowBudgetExceeded(
                f"batch has {len(batch.cases)} cases; budget is {self._policy.max_cases}"
            )

        started = time.monotonic()
        total_llm_calls = 0
        evidence: list[RealShadowCaseEvidence] = []

        for case in batch.cases:
            if time.monotonic() - started > self._policy.max_elapsed_seconds:
                raise RealShadowBudgetExceeded("real shadow wall-clock budget exceeded")

            baseline = baseline_agent(case.as_dict())
            candidate = candidate_agent(case.as_dict())
            if not isinstance(baseline, AgentObservation) or not isinstance(candidate, AgentObservation):
                raise TypeError("agents must return AgentObservation")

            total_llm_calls += baseline.llm_calls + candidate.llm_calls
            if total_llm_calls > self._policy.max_total_llm_calls:
                raise RealShadowBudgetExceeded("real shadow LLM-call budget exceeded")

            decision, delta = self._compare(baseline, candidate)
            evidence.append(
                RealShadowCaseEvidence(
                    task_key=case.task_key,
                    content_sha256=case.content_sha256,
                    baseline=baseline,
                    candidate=candidate,
                    decision=decision,
                    score_delta=delta,
                    evidence_sha256=self._case_digest(case, baseline, candidate, decision),
                )
            )

        improved = sum(item.decision is ShadowDecision.IMPROVED for item in evidence)
        equivalent = sum(item.decision is ShadowDecision.EQUIVALENT for item in evidence)
        regressed = sum(item.decision is ShadowDecision.REGRESSED for item in evidence)
        blocked = sum(item.decision is ShadowDecision.BLOCKED for item in evidence)

        if blocked or regressed > self._policy.max_regressed_cases:
            verdict = ShadowRunVerdict.REJECTED
        elif improved >= self._policy.min_improved_cases:
            verdict = ShadowRunVerdict.APPROVAL_REQUIRED
        else:
            verdict = ShadowRunVerdict.NO_ACTION

        elapsed_ms = (time.monotonic() - started) * 1000.0
        run_material = {
            "batch_sha256": batch.batch_sha256,
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "case_evidence": [item.evidence_sha256 for item in evidence],
            "verdict": verdict.value,
        }
        run_canonical = json.dumps(run_material, sort_keys=True, separators=(",", ":"))
        run_sha256 = sha256(run_canonical.encode("utf-8")).hexdigest()

        return RealShadowRunEvidence(
            batch_sha256=batch.batch_sha256,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            cases=tuple(evidence),
            verdict=verdict,
            improved_cases=improved,
            equivalent_cases=equivalent,
            regressed_cases=regressed,
            blocked_cases=blocked,
            total_llm_calls=total_llm_calls,
            elapsed_ms=elapsed_ms,
            run_sha256=run_sha256,
        )
