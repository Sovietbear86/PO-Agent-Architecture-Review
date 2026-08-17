import pytest

from po_agent.harness.promotion_registry import (
    HumanApprovalRecord,
    SQLitePromotionAuditStore,
    VersionedPromotionRegistry,
)


def test_promotion_requires_recorded_human_approval():
    registry = VersionedPromotionRegistry()
    with pytest.raises(ValueError):
        registry.record_promotion(
            approval_id="missing",
            release_ref="release/v1",
            baseline_sha="base",
            candidate_tree_sha256="tree",
        )


def test_approval_promotion_rollback_chain_is_append_only():
    registry = VersionedPromotionRegistry()
    approval = registry.record_approval(
        HumanApprovalRecord.create(candidate_id="c1", evaluation_id="e1", approver="human")
    )
    promotion = registry.record_promotion(
        approval_id=approval.approval_id,
        release_ref="release/v1",
        baseline_sha="base",
        candidate_tree_sha256="tree",
    )
    rollback = registry.record_rollback(
        promotion_id=promotion.promotion_id,
        reason="regression",
        rolled_back_by="human",
    )
    assert rollback.candidate_id == "c1"
    assert len(registry.candidate_history("c1")) == 3
    with pytest.raises(ValueError):
        registry.record_promotion(
            approval_id=approval.approval_id,
            release_ref="release/v2",
            baseline_sha="base",
            candidate_tree_sha256="tree2",
        )
    with pytest.raises(ValueError):
        registry.record_rollback(
            promotion_id=promotion.promotion_id,
            reason="again",
            rolled_back_by="human",
        )


def test_approval_requires_explicit_human_identity():
    with pytest.raises(ValueError):
        HumanApprovalRecord.create(candidate_id="c1", evaluation_id="e1", approver=" ")


def test_sqlite_audit_store_rejects_duplicate_event():
    store = SQLitePromotionAuditStore()
    approval = HumanApprovalRecord.create(candidate_id="c1", evaluation_id="e1", approver="human")
    store.append(approval)
    with pytest.raises(ValueError):
        store.append(approval)
    rows = store.events_for_candidate("c1")
    assert len(rows) == 1
    assert rows[0]["event_type"] == "approval"
