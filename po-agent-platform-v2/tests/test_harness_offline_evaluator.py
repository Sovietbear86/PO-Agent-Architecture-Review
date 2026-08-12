from dataclasses import dataclass

from po_agent.harness.offline_evaluator import (
    EvalOutcome,
    OfflineEvaluator,
    RegressionGate,
    RegressionPolicy,
)


@dataclass(frozen=True)
class FakeCase:
    case_id: str
    baseline: EvalOutcome
    candidate: EvalOutcome


def runner(case: FakeCase, candidate: object | None) -> EvalOutcome:
    return case.baseline if candidate is None else case.candidate


def test_candidate_with_improvement_and_no_regression_is_ready_for_human_approval():
    cases = [
        FakeCase("routing-1", EvalOutcome.FAIL, EvalOutcome.PASS),
        FakeCase("stable-1", EvalOutcome.PASS, EvalOutcome.PASS),
    ]
    report = OfflineEvaluator(runner).evaluate("candidate-1", {"apply": False}, cases)
    decision = RegressionGate().decide(report)

    assert report.improvements == 1
    assert report.regressions == 0
    assert decision.passed is True
    assert decision.status == "ready_for_approval"
    assert decision.requires_human_approval is True


def test_regression_blocks_candidate_even_when_other_case_improves():
    cases = [
        FakeCase("routing-1", EvalOutcome.FAIL, EvalOutcome.PASS),
        FakeCase("stable-1", EvalOutcome.PASS, EvalOutcome.FAIL),
    ]
    report = OfflineEvaluator(runner).evaluate("candidate-2", {"apply": False}, cases)
    decision = RegressionGate().decide(report)

    assert report.improvements == 1
    assert report.regressions == 1
    assert decision.passed is False
    assert decision.status == "rejected_by_regression_gate"


def test_policy_can_require_minimum_pass_rate():
    cases = [
        FakeCase("a", EvalOutcome.FAIL, EvalOutcome.PASS),
        FakeCase("b", EvalOutcome.FAIL, EvalOutcome.FAIL),
    ]
    report = OfflineEvaluator(runner).evaluate("candidate-3", object(), cases)
    decision = RegressionGate(RegressionPolicy(min_pass_rate=0.75)).decide(report)

    assert report.candidate_pass_rate == 0.5
    assert decision.passed is False
