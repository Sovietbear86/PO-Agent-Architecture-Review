"""Controlled AI-PDLC lifecycle for improvement candidates.

The lifecycle deliberately separates offline evaluation, regression gating,
human approval, promotion, and rollback. Nothing in this module mutates the
production router/skill registry automatically.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable

from .improvement_candidates import ImprovementCandidate
from .offline_evaluator import EvaluationReport, GateDecision, OfflineEvaluator, RegressionGate


class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    REJECTED_BY_REGRESSION_GATE = "rejected_by_regression_gate"
    READY_FOR_APPROVAL = "ready_for_approval"
    APPROVED = "approved"
    REJECTED_BY_HUMAN = "rejected_by_human"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class CandidateLifecycleRecord:
    candidate: ImprovementCandidate
    status: LifecycleStatus = LifecycleStatus.DRAFT
    evaluation: EvaluationReport | None = None
    gate: GateDecision | None = None
    approved_by: str | None = None
    approval_reason: str | None = None
    promoted_version: str | None = None
    rollback_reason: str | None = None


class CandidateLifecycle:
    """State machine enforcing evaluate -> gate -> human approval -> promotion."""

    def __init__(self, evaluator: OfflineEvaluator, gate: RegressionGate | None = None) -> None:
        self.evaluator = evaluator
        self.gate = gate or RegressionGate()

    def evaluate(
        self,
        record: CandidateLifecycleRecord,
        cases: Iterable[object],
    ) -> CandidateLifecycleRecord:
        if record.status is not LifecycleStatus.DRAFT:
            raise ValueError("only draft candidates can be evaluated")
        report = self.evaluator.evaluate(record.candidate.candidate_id, record.candidate, cases)
        decision = self.gate.decide(report)
        status = (
            LifecycleStatus.READY_FOR_APPROVAL
            if decision.passed
            else LifecycleStatus.REJECTED_BY_REGRESSION_GATE
        )
        return replace(record, evaluation=report, gate=decision, status=status)

    @staticmethod
    def approve(
        record: CandidateLifecycleRecord,
        *,
        approved_by: str,
        reason: str,
    ) -> CandidateLifecycleRecord:
        if record.status is not LifecycleStatus.READY_FOR_APPROVAL:
            raise ValueError("candidate must pass regression gate before approval")
        if not approved_by.strip() or not reason.strip():
            raise ValueError("approved_by and reason are required")
        return replace(
            record,
            status=LifecycleStatus.APPROVED,
            approved_by=approved_by.strip(),
            approval_reason=reason.strip(),
        )

    @staticmethod
    def reject(
        record: CandidateLifecycleRecord,
        *,
        rejected_by: str,
        reason: str,
    ) -> CandidateLifecycleRecord:
        if record.status is not LifecycleStatus.READY_FOR_APPROVAL:
            raise ValueError("only candidates awaiting approval can be rejected")
        if not rejected_by.strip() or not reason.strip():
            raise ValueError("rejected_by and reason are required")
        return replace(
            record,
            status=LifecycleStatus.REJECTED_BY_HUMAN,
            approved_by=rejected_by.strip(),
            approval_reason=reason.strip(),
        )

    @staticmethod
    def promote(
        record: CandidateLifecycleRecord,
        *,
        version: str,
        promoter: Callable[[ImprovementCandidate, str], None],
    ) -> CandidateLifecycleRecord:
        if record.status is not LifecycleStatus.APPROVED:
            raise ValueError("human approval is required before promotion")
        if record.candidate.proposed_change.get("apply") is not False:
            raise ValueError("candidate proposal must remain non-self-applying")
        promoter(record.candidate, version)
        return replace(record, status=LifecycleStatus.PROMOTED, promoted_version=version)

    @staticmethod
    def rollback(
        record: CandidateLifecycleRecord,
        *,
        reason: str,
        rollback: Callable[[ImprovementCandidate, str | None], None],
    ) -> CandidateLifecycleRecord:
        if record.status is not LifecycleStatus.PROMOTED:
            raise ValueError("only promoted candidates can be rolled back")
        if not reason.strip():
            raise ValueError("rollback reason is required")
        rollback(record.candidate, record.promoted_version)
        return replace(
            record,
            status=LifecycleStatus.ROLLED_BACK,
            rollback_reason=reason.strip(),
        )
