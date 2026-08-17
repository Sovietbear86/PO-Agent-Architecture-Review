"""Append-only registry for explicitly approved Harness promotions and rollbacks.

The registry records governance facts only. It never edits source, invokes git,
performs deployment, grants approval, or promotes a candidate autonomously.
Promotion is accepted only when linked to an explicit human approval record.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum


class ReleaseState(str, Enum):
    PROMOTED = "promoted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class HumanApprovalRecord:
    approval_id: str
    candidate_id: str
    evaluation_id: str
    approver: str
    approved_at: str
    note: str | None = None

    @classmethod
    def create(cls, *, candidate_id: str, evaluation_id: str, approver: str, note: str | None = None) -> "HumanApprovalRecord":
        if not candidate_id.strip() or not evaluation_id.strip() or not approver.strip():
            raise ValueError("candidate_id, evaluation_id and approver are required")
        return cls(
            approval_id=str(uuid.uuid4()),
            candidate_id=candidate_id.strip(),
            evaluation_id=evaluation_id.strip(),
            approver=approver.strip(),
            approved_at=datetime.now(timezone.utc).isoformat(),
            note=note,
        )


@dataclass(frozen=True)
class PromotionRecord:
    promotion_id: str
    candidate_id: str
    approval_id: str
    evaluation_id: str
    release_ref: str
    baseline_sha: str
    candidate_tree_sha256: str
    promoted_at: str
    state: ReleaseState = ReleaseState.PROMOTED


@dataclass(frozen=True)
class RollbackRecord:
    rollback_id: str
    promotion_id: str
    candidate_id: str
    release_ref: str
    reason: str
    rolled_back_by: str
    rolled_back_at: str


class VersionedPromotionRegistry:
    """In-memory append-only governance registry."""

    def __init__(self) -> None:
        self._approvals: dict[str, HumanApprovalRecord] = {}
        self._promotions: dict[str, PromotionRecord] = {}
        self._rollbacks: dict[str, RollbackRecord] = {}

    def record_approval(self, record: HumanApprovalRecord) -> HumanApprovalRecord:
        if record.approval_id in self._approvals:
            raise ValueError("approval already recorded")
        self._approvals[record.approval_id] = record
        return record

    def record_promotion(
        self,
        *,
        approval_id: str,
        release_ref: str,
        baseline_sha: str,
        candidate_tree_sha256: str,
    ) -> PromotionRecord:
        approval = self._approvals.get(approval_id)
        if approval is None:
            raise ValueError("promotion requires a recorded human approval")
        if not release_ref.strip() or not baseline_sha.strip() or not candidate_tree_sha256.strip():
            raise ValueError("release_ref, baseline_sha and candidate_tree_sha256 are required")
        if any(item.approval_id == approval_id for item in self._promotions.values()):
            raise ValueError("approval has already been consumed by a promotion")
        record = PromotionRecord(
            promotion_id=str(uuid.uuid4()),
            candidate_id=approval.candidate_id,
            approval_id=approval.approval_id,
            evaluation_id=approval.evaluation_id,
            release_ref=release_ref.strip(),
            baseline_sha=baseline_sha.strip(),
            candidate_tree_sha256=candidate_tree_sha256.strip(),
            promoted_at=datetime.now(timezone.utc).isoformat(),
        )
        self._promotions[record.promotion_id] = record
        return record

    def record_rollback(self, *, promotion_id: str, reason: str, rolled_back_by: str) -> RollbackRecord:
        promotion = self._promotions.get(promotion_id)
        if promotion is None:
            raise ValueError("unknown promotion_id")
        if not reason.strip() or not rolled_back_by.strip():
            raise ValueError("rollback reason and actor are required")
        if any(item.promotion_id == promotion_id for item in self._rollbacks.values()):
            raise ValueError("promotion already rolled back")
        record = RollbackRecord(
            rollback_id=str(uuid.uuid4()),
            promotion_id=promotion.promotion_id,
            candidate_id=promotion.candidate_id,
            release_ref=promotion.release_ref,
            reason=reason.strip(),
            rolled_back_by=rolled_back_by.strip(),
            rolled_back_at=datetime.now(timezone.utc).isoformat(),
        )
        self._rollbacks[record.rollback_id] = record
        return record

    def approval(self, approval_id: str) -> HumanApprovalRecord | None:
        return self._approvals.get(approval_id)

    def promotion(self, promotion_id: str) -> PromotionRecord | None:
        return self._promotions.get(promotion_id)

    def rollback_for(self, promotion_id: str) -> RollbackRecord | None:
        return next((item for item in self._rollbacks.values() if item.promotion_id == promotion_id), None)

    def candidate_history(self, candidate_id: str) -> tuple[object, ...]:
        rows: list[object] = []
        rows.extend(item for item in self._approvals.values() if item.candidate_id == candidate_id)
        rows.extend(item for item in self._promotions.values() if item.candidate_id == candidate_id)
        rows.extend(item for item in self._rollbacks.values() if item.candidate_id == candidate_id)
        return tuple(sorted(rows, key=lambda item: getattr(item, "approved_at", getattr(item, "promoted_at", getattr(item, "rolled_back_at", "")))))


class SQLitePromotionAuditStore:
    """Durable append-only event store; update/delete APIs intentionally absent."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS harness_promotion_events (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, candidate_id TEXT NOT NULL, created_at TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_promotion_candidate ON harness_promotion_events(candidate_id)")
        self._conn.commit()

    def append(self, record: HumanApprovalRecord | PromotionRecord | RollbackRecord) -> None:
        if isinstance(record, HumanApprovalRecord):
            event_id, event_type, candidate_id, created_at = record.approval_id, "approval", record.candidate_id, record.approved_at
        elif isinstance(record, PromotionRecord):
            event_id, event_type, candidate_id, created_at = record.promotion_id, "promotion", record.candidate_id, record.promoted_at
        elif isinstance(record, RollbackRecord):
            event_id, event_type, candidate_id, created_at = record.rollback_id, "rollback", record.candidate_id, record.rolled_back_at
        else:
            raise TypeError("unsupported promotion event")
        payload = json.dumps(asdict(record), ensure_ascii=False, sort_keys=True, default=lambda value: value.value if isinstance(value, Enum) else str(value))
        try:
            self._conn.execute("INSERT INTO harness_promotion_events VALUES (?, ?, ?, ?, ?)", (event_id, event_type, candidate_id, created_at, payload))
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"promotion event already exists: {event_id}") from exc

    def events_for_candidate(self, candidate_id: str) -> tuple[dict[str, object], ...]:
        rows = self._conn.execute(
            "SELECT event_type, payload_json FROM harness_promotion_events WHERE candidate_id = ? ORDER BY created_at ASC",
            (candidate_id,),
        ).fetchall()
        return tuple({"event_type": str(kind), "payload": json.loads(str(payload))} for kind, payload in rows)
