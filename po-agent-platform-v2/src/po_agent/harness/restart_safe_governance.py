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
    """GovernedPromotionService with durable restart/replay protection."""

    def __init__(self, *, state_store: SQLiteGovernanceStateStore, **kwargs) -> None:
        if state_store is None:
            raise ValueError("state_store is required for restart-safe governance")
        super().__init__(**kwargs)
        self._state_store = state_store
        self._rehydrate()

    def _rehydrate(self) -> None:
        self._approvals.update(
            {approval.approval_id: approval for approval in self._state_store.approvals()}
        )
        self._consumed_approvals.update(self._state_store.consumed_approval_ids())
        self._manifests.update(
            {manifest.promotion_id: manifest for manifest in self._state_store.manifests()}
        )
        self._rollbacks.update(
            {record.rollback_id: record for record in self._state_store.rollbacks()}
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
