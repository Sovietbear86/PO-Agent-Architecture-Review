import pytest

from po_agent.harness.offline_evaluator import GateDecision
from po_agent.harness.version_governance import (
    ApprovalStore,
    VersionArtifact,
    VersionRegistry,
)


def passed_gate(candidate_id: str) -> GateDecision:
    return GateDecision(
        candidate_id=candidate_id,
        passed=True,
        status="ready_for_approval",
        reasons=(),
        requires_human_approval=True,
    )


def test_promotion_requires_gate_and_explicit_human_approval():
    candidate_id = "cand-1"
    registry = VersionRegistry({"router": "deterministic-v1"})
    approvals = ApprovalStore()
    approval = approvals.record(candidate_id, approver="po-owner", approved=True, comment="approved after eval")
    artifact = VersionArtifact(component="router", version="deterministic-v2", candidate_id=candidate_id)

    record = registry.promote(artifact, gate=passed_gate(candidate_id), approval=approval)

    assert registry.active("router") == "deterministic-v2"
    assert record.from_version == "deterministic-v1"
    assert record.to_version == "deterministic-v2"
    assert record.approval_id == approval.approval_id


def test_rejected_human_decision_blocks_promotion():
    candidate_id = "cand-2"
    registry = VersionRegistry({"router": "deterministic-v1"})
    approval = ApprovalStore().record(candidate_id, approver="po-owner", approved=False)
    artifact = VersionArtifact(component="router", version="deterministic-v2", candidate_id=candidate_id)

    with pytest.raises(ValueError, match="human approval"):
        registry.promote(artifact, gate=passed_gate(candidate_id), approval=approval)

    assert registry.active("router") == "deterministic-v1"


def test_failed_regression_gate_blocks_promotion_even_if_human_approved():
    candidate_id = "cand-3"
    registry = VersionRegistry({"router": "deterministic-v1"})
    approval = ApprovalStore().record(candidate_id, approver="po-owner", approved=True)
    artifact = VersionArtifact(component="router", version="deterministic-v2", candidate_id=candidate_id)
    gate = GateDecision(
        candidate_id=candidate_id,
        passed=False,
        status="rejected_by_regression_gate",
        reasons=("regressions=1 > 0",),
        requires_human_approval=True,
    )

    with pytest.raises(ValueError, match="regression gate"):
        registry.promote(artifact, gate=gate, approval=approval)


def test_rollback_restores_exact_previous_version_and_is_audited():
    candidate_id = "cand-4"
    registry = VersionRegistry({"router": "deterministic-v1"})
    approval = ApprovalStore().record(candidate_id, approver="po-owner", approved=True)
    promotion = registry.promote(
        VersionArtifact(component="router", version="deterministic-v2", candidate_id=candidate_id),
        gate=passed_gate(candidate_id),
        approval=approval,
    )

    rollback = registry.rollback(promotion.promotion_id, actor="po-owner", reason="shadow KPI degraded")

    assert registry.active("router") == "deterministic-v1"
    assert rollback.from_version == "deterministic-v2"
    assert rollback.to_version == "deterministic-v1"
    assert len(registry.rollback_history) == 1


def test_candidate_identity_mismatch_is_rejected():
    registry = VersionRegistry({"router": "deterministic-v1"})
    approval = ApprovalStore().record("cand-a", approver="po-owner", approved=True)
    artifact = VersionArtifact(component="router", version="deterministic-v2", candidate_id="cand-b")

    with pytest.raises(ValueError, match="candidate identity mismatch"):
        registry.promote(artifact, gate=passed_gate("cand-b"), approval=approval)
