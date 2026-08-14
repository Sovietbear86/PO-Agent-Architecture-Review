from dataclasses import replace

import pytest

from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.lifecycle import CandidateLifecycle, CandidateLifecycleRecord, LifecycleStatus
from po_agent.harness.offline_evaluator import EvalOutcome, OfflineEvaluator, RegressionGate, RegressionPolicy


def candidate() -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id="cand-1",
        created_at="2026-08-12T00:00:00+00:00",
        kind="routing_rule",
        title="Fix routing",
        rationale="Repeated curated intent mismatch",
        source_failure_key="intent_mismatch:task-lookup",
        source_eval_ids=("eval-1",),
        proposed_change={"action": "review_router_rule", "apply": False},
    )


def runner(case: dict, proposed: object | None) -> EvalOutcome:
    if case["id"] == "target":
        return EvalOutcome.PASS if proposed is not None else EvalOutcome.FAIL
    return EvalOutcome.PASS


def test_candidate_must_pass_gate_then_human_approval_before_promotion():
    lifecycle = CandidateLifecycle(
        OfflineEvaluator(runner),
        RegressionGate(RegressionPolicy(max_regressions=0, min_improvements=1)),
    )
    record = CandidateLifecycleRecord(candidate())

    with pytest.raises(ValueError, match="human approval"):
        lifecycle.promote(record, version="router-2", promoter=lambda *_: None)

    evaluated = lifecycle.evaluate(record, [{"id": "target"}, {"id": "control"}])
    assert evaluated.status is LifecycleStatus.READY_FOR_APPROVAL
    assert evaluated.evaluation is not None
    assert evaluated.evaluation.improvements == 1
    assert evaluated.evaluation.regressions == 0

    approved = lifecycle.approve(evaluated, approved_by="po-owner", reason="eval corpus passed")
    promoted_calls = []
    promoted = lifecycle.promote(
        approved,
        version="router-2",
        promoter=lambda cand, version: promoted_calls.append((cand.candidate_id, version)),
    )
    assert promoted.status is LifecycleStatus.PROMOTED
    assert promoted.promoted_version == "router-2"
    assert promoted_calls == [("cand-1", "router-2")]

    rollback_calls = []
    rolled_back = lifecycle.rollback(
        promoted,
        reason="production regression detected",
        rollback=lambda cand, version: rollback_calls.append((cand.candidate_id, version)),
    )
    assert rolled_back.status is LifecycleStatus.ROLLED_BACK
    assert rollback_calls == [("cand-1", "router-2")]


def test_regression_gate_blocks_human_approval():
    def regressing_runner(case: dict, proposed: object | None) -> EvalOutcome:
        if case["id"] == "control" and proposed is not None:
            return EvalOutcome.FAIL
        return EvalOutcome.PASS

    lifecycle = CandidateLifecycle(OfflineEvaluator(regressing_runner))
    evaluated = lifecycle.evaluate(CandidateLifecycleRecord(candidate()), [{"id": "control"}])
    assert evaluated.status is LifecycleStatus.REJECTED_BY_REGRESSION_GATE
    with pytest.raises(ValueError, match="pass regression gate"):
        lifecycle.approve(evaluated, approved_by="po-owner", reason="override")


def test_human_can_reject_candidate_after_successful_gate():
    lifecycle = CandidateLifecycle(OfflineEvaluator(runner))
    evaluated = lifecycle.evaluate(CandidateLifecycleRecord(candidate()), [{"id": "target"}])
    rejected = lifecycle.reject(evaluated, rejected_by="po-owner", reason="business rule is wrong")
    assert rejected.status is LifecycleStatus.REJECTED_BY_HUMAN


def test_candidate_cannot_become_self_applying_before_promotion():
    lifecycle = CandidateLifecycle(OfflineEvaluator(runner))
    unsafe = replace(candidate(), proposed_change={"action": "review_router_rule", "apply": True})
    evaluated = lifecycle.evaluate(CandidateLifecycleRecord(unsafe), [{"id": "target"}])
    approved = lifecycle.approve(evaluated, approved_by="po-owner", reason="test")
    with pytest.raises(ValueError, match="non-self-applying"):
        lifecycle.promote(approved, version="router-2", promoter=lambda *_: None)
