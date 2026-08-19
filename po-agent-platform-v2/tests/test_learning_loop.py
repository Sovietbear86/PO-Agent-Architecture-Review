from po_agent.evolution.learning_loop import (
    EvaluationSnapshot,
    GateDecision,
    LearningLoop,
    PromotionGate,
)


def snap(passed=8, total=8, false_green=0, errors=0):
    return EvaluationSnapshot(total, passed, false_green, errors)


def test_core8_equal_candidate_is_recommendation_but_not_auto_promoted():
    loop = LearningLoop(PromotionGate(min_cases=8))
    decision = loop.compare(snap(), snap())
    assert decision.decision == GateDecision.RECOMMEND
    assert decision.requires_human_approval is True
    assert loop.can_promote(decision) is False
    assert loop.can_promote(decision, human_approved=True) is True


def test_false_green_fails_closed():
    decision = LearningLoop().compare(snap(), snap(false_green=1))
    assert decision.decision == GateDecision.REJECT
    assert any("false-green" in reason for reason in decision.reasons)


def test_regression_fails_closed():
    decision = LearningLoop().compare(snap(), snap(passed=7))
    assert decision.decision == GateDecision.REJECT


def test_insufficient_evidence_cannot_promote():
    loop = LearningLoop()
    decision = loop.compare(snap(total=7, passed=7), snap(total=7, passed=7))
    assert decision.decision == GateDecision.INSUFFICIENT_EVIDENCE
    assert loop.can_promote(decision, human_approved=True) is False
