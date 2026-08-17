from __future__ import annotations

from pathlib import Path

import pytest

from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, EvaluationSnapshot
from po_agent.harness.governed_promotion import ApprovalSigner, PromotionBinding
from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.promotion_registry import VersionedPromotionRegistry
from po_agent.harness.restart_safe_governance import (
    RestartSafeGovernedPromotionService,
    SQLiteGovernanceStateStore,
)


KEY = b"r" * 32


def _candidate(candidate_id: str) -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id=candidate_id,
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title=f"Candidate {candidate_id}",
        rationale="restart-safe governance verification",
        source_failure_key=f"failure:{candidate_id}",
        source_eval_ids=("source-eval",),
        proposed_change={"action": "review", "apply": False},
    )


def _prepare(lifecycle: ControlledImprovementLifecycle, candidate_id: str) -> PromotionBinding:
    lifecycle.register(_candidate(candidate_id))
    snapshot = EvaluationSnapshot.create(candidate_id=candidate_id, corpus_size=8, passed=8, failed=0)
    lifecycle.record_evaluation(snapshot)
    lifecycle.request_approval(candidate_id)
    return PromotionBinding(
        baseline_sha=f"baseline-{candidate_id}",
        candidate_id=candidate_id,
        candidate_fingerprint=f"fingerprint-{candidate_id}",
        evaluation_id=snapshot.evaluation_id,
    )


def _service(db_path: Path, lifecycle: ControlledImprovementLifecycle | None = None):
    lifecycle = lifecycle or ControlledImprovementLifecycle()
    store = SQLiteGovernanceStateStore(str(db_path))
    service = RestartSafeGovernedPromotionService(
        lifecycle=lifecycle,
        registry=VersionedPromotionRegistry(),
        signer=ApprovalSigner(KEY),
        state_store=store,
    )
    return lifecycle, store, service


def _promote(service, lifecycle, candidate_id: str, release_ref: str):
    binding = _prepare(lifecycle, candidate_id)
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")
    manifest = service.promote(
        approval=approval,
        expected_binding=binding,
        release_ref=release_ref,
    )
    return binding, approval, manifest


def test_consumed_approval_remains_blocked_after_restart(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle1, store1, service1 = _service(db)
    binding, approval, manifest = _promote(service1, lifecycle1, "cand-1", "release:1")
    store1.close()

    _, store2, service2 = _service(db)
    assert service2.manifest(manifest.promotion_id) == manifest
    with pytest.raises(ValueError, match="already been consumed"):
        service2.promote(
            approval=approval,
            expected_binding=binding,
            release_ref="release:replay",
        )
    store2.close()


def test_promotion_manifests_are_rehydrated_after_restart(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle1, store1, service1 = _service(db)
    _, _, first = _promote(service1, lifecycle1, "first", "release:first")
    _, _, second = _promote(service1, lifecycle1, "second", "release:second")
    store1.close()

    _, store2, service2 = _service(db)
    assert service2.manifest(first.promotion_id) == first
    assert service2.manifest(second.promotion_id) == second
    assert {item.promotion_id for item in store2.manifests()} == {
        first.promotion_id,
        second.promotion_id,
    }
    store2.close()


def test_governed_rollback_still_works_after_restart(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle1, store1, service1 = _service(db)
    _, _, old = _promote(service1, lifecycle1, "old", "release:old")
    _, _, current = _promote(service1, lifecycle1, "current", "release:current")
    store1.close()

    _, store2, service2 = _service(db)
    rollback = service2.rollback(
        promotion_id=current.promotion_id,
        target_promotion_id=old.promotion_id,
        reason="post-restart regression",
        rolled_back_by="release-owner@example",
    )
    assert rollback.promotion_id == current.promotion_id
    assert rollback.target_promotion_id == old.promotion_id
    assert store2.rollbacks() == (rollback,)
    store2.close()


def test_duplicate_rollback_remains_blocked_after_second_restart(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle1, store1, service1 = _service(db)
    _, _, old = _promote(service1, lifecycle1, "old", "release:old")
    _, _, current = _promote(service1, lifecycle1, "current", "release:current")
    service1.rollback(
        promotion_id=current.promotion_id,
        target_promotion_id=old.promotion_id,
        reason="regression",
        rolled_back_by="owner",
    )
    store1.close()

    _, store2, service2 = _service(db)
    with pytest.raises(ValueError, match="already been rolled back"):
        service2.rollback(
            promotion_id=current.promotion_id,
            target_promotion_id=old.promotion_id,
            reason="replay",
            rolled_back_by="owner",
        )
    store2.close()


def test_unfinished_approval_is_rehydrated_but_restart_fails_closed(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle1, store1, service1 = _service(db)
    binding = _prepare(lifecycle1, "pending")
    approval = service1.issue_human_approval(binding=binding, approved_by="owner@example")
    store1.close()

    _, store2, service2 = _service(db)
    assert store2.approvals() == (approval,)
    # Lifecycle/orchestrator in-flight state is intentionally not reconstructed.
    # A restart therefore cannot silently promote a half-finished session.
    with pytest.raises(ValueError, match="unknown candidate_id"):
        service2.promote(
            approval=approval,
            expected_binding=binding,
            release_ref="release:pending",
        )
    store2.close()


def test_store_rejects_duplicate_durable_approval(tmp_path: Path) -> None:
    db = tmp_path / "governance.sqlite"
    lifecycle, store, service = _service(db)
    binding = _prepare(lifecycle, "dup")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")

    with pytest.raises(ValueError, match="already persisted"):
        store.record_approval(approval)
    store.close()
