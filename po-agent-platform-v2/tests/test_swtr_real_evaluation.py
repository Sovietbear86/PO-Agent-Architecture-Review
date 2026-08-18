from __future__ import annotations

import pytest

from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot
from po_agent.harness.swtr_real_evaluation import (
    AgentObservation,
    RealShadowBudgetExceeded,
    RealShadowPolicy,
    SWTRRealShadowEvaluator,
    ShadowDecision,
    ShadowRunVerdict,
)


def _case(key: str, title: str = "Task") -> SWTRTaskSnapshot:
    payload = (
        '{"key":"%s","source":"swtr","title":"%s"}' % (key, title)
    )
    import hashlib

    return SWTRTaskSnapshot(
        task_key=key,
        source="swtr",
        payload_json=payload,
        content_sha256=hashlib.sha256(payload.encode()).hexdigest(),
    )


def _batch(*cases: SWTRTaskSnapshot) -> SWTRShadowBatch:
    return SWTRShadowBatch.build(cases)


def _agent(score: float, **flags):
    def run(snapshot):
        assert isinstance(snapshot, dict)
        return AgentObservation(
            answer=f"answer for {snapshot['key']}",
            score=score,
            grounded=flags.pop("grounded", True),
            hallucination=flags.pop("hallucination", False),
            wrong_skill=flags.pop("wrong_skill", False),
            provider_error=flags.pop("provider_error", False),
            latency_ms=10.0,
            llm_calls=1,
        )

    return run


def test_real_shadow_improvement_requires_human_approval():
    evaluator = SWTRRealShadowEvaluator(
        RealShadowPolicy(min_improved_cases=2, min_score_delta=0.05)
    )
    result = evaluator.evaluate(
        _batch(_case("SWTR-1"), _case("SWTR-2")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.50),
        candidate_agent=_agent(0.80),
    )

    assert result.verdict is ShadowRunVerdict.APPROVAL_REQUIRED
    assert result.improved_cases == 2
    assert result.regressed_cases == 0
    assert all(case.decision is ShadowDecision.IMPROVED for case in result.cases)
    assert result.total_llm_calls == 4
    assert len(result.run_sha256) == 64


def test_real_shadow_regression_is_rejected():
    evaluator = SWTRRealShadowEvaluator(
        RealShadowPolicy(min_improved_cases=1, min_score_delta=0.05)
    )
    result = evaluator.evaluate(
        _batch(_case("SWTR-3")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.90),
        candidate_agent=_agent(0.60),
    )

    assert result.verdict is ShadowRunVerdict.REJECTED
    assert result.regressed_cases == 1


@pytest.mark.parametrize("flag", ["hallucination", "wrong_skill", "provider_error"])
def test_false_green_candidate_signals_fail_closed(flag):
    evaluator = SWTRRealShadowEvaluator(RealShadowPolicy(min_improved_cases=1))
    result = evaluator.evaluate(
        _batch(_case("SWTR-4")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.50),
        candidate_agent=_agent(0.99, **{flag: True}),
    )

    assert result.verdict is ShadowRunVerdict.REJECTED
    assert result.blocked_cases == 1
    assert result.cases[0].decision is ShadowDecision.BLOCKED


def test_ungrounded_candidate_fails_closed_even_with_high_score():
    evaluator = SWTRRealShadowEvaluator(RealShadowPolicy(min_improved_cases=1))
    result = evaluator.evaluate(
        _batch(_case("SWTR-5")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.50),
        candidate_agent=_agent(1.00, grounded=False),
    )
    assert result.verdict is ShadowRunVerdict.REJECTED
    assert result.blocked_cases == 1


def test_no_meaningful_improvement_returns_no_action():
    evaluator = SWTRRealShadowEvaluator(
        RealShadowPolicy(min_improved_cases=1, min_score_delta=0.10)
    )
    result = evaluator.evaluate(
        _batch(_case("SWTR-6")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.70),
        candidate_agent=_agent(0.75),
    )
    assert result.verdict is ShadowRunVerdict.NO_ACTION
    assert result.equivalent_cases == 1


def test_case_budget_enforced_before_agent_execution():
    calls = []

    def should_not_run(snapshot):
        calls.append(snapshot)
        return AgentObservation(answer="x", score=1.0, grounded=True)

    evaluator = SWTRRealShadowEvaluator(RealShadowPolicy(max_cases=1))
    with pytest.raises(RealShadowBudgetExceeded):
        evaluator.evaluate(
            _batch(_case("SWTR-7"), _case("SWTR-8")),
            baseline_id="baseline-v1",
            candidate_id="candidate-v2",
            baseline_agent=should_not_run,
            candidate_agent=should_not_run,
        )
    assert calls == []


def test_llm_call_budget_fails_closed():
    def expensive(snapshot):
        return AgentObservation(
            answer="expensive",
            score=0.8,
            grounded=True,
            llm_calls=3,
        )

    evaluator = SWTRRealShadowEvaluator(
        RealShadowPolicy(max_total_llm_calls=5, min_improved_cases=1)
    )
    with pytest.raises(RealShadowBudgetExceeded):
        evaluator.evaluate(
            _batch(_case("SWTR-9")),
            baseline_id="baseline-v1",
            candidate_id="candidate-v2",
            baseline_agent=expensive,
            candidate_agent=expensive,
        )


def test_evidence_is_deterministic_except_elapsed_time():
    evaluator = SWTRRealShadowEvaluator(RealShadowPolicy(min_improved_cases=1))
    kwargs = dict(
        batch=_batch(_case("SWTR-10")),
        baseline_id="baseline-v1",
        candidate_id="candidate-v2",
        baseline_agent=_agent(0.4),
        candidate_agent=_agent(0.9),
    )
    first = evaluator.evaluate(**kwargs)
    second = evaluator.evaluate(**kwargs)

    assert first.run_sha256 == second.run_sha256
    assert first.cases[0].evidence_sha256 == second.cases[0].evidence_sha256


def test_same_baseline_and_candidate_identity_rejected():
    evaluator = SWTRRealShadowEvaluator()
    with pytest.raises(ValueError, match="must differ"):
        evaluator.evaluate(
            _batch(_case("SWTR-11")),
            baseline_id="same",
            candidate_id="same",
            baseline_agent=_agent(0.5),
            candidate_agent=_agent(0.6),
        )
