from dataclasses import replace

import pytest

from po_agent.harness.evolution_lifecycle import (
    ControlledImprovementLifecycle,
    EvaluationSnapshot,
    LifecycleState,
)
from po_agent.harness.governed_promotion import (
    ApprovalSigner,
    GovernanceEventType,
    GovernedPromotionService,
    PromotionBinding,
    SQLiteGovernanceAuditStore,
)
from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.promotion_registry import VersionedPromotionRegistry


KEY = b"g" * 32


def _candidate(candidate_id: str) -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id=candidate_id,
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title=f"Candidate {candidate_id}",
        rationale="Evidence-backed improvement",
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


def _service():
    lifecycle = ControlledImprovementLifecycle()
    registry = VersionedPromotionRegistry()
    audit = SQLiteGovernanceAuditStore()
    service = GovernedPromotionService(
        lifecycle=lifecycle,
        registry=registry,
        signer=ApprovalSigner(KEY),
        audit_store=audit,
    )
    return lifecycle, registry, service


def test_promotion_requires_explicit_human_approval() -> None:
    lifecycle, _, service = _service()
    binding = _prepare(lifecycle, "cand-1")

    with pytest.raises(ValueError, match="unknown"):
        service.promote(
            approval=replace(
                service.issue_human_approval(binding=binding, approved_by="owner@example"),
                approval_id="forged",
            ),
            expected_binding=binding,
            release_ref="release:1",
        )


def test_signed_approval_is_bound_to_baseline_fingerprint_and_evaluation() -> None:
    lifecycle, _, service = _service()
    binding = _prepare(lifecycle, "cand-1")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")

    for changed in (
        replace(binding, baseline_sha="other-baseline"),
        replace(binding, candidate_fingerprint="other-fingerprint"),
        replace(binding, evaluation_id="other-evaluation"),
    ):
        with pytest.raises(ValueError, match="binding|evaluation"):
            service.promote(approval=approval, expected_binding=changed, release_ref="release:1")


def test_tampered_signed_approval_is_rejected() -> None:
    lifecycle, _, service = _service()
    binding = _prepare(lifecycle, "cand-1")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")
    tampered = replace(approval, note="tampered")

    with pytest.raises(ValueError, match="unknown|does not match"):
        service.promote(approval=tampered, expected_binding=binding, release_ref="release:1")


def test_green_candidate_promotes_once_and_consumes_approval() -> None:
    lifecycle, registry, service = _service()
    binding = _prepare(lifecycle, "cand-1")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")
    manifest = service.promote(approval=approval, expected_binding=binding, release_ref="release:1")

    assert manifest.binding == binding
    assert registry.promotion(manifest.promotion_id) is not None
    assert lifecycle.get("cand-1").state is LifecycleState.PROMOTED

    with pytest.raises(ValueError, match="consumed"):
        service.promote(approval=approval, expected_binding=binding, release_ref="release:2")


def test_stale_approval_cannot_promote_after_new_evaluation() -> None:
    lifecycle, _, service = _service()
    binding = _prepare(lifecycle, "cand-1")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")
    lifecycle.record_evaluation(
        EvaluationSnapshot.create(candidate_id="cand-1", corpus_size=8, passed=8, failed=0)
    )

    with pytest.raises(ValueError, match="evaluation_id"):
        service.promote(approval=approval, expected_binding=binding, release_ref="release:1")


def test_approval_for_one_candidate_cannot_promote_another() -> None:
    lifecycle, _, service = _service()
    binding_a = _prepare(lifecycle, "cand-a")
    approval_a = service.issue_human_approval(binding=binding_a, approved_by="owner@example")
    binding_b = _prepare(lifecycle, "cand-b")

    with pytest.raises(ValueError, match="binding"):
        service.promote(approval=approval_a, expected_binding=binding_b, release_ref="release:b")


def test_audit_is_append_only_and_returns_immutable_tuple() -> None:
    lifecycle, _, service = _service()
    binding = _prepare(lifecycle, "cand-1")
    approval = service.issue_human_approval(binding=binding, approved_by="owner@example")
    manifest = service.promote(approval=approval, expected_binding=binding, release_ref="release:1")

    events = service.audit_events("cand-1")
    assert isinstance(events, tuple)
    assert [event.event_type for event in events] == [
        GovernanceEventType.APPROVAL_ISSUED,
        GovernanceEventType.PROMOTED,
    ]
    assert manifest.promotion_id == events[-1].event_id


def test_rollback_requires_known_earlier_promoted_release() -> None:
    lifecycle, _, service = _service()
    old_binding = _prepare(lifecycle, "old")
    old_approval = service.issue_human_approval(binding=old_binding, approved_by="owner@example")
    old = service.promote(approval=old_approval, expected_binding=old_binding, release_ref="release:old")

    new_binding = _prepare(lifecycle, "new")
    new_approval = service.issue_human_approval(binding=new_binding, approved_by="owner@example")
    new = service.promote(approval=new_approval, expected_binding=new_binding, release_ref="release:new")

    rolled_back = service.rollback(
        promotion_id=new.promotion_id,
        target_promotion_id=old.promotion_id,
        reason="post-promotion regression",
        rolled_back_by="release-owner@example",
    )
    assert rolled_back.target_release_ref == "release:old"
    assert lifecycle.get("new").state is LifecycleState.ROLLED_BACK


def test_rollback_rejects_unknown_same_or_forward_target() -> None:
    lifecycle, _, service = _service()
    first_binding = _prepare(lifecycle, "first")
    first_approval = service.issue_human_approval(binding=first_binding, approved_by="owner@example")
    first = service.promote(approval=first_approval, expected_binding=first_binding, release_ref="release:first")

    second_binding = _prepare(lifecycle, "second")
    second_approval = service.issue_human_approval(binding=second_binding, approved_by="owner@example")
    second = service.promote(approval=second_approval, expected_binding=second_binding, release_ref="release:second")

    with pytest.raises(ValueError, match="known governed promotion"):
        service.rollback(
            promotion_id="unknown",
            target_promotion_id=first.promotion_id,
            reason="x",
            rolled_back_by="owner",
        )
    with pytest.raises(ValueError, match="differ"):
        service.rollback(
            promotion_id=second.promotion_id,
            target_promotion_id=second.promotion_id,
            reason="x",
            rolled_back_by="owner",
        )
    with pytest.raises(ValueError, match="earlier"):
        service.rollback(
            promotion_id=first.promotion_id,
            target_promotion_id=second.promotion_id,
            reason="x",
            rolled_back_by="owner",
        )


def test_duplicate_rollback_is_rejected() -> None:
    lifecycle, _, service = _service()
    old_binding = _prepare(lifecycle, "old")
    old_approval = service.issue_human_approval(binding=old_binding, approved_by="owner@example")
    old = service.promote(approval=old_approval, expected_binding=old_binding, release_ref="release:old")
    new_binding = _prepare(lifecycle, "new")
    new_approval = service.issue_human_approval(binding=new_binding, approved_by="owner@example")
    new = service.promote(approval=new_approval, expected_binding=new_binding, release_ref="release:new")

    service.rollback(
        promotion_id=new.promotion_id,
        target_promotion_id=old.promotion_id,
        reason="regression",
        rolled_back_by="owner",
    )
    with pytest.raises(ValueError, match="already been rolled back"):
        service.rollback(
            promotion_id=new.promotion_id,
            target_promotion_id=old.promotion_id,
            reason="again",
            rolled_back_by="owner",
        )


def test_signer_rejects_short_key_and_copy_serialization_boundary() -> None:
    import copy
    import pickle

    with pytest.raises(ValueError, match="32 bytes"):
        ApprovalSigner(b"short")
    signer = ApprovalSigner(KEY)
    with pytest.raises(TypeError):
        pickle.dumps(signer)
    with pytest.raises(TypeError):
        copy.copy(signer)
    with pytest.raises(TypeError):
        copy.deepcopy(signer)
