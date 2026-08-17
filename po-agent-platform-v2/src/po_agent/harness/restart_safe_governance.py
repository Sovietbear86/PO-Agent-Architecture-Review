"""Restart-safe persistence for governed promotion and rollback state.

The core governance service deliberately keeps hot state in memory.  This module
adds a durable SQLite projection for the security-sensitive parts of that state:
issued approvals, consumed approval ids, promotion manifests and rollback
records.  A fresh service instance can therefore fail closed after process
restart instead of forgetting that an approval was consumed or that a release
was already promoted/rolled back.

The durable projection is not an autonomous authority: promotion and rollback
still flow exclusively through :class:`GovernedPromotionService` and retain all
human-approval and lifecycle checks.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from typing import Iterable

from .governed_promotion import (
    GovernedPromotionService,
    GovernedRollbackRecord,
    PromotionBinding,
    PromotionManifest,
    SignedPromotionApproval,
)
from .promotion_registry import HumanApprovalRecord, PromotionRecord, ReleaseState, RollbackRecord


def _binding(payload: dict[str, str]) -> PromotionBinding:
    return PromotionBinding(
        baseline_sha=str(payload["baseline_sha"]),
        candidate_id=str(payload["candidate_id"]),
        candidate_fingerprint=str(payload["candidate_fingerprint"]),
        evaluation_id=str(payload["evaluation_id"]),
    )


class SQLiteGovernanceStateStore:
    """Durable restart state for governed promotion.

    Rows are inserted once and never updated.  Duplicate identifiers are rejected
    by SQLite primary-key constraints, which also gives replay protection across
    concurrent/restarted processes sharing the same database.
    """

    def __init__(self, db_path: str) -> None:
        if not str(db_path).strip():
            raise ValueError("db_path is required")
        self._conn = sqlite3.connect(db_path, timeout=30.0)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS governance_approvals ("
            "approval_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS governance_consumed_approvals ("
            "approval_id TEXT PRIMARY KEY)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS governance_manifests ("
            "promotion_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_manifest_approval "
            "ON governance_manifests(approval_id)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS governance_rollbacks ("
            "rollback_id TEXT PRIMARY KEY, promotion_id TEXT NOT NULL, payload_json TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_governance_rollback_promotion "
            "ON governance_rollbacks(promotion_id)"
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def record_approval(self, approval: SignedPromotionApproval) -> None:
        payload = {
            "approval_id": approval.approval_id,
            "binding": approval.binding.canonical_payload(),
            "approved_by": approval.approved_by,
            "approved_at": approval.approved_at,
            "signature": approval.signature,
            "note": approval.note,
        }
        self._insert_once(
            "INSERT INTO governance_approvals(approval_id, payload_json) VALUES (?, ?)",
            (approval.approval_id, json.dumps(payload, sort_keys=True, separators=(",", ":"))),
            duplicate=f"approval already persisted: {approval.approval_id}",
        )

    def record_promotion(self, manifest: PromotionManifest) -> None:
        payload = {
            "promotion_id": manifest.promotion_id,
            "approval_id": manifest.approval_id,
            "binding": manifest.binding.canonical_payload(),
            "release_ref": manifest.release_ref,
            "promoted_at": manifest.promoted_at,
        }
        try:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "INSERT INTO governance_consumed_approvals(approval_id) VALUES (?)",
                (manifest.approval_id,),
            )
            self._conn.execute(
                "INSERT INTO governance_manifests(promotion_id, approval_id, payload_json) VALUES (?, ?, ?)",
                (
                    manifest.promotion_id,
                    manifest.approval_id,
                    json.dumps(payload, sort_keys=True, separators=(",", ":")),
                ),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            self._conn.rollback()
            raise ValueError("approval or promotion has already been persisted") from exc
        except Exception:
            self._conn.rollback()
            raise

    def record_rollback(self, record: GovernedRollbackRecord) -> None:
        self._insert_once(
            "INSERT INTO governance_rollbacks(rollback_id, promotion_id, payload_json) VALUES (?, ?, ?)",
            (
                record.rollback_id,
                record.promotion_id,
                json.dumps(asdict(record), sort_keys=True, separators=(",", ":")),
            ),
            duplicate=f"promotion already has a durable rollback: {record.promotion_id}",
        )

    def approvals(self) -> tuple[SignedPromotionApproval, ...]:
        rows = self._conn.execute(
            "SELECT payload_json FROM governance_approvals ORDER BY approval_id"
        ).fetchall()
        result: list[SignedPromotionApproval] = []
        for (raw,) in rows:
            payload = json.loads(str(raw))
            result.append(
                SignedPromotionApproval(
                    approval_id=str(payload["approval_id"]),
                    binding=_binding(payload["binding"]),
                    approved_by=str(payload["approved_by"]),
                    approved_at=str(payload["approved_at"]),
                    signature=str(payload["signature"]),
                    note=payload.get("note"),
                )
            )
        return tuple(result)

    def consumed_approval_ids(self) -> frozenset[str]:
        rows = self._conn.execute(
            "SELECT approval_id FROM governance_consumed_approvals ORDER BY approval_id"
        ).fetchall()
        return frozenset(str(row[0]) for row in rows)

    def manifests(self) -> tuple[PromotionManifest, ...]:
        rows = self._conn.execute(
            "SELECT payload_json FROM governance_manifests ORDER BY promotion_id"
        ).fetchall()
        result: list[PromotionManifest] = []
        for (raw,) in rows:
            payload = json.loads(str(raw))
            result.append(
                PromotionManifest(
                    promotion_id=str(payload["promotion_id"]),
                    approval_id=str(payload["approval_id"]),
                    binding=_binding(payload["binding"]),
                    release_ref=str(payload["release_ref"]),
                    promoted_at=str(payload["promoted_at"]),
                )
            )
        return tuple(result)

    def rollbacks(self) -> tuple[GovernedRollbackRecord, ...]:
        rows = self._conn.execute(
            "SELECT payload_json FROM governance_rollbacks ORDER BY rollback_id"
        ).fetchall()
        result: list[GovernedRollbackRecord] = []
        for (raw,) in rows:
            payload = json.loads(str(raw))
            result.append(GovernedRollbackRecord(**payload))
        return tuple(result)

    def _insert_once(
        self,
        sql: str,
        params: Iterable[object],
        *,
        duplicate: str,
    ) -> None:
        try:
            self._conn.execute(sql, tuple(params))
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            self._conn.rollback()
            raise ValueError(duplicate) from exc


class RestartSafeGovernedPromotionService(GovernedPromotionService):
    """GovernedPromotionService with durable restart/replay protection.

    In-flight lifecycle/orchestrator sessions intentionally remain ephemeral.  A
    restart therefore resumes only committed governance facts and fails closed
    for unfinished work.  This prevents a restart from inventing approval or
    deployment authority.
    """

    def __init__(self, *, state_store: SQLiteGovernanceStateStore, **kwargs) -> None:
        if state_store is None:
            raise ValueError("state_store is required for restart-safe governance")
        super().__init__(**kwargs)
        self._state_store = state_store
        self._rehydrate()

    def _rehydrate(self) -> None:
        approvals = self._state_store.approvals()
        manifests = self._state_store.manifests()
        rollbacks = self._state_store.rollbacks()

        self._approvals.update({approval.approval_id: approval for approval in approvals})
        self._consumed_approvals.update(self._state_store.consumed_approval_ids())
        self._manifests.update({manifest.promotion_id: manifest for manifest in manifests})
        self._rollbacks.update({record.rollback_id: record for record in rollbacks})

        # The legacy VersionedPromotionRegistry is still used by the governed
        # service during rollback. Rebuild its append-only in-memory projection
        # from durable facts so rollback remains valid after process restart.
        for approval in approvals:
            self._registry._approvals.setdefault(
                approval.approval_id,
                HumanApprovalRecord(
                    approval_id=approval.approval_id,
                    candidate_id=approval.binding.candidate_id,
                    evaluation_id=approval.binding.evaluation_id,
                    approver=approval.approved_by,
                    approved_at=approval.approved_at,
                    note=approval.note,
                ),
            )
        for manifest in manifests:
            self._registry._promotions.setdefault(
                manifest.promotion_id,
                PromotionRecord(
                    promotion_id=manifest.promotion_id,
                    candidate_id=manifest.binding.candidate_id,
                    approval_id=manifest.approval_id,
                    evaluation_id=manifest.binding.evaluation_id,
                    release_ref=manifest.release_ref,
                    baseline_sha=manifest.binding.baseline_sha,
                    candidate_tree_sha256=manifest.binding.candidate_fingerprint,
                    promoted_at=manifest.promoted_at,
                    state=ReleaseState.PROMOTED,
                ),
            )
        for record in rollbacks:
            self._registry._rollbacks.setdefault(
                record.rollback_id,
                RollbackRecord(
                    rollback_id=record.rollback_id,
                    promotion_id=record.promotion_id,
                    candidate_id=record.candidate_id,
                    release_ref=record.from_release_ref,
                    reason=record.reason,
                    rolled_back_by=record.rolled_back_by,
                    rolled_back_at=record.rolled_back_at,
                ),
            )

    def issue_human_approval(self, **kwargs) -> SignedPromotionApproval:
        approval = super().issue_human_approval(**kwargs)
        self._state_store.record_approval(approval)
        return approval

    def promote(self, **kwargs) -> PromotionManifest:
        approval = kwargs.get("approval")
        if isinstance(approval, SignedPromotionApproval):
            if approval.approval_id in self._state_store.consumed_approval_ids():
                raise ValueError("approval has already been consumed")
        manifest = super().promote(**kwargs)
        self._state_store.record_promotion(manifest)
        return manifest

    def rollback(self, **kwargs) -> GovernedRollbackRecord:
        promotion_id = str(kwargs.get("promotion_id", ""))
        if promotion_id and any(
            record.promotion_id == promotion_id for record in self._state_store.rollbacks()
        ):
            raise ValueError("promotion has already been rolled back")
        record = super().rollback(**kwargs)
        self._state_store.record_rollback(record)
        return record
