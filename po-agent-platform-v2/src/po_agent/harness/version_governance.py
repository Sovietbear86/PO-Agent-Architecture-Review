"""Human approval, promotion and rollback governance for Harness improvements.

This module never edits source code. It controls which already-versioned runtime
artifact may become active after offline evaluation and explicit human approval.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .offline_evaluator import GateDecision


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str
    candidate_id: str
    approver: str
    approved: bool
    timestamp: str
    comment: str | None = None


@dataclass(frozen=True)
class VersionArtifact:
    component: str
    version: str
    candidate_id: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PromotionRecord:
    promotion_id: str
    candidate_id: str
    component: str
    from_version: str
    to_version: str
    approval_id: str
    timestamp: str
    status: str = "promoted"


@dataclass(frozen=True)
class RollbackRecord:
    rollback_id: str
    component: str
    from_version: str
    to_version: str
    reason: str
    actor: str
    timestamp: str


class ApprovalStore:
    def __init__(self) -> None:
        self._records: dict[str, ApprovalRecord] = {}

    def record(self, candidate_id: str, *, approver: str, approved: bool, comment: str | None = None) -> ApprovalRecord:
        if not approver.strip():
            raise ValueError("approver is required")
        record = ApprovalRecord(
            approval_id=str(uuid.uuid4()),
            candidate_id=candidate_id,
            approver=approver.strip(),
            approved=approved,
            timestamp=datetime.now(timezone.utc).isoformat(),
            comment=comment,
        )
        self._records[record.approval_id] = record
        return record

    def get(self, approval_id: str) -> ApprovalRecord | None:
        return self._records.get(approval_id)


class VersionRegistry:
    """Tracks active versions and immutable promotion history."""

    def __init__(self, initial: dict[str, str] | None = None) -> None:
        self._active = dict(initial or {})
        self._promotion_history: list[PromotionRecord] = []
        self._rollback_history: list[RollbackRecord] = []

    def active(self, component: str) -> str | None:
        return self._active.get(component)

    def promote(
        self,
        artifact: VersionArtifact,
        *,
        gate: GateDecision,
        approval: ApprovalRecord,
    ) -> PromotionRecord:
        if gate.candidate_id != artifact.candidate_id or approval.candidate_id != artifact.candidate_id:
            raise ValueError("candidate identity mismatch")
        if not gate.passed or gate.status != "ready_for_approval":
            raise ValueError("candidate did not pass regression gate")
        if not approval.approved:
            raise ValueError("explicit human approval is required")

        previous = self._active.get(artifact.component)
        if previous is None:
            raise ValueError(f"no active baseline for component: {artifact.component}")
        if previous == artifact.version:
            raise ValueError("target version is already active")

        record = PromotionRecord(
            promotion_id=str(uuid.uuid4()),
            candidate_id=artifact.candidate_id,
            component=artifact.component,
            from_version=previous,
            to_version=artifact.version,
            approval_id=approval.approval_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._active[artifact.component] = artifact.version
        self._promotion_history.append(record)
        return record

    def rollback(self, promotion_id: str, *, actor: str, reason: str) -> RollbackRecord:
        if not actor.strip() or not reason.strip():
            raise ValueError("actor and reason are required")
        promotion = next((p for p in self._promotion_history if p.promotion_id == promotion_id), None)
        if promotion is None:
            raise ValueError(f"unknown promotion_id: {promotion_id}")
        current = self._active.get(promotion.component)
        if current != promotion.to_version:
            raise ValueError("promotion is no longer the active version and cannot be directly rolled back")

        record = RollbackRecord(
            rollback_id=str(uuid.uuid4()),
            component=promotion.component,
            from_version=promotion.to_version,
            to_version=promotion.from_version,
            reason=reason.strip(),
            actor=actor.strip(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self._active[promotion.component] = promotion.from_version
        self._rollback_history.append(record)
        return record

    @property
    def promotion_history(self) -> tuple[PromotionRecord, ...]:
        return tuple(self._promotion_history)

    @property
    def rollback_history(self) -> tuple[RollbackRecord, ...]:
        return tuple(self._rollback_history)
