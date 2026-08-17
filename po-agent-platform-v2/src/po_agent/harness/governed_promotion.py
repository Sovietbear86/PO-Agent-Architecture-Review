"""Governed, human-gated promotion and rollback for Harness evolution.

This module is the production governance boundary after shadow evaluation.  It
never generates candidates, runs the sandbox, edits source, invokes git, or
autonomously grants approval.  A promotion requires a signed human approval
bound to the exact baseline, candidate fingerprint, and evaluation.  Approvals
are single-use and every governance transition is appended to an immutable audit
log.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from .evolution_lifecycle import ControlledImprovementLifecycle, LifecycleState
from .promotion_registry import VersionedPromotionRegistry


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required(value: str, name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _canonical(payload: dict[str, object]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


class GovernanceEventType(str, Enum):
    APPROVAL_ISSUED = "approval_issued"
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class PromotionBinding:
    """Identity of exactly one evaluated candidate release."""

    baseline_sha: str
    candidate_id: str
    candidate_fingerprint: str
    evaluation_id: str

    def __post_init__(self) -> None:
        for field_name in ("baseline_sha", "candidate_id", "candidate_fingerprint", "evaluation_id"):
            if not str(getattr(self, field_name)).strip():
                raise ValueError(f"{field_name} is required")

    def canonical_payload(self) -> dict[str, str]:
        return {
            "baseline_sha": self.baseline_sha,
            "candidate_id": self.candidate_id,
            "candidate_fingerprint": self.candidate_fingerprint,
            "evaluation_id": self.evaluation_id,
        }


@dataclass(frozen=True)
class SignedPromotionApproval:
    approval_id: str
    binding: PromotionBinding
    approved_by: str
    approved_at: str
    signature: str
    note: str | None = None

    def signing_payload(self) -> dict[str, object]:
        return {
            "approval_id": self.approval_id,
            "binding": self.binding.canonical_payload(),
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "note": self.note,
        }


@dataclass(frozen=True)
class PromotionManifest:
    promotion_id: str
    approval_id: str
    binding: PromotionBinding
    release_ref: str
    promoted_at: str


@dataclass(frozen=True)
class GovernedRollbackRecord:
    rollback_id: str
    promotion_id: str
    candidate_id: str
    from_release_ref: str
    target_promotion_id: str
    target_release_ref: str
    reason: str
    rolled_back_by: str
    rolled_back_at: str


@dataclass(frozen=True)
class GovernanceAuditEvent:
    event_id: str
    event_type: GovernanceEventType
    candidate_id: str
    created_at: str
    payload_json: str


class ApprovalSigner:
    """HMAC signer/verifier owned by the trusted governance boundary."""

    __slots__ = ("__key",)

    def __init__(self, key: bytes) -> None:
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("governance signing key must contain at least 32 bytes")
        self.__key = key

    def sign(self, payload: dict[str, object]) -> str:
        return hmac.new(self.__key, _canonical(payload), hashlib.sha256).hexdigest()

    def verify(self, payload: dict[str, object], signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)

    def __getstate__(self):
        raise TypeError("ApprovalSigner cannot be pickled")

    def __copy__(self):
        raise TypeError("ApprovalSigner cannot be copied")

    def __deepcopy__(self, memo):
        raise TypeError("ApprovalSigner cannot be deep-copied")


class SQLiteGovernanceAuditStore:
    """Append-only durable audit store.  Update/delete APIs intentionally absent."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS governed_promotion_events ("
            "event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, candidate_id TEXT NOT NULL, "
            "created_at TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_governance_candidate ON governed_promotion_events(candidate_id, created_at)"
        )
        self._conn.commit()

    def append(self, event: GovernanceAuditEvent) -> None:
        try:
            self._conn.execute(
                "INSERT INTO governed_promotion_events VALUES (?, ?, ?, ?, ?)",
                (event.event_id, event.event_type.value, event.candidate_id, event.created_at, event.payload_json),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"governance event already exists: {event.event_id}") from exc

    def events_for_candidate(self, candidate_id: str) -> tuple[GovernanceAuditEvent, ...]:
        rows = self._conn.execute(
            "SELECT event_id, event_type, candidate_id, created_at, payload_json "
            "FROM governed_promotion_events WHERE candidate_id = ? ORDER BY created_at ASC, event_id ASC",
            (candidate_id,),
        ).fetchall()
        return tuple(
            GovernanceAuditEvent(
                event_id=str(event_id),
                event_type=GovernanceEventType(str(event_type)),
                candidate_id=str(row_candidate_id),
                created_at=str(created_at),
                payload_json=str(payload_json),
            )
            for event_id, event_type, row_candidate_id, created_at, payload_json in rows
        )


class GovernedPromotionService:
    """Single production-facing promotion/rollback governance path.

    The service records governance facts only.  Release mutation/deployment is
    deliberately delegated to an injected, trusted release applier.  When no
    applier is supplied the service remains a pure governance recorder.
    """

    def __init__(
        self,
        *,
        lifecycle: ControlledImprovementLifecycle,
        registry: VersionedPromotionRegistry,
        signer: ApprovalSigner,
        audit_store: SQLiteGovernanceAuditStore | None = None,
        release_applier: Callable[[PromotionManifest], None] | None = None,
        rollback_applier: Callable[[GovernedRollbackRecord], None] | None = None,
    ) -> None:
        self._lifecycle = lifecycle
        self._registry = registry
        self._signer = signer
        self._audit = audit_store or SQLiteGovernanceAuditStore()
        self._release_applier = release_applier
        self._rollback_applier = rollback_applier
        self._approvals: dict[str, SignedPromotionApproval] = {}
        self._consumed_approvals: set[str] = set()
        self._manifests: dict[str, PromotionManifest] = {}
        self._rollbacks: dict[str, GovernedRollbackRecord] = {}

    def issue_human_approval(
        self,
        *,
        binding: PromotionBinding,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval:
        """Create an explicit signed approval for the current APPROVAL_REQUIRED state."""
        approver = _required(approved_by, "approved_by")
        record = self._require_exact_evaluated_binding(binding, require_approval_state=True)
        approval_id = str(uuid.uuid4())
        approved_at = _now()
        unsigned = SignedPromotionApproval(
            approval_id=approval_id,
            binding=binding,
            approved_by=approver,
            approved_at=approved_at,
            note=note,
            signature="",
        )
        approval = SignedPromotionApproval(
            approval_id=approval_id,
            binding=binding,
            approved_by=approver,
            approved_at=approved_at,
            note=note,
            signature=self._signer.sign(unsigned.signing_payload()),
        )
        # Keep lifecycle human-approval state aligned, but do not promote here.
        self._lifecycle.approve(record.candidate.candidate_id, approver=approver, note=note)
        self._approvals[approval.approval_id] = approval
        self._append_audit(
            GovernanceEventType.APPROVAL_ISSUED,
            approval.approval_id,
            binding.candidate_id,
            approval.approved_at,
            {
                "approval_id": approval.approval_id,
                "binding": approval.binding.canonical_payload(),
                "approved_by": approval.approved_by,
                "approved_at": approval.approved_at,
                "note": approval.note,
                "signature_sha256": hashlib.sha256(approval.signature.encode("ascii")).hexdigest(),
            },
        )
        return approval

    def promote(
        self,
        *,
        approval: SignedPromotionApproval,
        expected_binding: PromotionBinding,
        release_ref: str,
    ) -> PromotionManifest:
        release_ref = _required(release_ref, "release_ref")
        stored = self._approvals.get(approval.approval_id)
        if stored is None or stored != approval:
            raise ValueError("approval is unknown or does not match the trusted recorded approval")
        if approval.approval_id in self._consumed_approvals:
            raise ValueError("approval has already been consumed")
        if approval.binding != expected_binding:
            raise ValueError("approval binding does not match requested promotion")
        if not self._signer.verify(approval.signing_payload(), approval.signature):
            raise ValueError("approval signature verification failed")
        lifecycle_record = self._require_exact_evaluated_binding(expected_binding, require_approval_state=False)
        if lifecycle_record.state is not LifecycleState.APPROVED:
            raise ValueError(f"candidate must be human-approved before promotion, got {lifecycle_record.state.value}")
        decision = self._lifecycle.decision(expected_binding.candidate_id)
        if not decision.eligible or decision.evaluation_id != expected_binding.evaluation_id:
            raise ValueError("current lifecycle decision is not eligible for the approved evaluation")

        # Reuse the append-only versioned registry.  Its approval record is an
        # audit-compatible projection of the stronger signed approval.
        from .promotion_registry import HumanApprovalRecord

        registry_approval = HumanApprovalRecord(
            approval_id=approval.approval_id,
            candidate_id=expected_binding.candidate_id,
            evaluation_id=expected_binding.evaluation_id,
            approver=approval.approved_by,
            approved_at=approval.approved_at,
            note=approval.note,
        )
        if self._registry.approval(approval.approval_id) is None:
            self._registry.record_approval(registry_approval)
        registry_promotion = self._registry.record_promotion(
            approval_id=approval.approval_id,
            release_ref=release_ref,
            baseline_sha=expected_binding.baseline_sha,
            candidate_tree_sha256=expected_binding.candidate_fingerprint,
        )
        manifest = PromotionManifest(
            promotion_id=registry_promotion.promotion_id,
            approval_id=approval.approval_id,
            binding=expected_binding,
            release_ref=release_ref,
            promoted_at=registry_promotion.promoted_at,
        )

        # Apply first; only successful application becomes consumed/promoted.
        if self._release_applier is not None:
            self._release_applier(manifest)
        self._consumed_approvals.add(approval.approval_id)
        self._manifests[manifest.promotion_id] = manifest
        self._lifecycle.mark_promoted(expected_binding.candidate_id, release_ref=release_ref)
        self._append_audit(
            GovernanceEventType.PROMOTED,
            manifest.promotion_id,
            expected_binding.candidate_id,
            manifest.promoted_at,
            {
                "promotion_id": manifest.promotion_id,
                "approval_id": manifest.approval_id,
                "binding": manifest.binding.canonical_payload(),
                "release_ref": manifest.release_ref,
                "promoted_at": manifest.promoted_at,
            },
        )
        return manifest

    def rollback(
        self,
        *,
        promotion_id: str,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord:
        promotion_id = _required(promotion_id, "promotion_id")
        target_promotion_id = _required(target_promotion_id, "target_promotion_id")
        reason = _required(reason, "reason")
        actor = _required(rolled_back_by, "rolled_back_by")
        current = self._manifests.get(promotion_id)
        target = self._manifests.get(target_promotion_id)
        if current is None:
            raise ValueError("rollback requires a known governed promotion")
        if target is None:
            raise ValueError("rollback target must be a known governed promotion")
        if current.candidate_id if hasattr(current, "candidate_id") else current.binding.candidate_id:
            pass
        if promotion_id == target_promotion_id:
            raise ValueError("rollback target must differ from current promotion")
        if any(item.promotion_id == promotion_id for item in self._rollbacks.values()):
            raise ValueError("promotion has already been rolled back")
        # Target must predate current promotion; this prevents rolling forward
        # under the guise of rollback and makes the target a known-good release.
        if target.promoted_at >= current.promoted_at:
            raise ValueError("rollback target must be an earlier known-good promotion")

        record = GovernedRollbackRecord(
            rollback_id=str(uuid.uuid4()),
            promotion_id=current.promotion_id,
            candidate_id=current.binding.candidate_id,
            from_release_ref=current.release_ref,
            target_promotion_id=target.promotion_id,
            target_release_ref=target.release_ref,
            reason=reason,
            rolled_back_by=actor,
            rolled_back_at=_now(),
        )
        if self._rollback_applier is not None:
            self._rollback_applier(record)
        self._registry.record_rollback(promotion_id=current.promotion_id, reason=reason, rolled_back_by=actor)
        self._rollbacks[record.rollback_id] = record
        lifecycle_record = self._lifecycle.get(current.binding.candidate_id)
        if lifecycle_record is not None and lifecycle_record.state is LifecycleState.PROMOTED:
            self._lifecycle.rollback(current.binding.candidate_id, reason=reason)
        self._append_audit(
            GovernanceEventType.ROLLED_BACK,
            record.rollback_id,
            record.candidate_id,
            record.rolled_back_at,
            asdict(record),
        )
        return record

    def manifest(self, promotion_id: str) -> PromotionManifest | None:
        return self._manifests.get(promotion_id)

    def audit_events(self, candidate_id: str) -> tuple[GovernanceAuditEvent, ...]:
        return self._audit.events_for_candidate(candidate_id)

    def _require_exact_evaluated_binding(self, binding: PromotionBinding, *, require_approval_state: bool):
        record = self._lifecycle.get(binding.candidate_id)
        if record is None:
            raise ValueError("unknown candidate_id")
        evaluation = record.latest_evaluation
        if evaluation is None or evaluation.evaluation_id != binding.evaluation_id:
            raise ValueError("evaluation_id does not match current candidate evaluation")
        if require_approval_state and record.state is not LifecycleState.APPROVAL_REQUIRED:
            raise ValueError("candidate must be in APPROVAL_REQUIRED state")
        return record

    def _append_audit(
        self,
        event_type: GovernanceEventType,
        event_id: str,
        candidate_id: str,
        created_at: str,
        payload: dict[str, object],
    ) -> None:
        self._audit.append(
            GovernanceAuditEvent(
                event_id=event_id,
                event_type=event_type,
                candidate_id=candidate_id,
                created_at=created_at,
                payload_json=json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str),
            )
        )
