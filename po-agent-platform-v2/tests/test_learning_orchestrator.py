from po_agent.evolution.learning_loop import EvaluationSnapshot, GateDecision
from po_agent.evolution.learning_orchestrator import ControlledLearningOrchestrator
from po_agent.evolution.models import ImprovementType, SkillImprovementCandidate
from po_agent.evolution.pipeline import SkillEvolutionPipeline
from po_agent.skill.registry import SkillRegistry


def _candidate():
    return SkillImprovementCandidate(
        candidate_id="candidate-core8-001",
        skill_id="task_summary",
        skill_version="1.0.0",
        improvement_type=ImprovementType.LOW_ACCURACY,
        threshold_value=0.7,
        current_value=0.5,
    )


def _snapshot(passed=8, false_green=0, errors=0):
    return EvaluationSnapshot(
        total_cases=8,
        passed_cases=passed,
        false_green_count=false_green,
        error_count=errors,
    )


def test_orchestrator_rejects_degraded_candidate_without_mutating_registry():
    registry = SkillRegistry()
    pipeline = SkillEvolutionPipeline(registry)
    orchestrator = ControlledLearningOrchestrator(pipeline)
    orchestrator.register_candidate(_candidate())

    before = registry.count_skills()
    artifact = orchestrator.evaluate_candidate(
        "candidate-core8-001",
        baseline=_snapshot(),
        candidate=_snapshot(passed=7),
        evidence={"case_set": "core8"},
    )

    assert artifact.decision.decision == GateDecision.REJECT
    assert registry.count_skills() == before
    assert orchestrator.can_promote("candidate-core8-001", human_approved=True) is False


def test_green_candidate_still_requires_explicit_human_approval():
    registry = SkillRegistry()
    pipeline = SkillEvolutionPipeline(registry)
    orchestrator = ControlledLearningOrchestrator(pipeline)
    orchestrator.register_candidate(_candidate())

    artifact = orchestrator.evaluate_candidate(
        "candidate-core8-001",
        baseline=_snapshot(),
        candidate=_snapshot(),
    )

    assert artifact.decision.decision == GateDecision.RECOMMEND
    assert orchestrator.can_promote("candidate-core8-001") is False
    assert orchestrator.can_promote("candidate-core8-001", human_approved=True) is True


def test_artifact_is_required_before_approval_boundary():
    registry = SkillRegistry()
    pipeline = SkillEvolutionPipeline(registry)
    orchestrator = ControlledLearningOrchestrator(pipeline)
    orchestrator.register_candidate(_candidate())

    assert orchestrator.can_promote("candidate-core8-001", human_approved=True) is False
