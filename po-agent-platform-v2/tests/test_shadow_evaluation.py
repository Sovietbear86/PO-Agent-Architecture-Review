from __future__ import annotations

from dataclasses import replace

import pytest

from po_agent.harness.eval_store import EvalSeed
from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, LifecycleState
from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.shadow_evaluation import (
    SQLiteShadowEvaluationAuditStore,
    ShadowEvaluator,
    ShadowObservation,
)


def _candidate() -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id="candidate-1",
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title="Improve sprint routing",
        rationale="Observed repeated intent mismatch",
        source_failure_key="intent:sprint_health",
        source_eval_ids=("eval-1", "eval-2", "eval-3"),
        proposed_change={"action": "review_router_rule", "apply": False},
    )


def _seed(eval_id: str, expected_intent: str = "sprint_health") -> EvalSeed:
    return EvalSeed(
        eval_id=eval_id,
        source_trace_id=f"trace-{eval_id}",
        source_feedback_id=None,
        created_at="2026-08-17T00:00:00+00:00",
        query="Готовность спринта WMB-SPRNT-1",
        expected_intent=expected_intent,
    )


class StaticRunner:
    def __init__(self, observation: ShadowObservation) -> None:
        self.observation = observation
        self.calls: list[tuple[str, str | None]] = []

    def run(self, seed: EvalSeed, candidate: ImprovementCandidate | None) -> ShadowObservation:
        self.calls.append((seed.eval_id, candidate.candidate_id if candidate else None))
        return self.observation


def test_shadow_evaluator_compares_same_seed_without_applying_candidate() -> None:
    candidate = _candidate()
    seeds = [_seed("eval-1"), _seed("eval-2"), _seed("eval-3")]
    baseline = StaticRunner(ShadowObservation(intent=None, llm_calls=2, latency_ms=10))
    proposed = StaticRunner(ShadowObservation(intent="sprint_health", llm_calls=3, latency_ms=12))

    report = ShadowEvaluator().evaluate(
        candidate=candidate,
        seeds=seeds,
        baseline_runner=baseline,
        candidate_runner=proposed,
    )

    assert report.corpus_size == 3
    assert report.baseline_passed == 0
    assert report.candidate_passed == 3
    assert report.improved_cases == 3
    assert report.regressed_cases == 0
    assert baseline.calls == [("eval-1", None), ("eval-2", None), ("eval-3", None)]
    assert proposed.calls == [
        ("eval-1", "candidate-1"),
        ("eval-2", "candidate-1"),
        ("eval-3", "candidate-1"),
    ]
    assert candidate.proposed_change["apply"] is False


def test_snapshot_is_candidate_evidence_and_can_drive_lifecycle() -> None:
    candidate = _candidate()
    runner = StaticRunner(ShadowObservation(intent="sprint_health"))
    report = ShadowEvaluator().evaluate(
        candidate=candidate,
        seeds=[_seed("eval-1"), _seed("eval-2"), _seed("eval-3")],
        baseline_runner=StaticRunner(ShadowObservation(intent=None)),
        candidate_runner=runner,
    )
    snapshot = report.to_snapshot()

    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(candidate)
    lifecycle.record_evaluation(snapshot)
    record = lifecycle.request_approval(candidate.candidate_id)

    assert snapshot.passed == 3
    assert snapshot.failed == 0
    assert "shadow_report=" in (snapshot.notes or "")
    assert record.state is LifecycleState.APPROVAL_REQUIRED


def test_candidate_regression_fails_seed_even_when_baseline_passed() -> None:
    report = ShadowEvaluator().evaluate(
        candidate=_candidate(),
        seeds=[_seed("eval-1")],
        baseline_runner=StaticRunner(ShadowObservation(intent="sprint_health")),
        candidate_runner=StaticRunner(ShadowObservation(intent=None)),
    )

    assert report.baseline_passed == 1
    assert report.candidate_passed == 0
    assert report.regressed_cases == 1
    assert report.comparisons[0].reasons == ("candidate:intent_mismatch",)


def test_new_safety_regression_is_counted_and_blocks_promotion() -> None:
    candidate = _candidate()
    report = ShadowEvaluator().evaluate(
        candidate=candidate,
        seeds=[_seed("eval-1"), _seed("eval-2"), _seed("eval-3")],
        baseline_runner=StaticRunner(ShadowObservation(intent="sprint_health")),
        candidate_runner=StaticRunner(
            ShadowObservation(intent="sprint_health", unsupported_request_executed=True)
        ),
    )
    snapshot = report.to_snapshot()

    lifecycle = ControlledImprovementLifecycle()
    lifecycle.register(candidate)
    lifecycle.record_evaluation(snapshot)

    assert report.safety_regressions == 3
    assert snapshot.safety_regressions == 3
    with pytest.raises(ValueError, match="safety_regression"):
        lifecycle.request_approval(candidate.candidate_id)


def test_existing_baseline_safety_problem_is_not_mislabeled_as_new_regression() -> None:
    unsafe = ShadowObservation(
        intent="sprint_health",
        unsupported_request_executed=True,
    )
    report = ShadowEvaluator().evaluate(
        candidate=_candidate(),
        seeds=[_seed("eval-1")],
        baseline_runner=StaticRunner(unsafe),
        candidate_runner=StaticRunner(unsafe),
    )

    assert report.safety_regressions == 0
    assert report.candidate_passed == 0


def test_expected_entity_and_facts_are_checked_deterministically() -> None:
    seed = replace(
        _seed("eval-1"),
        expected_entity="WMB-SPRNT-1",
        expected_facts=["blocked=0", "risk=low"],
    )
    report = ShadowEvaluator().evaluate(
        candidate=_candidate(),
        seeds=[seed],
        baseline_runner=StaticRunner(ShadowObservation()),
        candidate_runner=StaticRunner(
            ShadowObservation(
                intent="sprint_health",
                entity="WMB-SPRNT-1",
                facts=("blocked=0", "risk=low"),
            )
        ),
    )

    assert report.candidate_passed == 1
    assert report.comparisons[0].reasons[:2] == (
        "baseline:intent_mismatch",
        "baseline:entity_mismatch",
    )


def test_provider_error_is_fail_closed_evaluation_evidence() -> None:
    report = ShadowEvaluator().evaluate(
        candidate=_candidate(),
        seeds=[_seed("eval-1")],
        baseline_runner=StaticRunner(ShadowObservation(intent="sprint_health")),
        candidate_runner=StaticRunner(
            ShadowObservation(intent="sprint_health", provider_error=True)
        ),
    )
    snapshot = report.to_snapshot()

    assert report.candidate_passed == 0
    assert snapshot.provider_errors == 1
    assert "candidate:provider_error" in report.comparisons[0].reasons


def test_latency_and_llm_calls_are_measured_but_do_not_override_correctness() -> None:
    report = ShadowEvaluator().evaluate(
        candidate=_candidate(),
        seeds=[_seed("eval-1"), _seed("eval-2")],
        baseline_runner=StaticRunner(
            ShadowObservation(intent="sprint_health", latency_ms=20, llm_calls=5)
        ),
        candidate_runner=StaticRunner(
            ShadowObservation(intent="sprint_health", latency_ms=12, llm_calls=3)
        ),
    )

    assert report.baseline_latency_ms == 40
    assert report.candidate_latency_ms == 24
    assert report.baseline_llm_calls == 10
    assert report.candidate_llm_calls == 6
    assert report.candidate_passed == 2


def test_append_only_audit_store_round_trips_report_and_rejects_duplicate() -> None:
    store = SQLiteShadowEvaluationAuditStore()
    evaluator = ShadowEvaluator(audit_store=store)
    report = evaluator.evaluate(
        candidate=_candidate(),
        seeds=[_seed("eval-1")],
        baseline_runner=StaticRunner(ShadowObservation(intent=None)),
        candidate_runner=StaticRunner(
            ShadowObservation(intent="sprint_health", facts=("risk=low",))
        ),
    )

    loaded = store.get(report.report_id)
    assert loaded is not None
    assert loaded.report_id == report.report_id
    assert loaded.candidate_id == report.candidate_id
    assert loaded.candidate_passed == 1
    assert tuple(loaded.comparisons[0].candidate.facts) == ("risk=low",)

    with pytest.raises(ValueError, match="already exists"):
        store.append(report)


def test_empty_corpus_and_negative_regression_count_fail_closed() -> None:
    evaluator = ShadowEvaluator()
    with pytest.raises(ValueError, match="at least one EvalSeed"):
        evaluator.evaluate(
            candidate=_candidate(),
            seeds=[],
            baseline_runner=StaticRunner(ShadowObservation()),
            candidate_runner=StaticRunner(ShadowObservation()),
        )
    with pytest.raises(ValueError, match="cannot be negative"):
        evaluator.evaluate(
            candidate=_candidate(),
            seeds=[_seed("eval-1")],
            baseline_runner=StaticRunner(ShadowObservation()),
            candidate_runner=StaticRunner(ShadowObservation()),
            new_code_regressions=-1,
        )
