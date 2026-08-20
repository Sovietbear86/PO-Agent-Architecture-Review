import pytest

from po_agent.evolution.controlled_lifecycle import ControlledSkillLifecycle
from po_agent.evolution.learning_loop import EvaluationSnapshot, LearningLoop
from po_agent.evolution.learning_orchestrator import CandidateEvaluationArtifact
from po_agent.skill.models import SkillStatus
from po_agent.skill.registry import SkillRegistry
from po_agent.skill.skills import INITIAL_SKILLS


def build_registry_with_candidate():
    registry = SkillRegistry()
    registry.load_skills_from_dict(INITIAL_SKILLS)
    active = registry.get_active_skill("sprint_health")
    assert active is not None
    candidate = registry.register_new_version(
        "sprint_health", "1.0.1", changes="controlled analytical improvement"
    )
    assert candidate is not None
    return registry, active, candidate


def green_artifact(skill_version="1.0.0"):
    baseline = EvaluationSnapshot(8, 8)
    candidate = EvaluationSnapshot(8, 8)
    decision = LearningLoop().compare(baseline, candidate)
    return CandidateEvaluationArtifact(
        candidate_id="sprint-health-candidate",
        skill_id="sprint_health",
        skill_version=skill_version,
        baseline=baseline,
        candidate=candidate,
        decision=decision,
        evidence={"corpus_id": "sprint-health-frozen-v1"},
    )


def test_promotion_requires_explicit_human_approval():
    registry, active, candidate = build_registry_with_candidate()
    lifecycle = ControlledSkillLifecycle(registry)

    with pytest.raises(PermissionError):
        lifecycle.promote(
            artifact=green_artifact(active.version),
            candidate_version=candidate.version,
            approved_by="owner",
            human_approved=False,
        )

    assert registry.get_active_skill("sprint_health").version == active.version
    assert candidate.status == SkillStatus.CANDIDATE


def test_green_candidate_can_be_promoted_then_rolled_back():
    registry, active, candidate = build_registry_with_candidate()
    lifecycle = ControlledSkillLifecycle(registry)

    receipt = lifecycle.promote(
        artifact=green_artifact(active.version),
        candidate_version=candidate.version,
        approved_by="owner",
        human_approved=True,
    )
    assert receipt.previous_version == active.version
    assert registry.get_active_skill("sprint_health").version == candidate.version
    assert active.status == SkillStatus.DEPRECATED
    assert candidate.status == SkillStatus.ACTIVE

    rollback = lifecycle.rollback(skill_id="sprint_health", approved_by="owner")
    assert rollback.restored_version == active.version
    assert registry.get_active_skill("sprint_health").version == active.version
    assert active.status == SkillStatus.ACTIVE
    assert candidate.status == SkillStatus.DEPRECATED


def test_rejected_shadow_artifact_cannot_promote_even_with_human_approval():
    registry, active, candidate = build_registry_with_candidate()
    baseline = EvaluationSnapshot(8, 8)
    degraded = EvaluationSnapshot(8, 7)
    decision = LearningLoop().compare(baseline, degraded)
    artifact = CandidateEvaluationArtifact(
        candidate_id="bad",
        skill_id="sprint_health",
        skill_version=active.version,
        baseline=baseline,
        candidate=degraded,
        decision=decision,
        evidence={},
    )
    lifecycle = ControlledSkillLifecycle(registry)

    with pytest.raises(ValueError):
        lifecycle.promote(
            artifact=artifact,
            candidate_version=candidate.version,
            approved_by="owner",
            human_approved=True,
        )

    assert registry.get_active_skill("sprint_health").version == active.version


def test_rollback_refuses_if_registry_changed_after_promotion():
    registry, active, candidate = build_registry_with_candidate()
    lifecycle = ControlledSkillLifecycle(registry)
    lifecycle.promote(
        artifact=green_artifact(active.version),
        candidate_version=candidate.version,
        approved_by="owner",
        human_approved=True,
    )

    # Simulate an unexpected out-of-band registry mutation.
    other = registry.register_new_version("sprint_health", "1.0.2", changes="unexpected")
    assert other is not None
    registry.promote_candidate("sprint_health", "1.0.2", "other-owner")

    with pytest.raises(RuntimeError):
        lifecycle.rollback(skill_id="sprint_health", approved_by="owner")
