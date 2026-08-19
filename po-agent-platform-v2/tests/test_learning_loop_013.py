import pytest

from po_agent.evolution.learning_loop import EvaluationSnapshot, GateDecision, LearningLoop, PromotionGate
from po_agent.evolution.learning_orchestrator import ControlledLearningOrchestrator
from po_agent.evolution.shadow_cycle import LearningCycle013
from po_agent.evolution.improvement_synthesizer import ProposalKind


class DummyPipeline:
    def __init__(self):
        self._candidates = {}


def snapshot(passed, total=8, false_green=0, errors=0, corpus="core8-task-search-v1", case_hash="abc123"):
    return EvaluationSnapshot(
        total_cases=total,
        passed_cases=passed,
        false_green_count=false_green,
        error_count=errors,
        metadata={"corpus_id": corpus, "case_set_sha256": case_hash},
    )


def failures(category="ROUTING_ERROR"):
    return [
        {
            "trace_id": "trace-001",
            "category": category,
            "query": "найди карточку WMB-30000",
            "error_message": "unknown intent for task lookup phrase",
        },
        {
            "trace_id": "trace-002",
            "category": category,
            "query": "отыщи карточку WMB-30000",
            "error_message": "unknown intent for task lookup phrase",
        },
    ]


def cycle():
    orchestrator = ControlledLearningOrchestrator(DummyPipeline(), LearningLoop(PromotionGate(min_cases=8)))
    return LearningCycle013(orchestrator), orchestrator


def test_failure_cluster_synthesizes_non_executable_routing_candidate():
    learning, _ = cycle()
    proposal = learning.build_proposal(skill_id="task_search", failures=failures())
    assert proposal.kind == ProposalKind.ROUTING_ALIAS
    assert proposal.target == "intent_router"
    assert proposal.executable is False
    assert proposal.requires_sandbox is True
    assert proposal.requires_human_approval is True
    assert proposal.evidence_ids == ("trace-001", "trace-002")


def test_shadow_candidate_can_show_measurable_improvement_without_production_mutation():
    learning, orchestrator = cycle()
    artifact = learning.run_shadow(
        skill_id="task_search",
        skill_version="1.0.0",
        failures=failures(),
        baseline=snapshot(7),
        candidate=snapshot(8),
        corpus_id="core8-task-search-v1",
    )
    assert artifact.decision.decision == GateDecision.RECOMMEND
    assert artifact.candidate.pass_rate > artifact.baseline.pass_rate
    assert artifact.production_mutations == 0
    assert orchestrator.can_promote(artifact.candidate_id, human_approved=False) is False
    assert orchestrator.can_promote(artifact.candidate_id, human_approved=True) is True


def test_shadow_rejects_false_green_even_when_candidate_is_8_of_8():
    learning, _ = cycle()
    artifact = learning.run_shadow(
        skill_id="task_search",
        skill_version="1.0.0",
        failures=failures(),
        baseline=snapshot(7),
        candidate=snapshot(8, false_green=1),
        corpus_id="core8-task-search-v1",
    )
    assert artifact.decision.decision == GateDecision.REJECT


def test_shadow_rejects_regression():
    learning, _ = cycle()
    artifact = learning.run_shadow(
        skill_id="task_search",
        skill_version="1.0.0",
        failures=failures(),
        baseline=snapshot(8),
        candidate=snapshot(7, errors=1),
        corpus_id="core8-task-search-v1",
    )
    assert artifact.decision.decision == GateDecision.REJECT


def test_shadow_refuses_different_case_sets():
    learning, _ = cycle()
    with pytest.raises(ValueError, match="identical frozen case-set hash"):
        learning.run_shadow(
            skill_id="task_search",
            skill_version="1.0.0",
            failures=failures(),
            baseline=snapshot(7, case_hash="baseline"),
            candidate=snapshot(8, case_hash="candidate"),
            corpus_id="core8-task-search-v1",
        )


def test_shadow_refuses_different_corpus_ids():
    learning, _ = cycle()
    with pytest.raises(ValueError, match="requested frozen corpus"):
        learning.run_shadow(
            skill_id="task_search",
            skill_version="1.0.0",
            failures=failures(),
            baseline=snapshot(7, corpus="corpus-a"),
            candidate=snapshot(8, corpus="corpus-b"),
            corpus_id="corpus-a",
        )


def test_source_contract_failure_never_becomes_executable_patch():
    learning, _ = cycle()
    proposal = learning.build_proposal(skill_id="task_search", failures=failures("ADAPTER_ERROR"))
    assert proposal.kind == ProposalKind.SOURCE_CONTRACT
    assert proposal.executable is False
    assert proposal.change["operation"] == "review_source_contract"
