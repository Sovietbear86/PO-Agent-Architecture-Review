"""Controlled lifecycle for evidence-backed Harness improvements.

This module is deliberately non-executing: it can register proposals, attach
offline/shadow evaluation evidence, record human approval and produce a
promotion decision.  It never edits Skill Catalog, prompts or production code.
That separation is the safety boundary for future self-improving skill work.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from .improvement_candidates import ImprovementCandidate


class LifecycleState(str, Enum):
    DRAFT = "draft"
    EVALUATED = "evaluated"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"
    PROMOTED = "promoted"
    REJECTED = "rejected"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class EvaluationSnapshot:
    evaluation_id: str
    candidate_id: str
    created_at: str
    corpus_size: int
    passed: int
    failed: int
    safety_regressions: int = 0
    new_code_regressions: int = 0
    wrong_skill_selections: int = 0
    hallucinated_entities: int = 0
    ungrounded_answers: int = 0
    provider_errors: int = 0
    notes: str | None = None

    @property
    def pass_rate(self) -> float:
        if self.corpus_size <= 0:
            return 0.0
        return self.passed / self.corpus_size

    @classmethod
    def create(
        cls,
        *,
        candidate_id: str,
        corpus_size: int,
        passed: int,
        failed: int,
        safety_regressions: int = 0,
        new_code_regressions: int = 0,
        wrong_skill_selections: int = 0,
        hallucinated_entities: int = 0,
        ungrounded_answers: int = 0,
        provider_errors: int = 0,
        notes: str | None = None,
    ) -> "EvaluationSnapshot":
        if not candidate_id:
            raise ValueError("candidate_id is required")
        if corpus_size < 1:
            raise ValueError("corpus_size must be positive")
        if min(
            passed,
            failed,
            safety_regressions,
            new_code_regressions,
            wrong_skill_selections,
            hallucinated_entities,
            ungrounded_answers,
            provider_errors,
        ) < 0:
            raise ValueError("evaluation counters cannot be negative")
        if passed + failed != corpus_size:
            raise ValueError("passed + failed must equal corpus_size")
        return cls(
            evaluation_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            corpus_size=corpus_size,
            passed=passed,
            failed=failed,
            safety_regressions=safety_regressions,
            new_code_regressions=new_code_regressions,
            wrong_skill_selections=wrong_skill_selections,
            hallucinated_entities=hallucinated_entities,
            ungrounded_answers=ungrounded_answers,
            provider_errors=provider_errors,
            notes=notes,
        )


@dataclass(frozen=True)
class PromotionPolicy:
    min_corpus_size: int = 3
    min_pass_rate: float = 1.0
    max_safety_regressions: int = 0
    max_new_code_regressions: int = 0
    max_wrong_skill_selections: int = 0
    max_hallucinated_entities: int = 0
    max_ungrounded_answers: int = 0
    max_provider_errors: int = 0
    require_human_approval: bool = True

    def __post_init__(self) -> None:
        if self.min_corpus_size < 1:
            raise ValueError("min_corpus_size must be positive")
        if not 0.0 <= self.min_pass_rate <= 1.0:
            raise ValueError("min_pass_rate must be between 0 and 1")


@dataclass(frozen=True)
class PromotionDecision:
    candidate_id: str
    eligible: bool
    reasons: tuple[str, ...]
    evaluation_id: str | None
    human_approval_required: bool
    approved_by: str | None


@dataclass
class LifecycleRecord:
    candidate: ImprovementCandidate
    state: LifecycleState = LifecycleState.DRAFT
    evaluations: list[EvaluationSnapshot] = field(default_factory=list)
    approved_by: str | None = None
    approval_note: str | None = None
    promoted_ref: str | None = None
    rollback_reason: str | None = None

    @property
    def latest_evaluation(self) -> EvaluationSnapshot | None:
        return self.evaluations[-1] if self.evaluations else None


class ControlledImprovementLifecycle:
    """Deterministic governance around improvement proposals.

    The class owns lifecycle state only.  `mark_promoted` records that an
    external, separately verified deployment happened; it does not perform that
    deployment.  This keeps generation/evaluation distinct from execution.
    """

    def __init__(self, policy: PromotionPolicy | None = None) -> None:
        self.policy = policy or PromotionPolicy()
        self._records: dict[str, LifecycleRecord] = {}

    def register(self, candidate: ImprovementCandidate) -> LifecycleRecord:
        existing = self._records.get(candidate.candidate_id)
        if existing is not None:
            return existing
        record = LifecycleRecord(candidate=candidate)
        self._records[candidate.candidate_id] = record
        return record

    def get(self, candidate_id: str) -> LifecycleRecord | None:
        return self._records.get(candidate_id)

    def record_evaluation(self, snapshot: EvaluationSnapshot) -> LifecycleRecord:
        record = self._require(snapshot.candidate_id)
        if record.state in {LifecycleState.PROMOTED, LifecycleState.ROLLED_BACK}:
            raise ValueError(f"cannot evaluate candidate in state {record.state.value}")
        record.evaluations.append(snapshot)
        record.state = LifecycleState.EVALUATED
        return record

    def decision(self, candidate_id: str) -> PromotionDecision:
        record = self._require(candidate_id)
        evaluation = record.latest_evaluation
        reasons: list[str] = []
        if evaluation is None:
            reasons.append("missing_evaluation")
        else:
            policy = self.policy
            if evaluation.corpus_size < policy.min_corpus_size:
                reasons.append("insufficient_corpus")
            if evaluation.pass_rate < policy.min_pass_rate:
                reasons.append("pass_rate_below_threshold")
            if evaluation.safety_regressions > policy.max_safety_regressions:
                reasons.append("safety_regression")
            if evaluation.new_code_regressions > policy.max_new_code_regressions:
                reasons.append("new_code_regression")
            if evaluation.wrong_skill_selections > policy.max_wrong_skill_selections:
                reasons.append("wrong_skill_selection")
            if evaluation.hallucinated_entities > policy.max_hallucinated_entities:
                reasons.append("hallucinated_entity")
            if evaluation.ungrounded_answers > policy.max_ungrounded_answers:
                reasons.append("ungrounded_answer")
            if evaluation.provider_errors > policy.max_provider_errors:
                reasons.append("provider_error")

        approval_missing = self.policy.require_human_approval and not record.approved_by
        if approval_missing:
            reasons.append("human_approval_required")
        eligible = not reasons
        return PromotionDecision(
            candidate_id=candidate_id,
            eligible=eligible,
            reasons=tuple(reasons),
            evaluation_id=evaluation.evaluation_id if evaluation else None,
            human_approval_required=self.policy.require_human_approval,
            approved_by=record.approved_by,
        )

    def request_approval(self, candidate_id: str) -> LifecycleRecord:
        record = self._require(candidate_id)
        evaluation = record.latest_evaluation
        if evaluation is None:
            raise ValueError("candidate must be evaluated before approval")
        technical = self._technical_reasons(evaluation)
        if technical:
            raise ValueError("candidate has not passed technical promotion gates: " + ", ".join(technical))
        record.state = LifecycleState.APPROVAL_REQUIRED
        return record

    def approve(self, candidate_id: str, *, approver: str, note: str | None = None) -> LifecycleRecord:
        if not approver.strip():
            raise ValueError("approver is required")
        record = self._require(candidate_id)
        if record.state not in {LifecycleState.EVALUATED, LifecycleState.APPROVAL_REQUIRED}:
            raise ValueError(f"candidate cannot be approved from state {record.state.value}")
        evaluation = record.latest_evaluation
        if evaluation is None:
            raise ValueError("candidate must be evaluated before approval")
        technical = self._technical_reasons(evaluation)
        if technical:
            raise ValueError("candidate has not passed technical promotion gates: " + ", ".join(technical))
        record.approved_by = approver.strip()
        record.approval_note = note
        record.state = LifecycleState.APPROVED
        return record

    def reject(self, candidate_id: str, *, reason: str) -> LifecycleRecord:
        if not reason.strip():
            raise ValueError("rejection reason is required")
        record = self._require(candidate_id)
        if record.state in {LifecycleState.PROMOTED, LifecycleState.ROLLED_BACK}:
            raise ValueError(f"candidate cannot be rejected from state {record.state.value}")
        record.state = LifecycleState.REJECTED
        record.approval_note = reason.strip()
        return record

    def mark_promoted(self, candidate_id: str, *, release_ref: str) -> LifecycleRecord:
        if not release_ref.strip():
            raise ValueError("release_ref is required")
        record = self._require(candidate_id)
        decision = self.decision(candidate_id)
        if not decision.eligible:
            raise ValueError("candidate is not eligible for promotion: " + ", ".join(decision.reasons))
        record.state = LifecycleState.PROMOTED
        record.promoted_ref = release_ref.strip()
        return record

    def rollback(self, candidate_id: str, *, reason: str) -> LifecycleRecord:
        if not reason.strip():
            raise ValueError("rollback reason is required")
        record = self._require(candidate_id)
        if record.state is not LifecycleState.PROMOTED:
            raise ValueError("only promoted candidates can be rolled back")
        record.state = LifecycleState.ROLLED_BACK
        record.rollback_reason = reason.strip()
        return record

    def _technical_reasons(self, evaluation: EvaluationSnapshot) -> list[str]:
        policy = self.policy
        reasons: list[str] = []
        if evaluation.corpus_size < policy.min_corpus_size:
            reasons.append("insufficient_corpus")
        if evaluation.pass_rate < policy.min_pass_rate:
            reasons.append("pass_rate_below_threshold")
        if evaluation.safety_regressions > policy.max_safety_regressions:
            reasons.append("safety_regression")
        if evaluation.new_code_regressions > policy.max_new_code_regressions:
            reasons.append("new_code_regression")
        if evaluation.wrong_skill_selections > policy.max_wrong_skill_selections:
            reasons.append("wrong_skill_selection")
        if evaluation.hallucinated_entities > policy.max_hallucinated_entities:
            reasons.append("hallucinated_entity")
        if evaluation.ungrounded_answers > policy.max_ungrounded_answers:
            reasons.append("ungrounded_answer")
        if evaluation.provider_errors > policy.max_provider_errors:
            reasons.append("provider_error")
        return reasons

    def _require(self, candidate_id: str) -> LifecycleRecord:
        record = self._records.get(candidate_id)
        if record is None:
            raise ValueError(f"unknown candidate_id: {candidate_id}")
        return record
