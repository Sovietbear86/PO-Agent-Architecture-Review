from po_agent.harness.evolution_lifecycle import (
    ControlledImprovementLifecycle,
    EvaluationSnapshot,
    LifecycleState,
    PromotionPolicy,
)
from po_agent.harness.improvement_candidates import ImprovementCandidate


def _candidate(candidate_id: str = "cand-1") -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id=candidate_id,
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title="Investigate routing",
        rationale="Repeated evidence",
        source_failure_key="intent_mismatch:task_search->task_lookup",
        source_eval_ids=("eval-1", "eval-2", "eval-3"),
        proposed_change={"action": "review_router_rule", "apply": False},
    )


def _green(candidate_id: str = "cand-1") -> EvaluationSnapshot:
    return EvaluationSnapshot.create(
        candidate_id=candidate_id,
        corpus_size=8,
        passed=8,
        failed=0,
    )


def test_candidate_cannot_promote_without_evaluation_and_human_approval() -> None:
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(_candidate())

    decision = lifecycle.decision("cand-1")
    assert decision.eligible is False
    assert "missing_evaluation" in decision.reasons
    assert "human_approval_required" in decision.reasons


def test_green_evaluation_still_requires_human_approval() -> None:
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(_candidate())
    lifecycle.record_evaluation(_green())

    decision = lifecycle.decision("cand-1")
    assert decision.eligible is False
    assert decision.reasons == ("human_approval_required",)
    assert lifecycle.get("cand-1").state is LifecycleState.EVALUATED


def test_green_candidate_can_be_approved_and_marked_promoted() -> None:
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(_candidate())
    lifecycle.record_evaluation(_green())
    lifecycle.request_approval("cand-1")
    lifecycle.approve("cand-1", approver="owner@example", note="reviewed")

    decision = lifecycle.decision("cand-1")
    assert decision.eligible is True
    assert decision.reasons == ()

    record = lifecycle.mark_promoted("cand-1", release_ref="commit:abc123")
    assert record.state is LifecycleState.PROMOTED
    assert record.promoted_ref == "commit:abc123"


def test_any_safety_regression_blocks_approval() -> None:
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(_candidate())
    lifecycle.record_evaluation(
        EvaluationSnapshot.create(
            candidate_id="cand-1",
            corpus_size=8,
            passed=8,
            failed=0,
            safety_regressions=1,
        )
    )

    decision = lifecycle.decision("cand-1")
    assert decision.eligible is False
    assert "safety_regression" in decision.reasons

    try:
        lifecycle.approve("cand-1", approver="owner@example")
    except ValueError as exc:
        assert "safety_regression" in str(exc)
    else:
        raise AssertionError("unsafe candidate must not be approved")


def test_failed_or_small_corpus_blocks_technical_gate() -> None:
    lifecycle = ControlledImprovementLifecycle(PromotionPolicy(min_corpus_size=5, min_pass_rate=1.0))
    lifecycle.register(_candidate())
    lifecycle.record_evaluation(
        EvaluationSnapshot.create(candidate_id="cand-1", corpus_size=4, passed=3, failed=1)
    )

    decision = lifecycle.decision("cand-1")
    assert "insufficient_corpus" in decision.reasons
    assert "pass_rate_below_threshold" in decision.reasons


def test_promotion_records_external_release_but_does_not_apply_candidate_change() -> None:
    candidate = _candidate()
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(candidate)
    lifecycle.record_evaluation(_green())
    lifecycle.approve("cand-1", approver="owner@example")
    record = lifecycle.mark_promoted("cand-1", release_ref="pr:42")

    assert record.candidate.proposed_change["apply"] is False
    assert record.promoted_ref == "pr:42"


def test_promoted_candidate_can_be_rolled_back_with_reason() -> None:
    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(_candidate())
    lifecycle.record_evaluation(_green())
    lifecycle.approve("cand-1", approver="owner@example")
    lifecycle.mark_promoted("cand-1", release_ref="commit:abc123")

    record = lifecycle.rollback("cand-1", reason="shadow regression")
    assert record.state is LifecycleState.ROLLED_BACK
    assert record.rollback_reason == "shadow regression"


def test_register_is_idempotent_for_same_candidate_id() -> None:
    lifecycle = ControlledImprovementLifecycle()
    first = lifecycle.register(_candidate())
    second = lifecycle.register(_candidate())
    assert first is second


def test_evaluation_counter_contract_is_fail_closed() -> None:
    try:
        EvaluationSnapshot.create(candidate_id="cand-1", corpus_size=3, passed=3, failed=1)
    except ValueError as exc:
        assert "passed + failed" in str(exc)
    else:
        raise AssertionError("inconsistent evaluation counters must be rejected")
