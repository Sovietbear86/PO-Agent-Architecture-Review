from types import SimpleNamespace

import pytest

from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, EvaluationSnapshot
from po_agent.harness.evolution_loop import EvolutionOutcome
from po_agent.harness.governed_promotion import ApprovalSigner, GovernedPromotionService, PromotionBinding
from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.post_promotion_monitoring import MetricDirection, MetricRule, MetricValue, MonitoringPolicy
from po_agent.harness.production_evolution_orchestrator import (
    ProductionEvolutionOrchestrator,
    ProductionEvolutionStage,
)
from po_agent.harness.promotion_registry import VersionedPromotionRegistry

BASELINE = "a" * 40


def _candidate(candidate_id: str) -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id=candidate_id,
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title=f"candidate:{candidate_id}",
        rationale="release-candidate integration test",
        source_failure_key=f"intent:{candidate_id}",
        source_eval_ids=(f"eval-seed:{candidate_id}",),
        proposed_change={"action": "review_router_rule", "apply": False},
    )


def _ready(lifecycle: ControlledImprovementLifecycle, candidate_id: str) -> None:
    lifecycle.register(_candidate(candidate_id))
    snapshot = EvaluationSnapshot.create(candidate_id=candidate_id, corpus_size=5, passed=5, failed=0)
    lifecycle.record_evaluation(snapshot)
    lifecycle.request_approval(candidate_id)


class _Runner:
    """External experiment boundary fake; governance/lifecycle remain real."""

    def __init__(self, lifecycle: ControlledImprovementLifecycle, candidate_ids: list[str]) -> None:
        self.lifecycle = lifecycle
        self.candidate_ids = list(candidate_ids)

    def run(self, *, seeds, source_root, baseline_sha):
        candidate_id = self.candidate_ids.pop(0)
        _ready(self.lifecycle, candidate_id)
        return SimpleNamespace(
            outcomes=(
                SimpleNamespace(
                    candidate_id=candidate_id,
                    cluster_key=f"cluster:{candidate_id}",
                    outcome=EvolutionOutcome.APPROVAL_REQUIRED,
                ),
            )
        )


def _build(candidate_ids=("c1",)):
    lifecycle = ControlledImprovementLifecycle()
    registry = VersionedPromotionRegistry()
    governance = GovernedPromotionService(
        lifecycle=lifecycle,
        registry=registry,
        signer=ApprovalSigner(b"release-candidate-signing-key-0001"),
    )
    fingerprints = {
        candidate_id: (candidate_id.encode("utf-8").hex() + "f" * 64)[:64]
        for candidate_id in candidate_ids
    }
    orchestrator = ProductionEvolutionOrchestrator(
        experiment_runner=_Runner(lifecycle, list(candidate_ids)),
        lifecycle=lifecycle,
        governance=governance,
        fingerprint_resolver=lambda candidate_id: fingerprints[candidate_id],
    )
    return orchestrator, lifecycle, governance


def _run_one(orchestrator: ProductionEvolutionOrchestrator):
    sessions = orchestrator.run_experiments(seeds=(), source_root=".", baseline_sha=BASELINE)
    assert len(sessions) == 1
    return sessions[0]


def _policy():
    return MonitoringPolicy(
        rules=(MetricRule("success_rate", MetricDirection.HIGHER_IS_BETTER, 0.05),),
        min_observations=2,
        max_observations=4,
        breach_observations_required=2,
    )


def _promote_and_monitor(orchestrator: ProductionEvolutionOrchestrator, release_ref="release-1"):
    session = _run_one(orchestrator)
    approval = orchestrator.request_human_approval(session.session_id, approved_by="release-owner")
    manifest = orchestrator.promote(session.session_id, approval=approval, release_ref=release_ref)
    orchestrator.begin_monitoring(session.session_id)
    orchestrator.start_post_promotion_monitor(
        session.session_id,
        baseline_metrics=(MetricValue("success_rate", 0.95),),
        policy=_policy(),
    )
    return session, approval, manifest


def test_rc_automated_path_stops_at_human_boundary():
    orchestrator, lifecycle, _ = _build()
    session = _run_one(orchestrator)

    assert session.stage is ProductionEvolutionStage.APPROVAL_REQUIRED
    assert session.approval_id is None
    assert session.promotion_id is None
    assert session.release_ref is None
    assert lifecycle.get(session.candidate_id).state.value == "approval_required"
    assert [t.to_stage for t in session.transitions] == [
        ProductionEvolutionStage.OBSERVE,
        ProductionEvolutionStage.MINE,
        ProductionEvolutionStage.PROPOSE,
        ProductionEvolutionStage.SANDBOX,
        ProductionEvolutionStage.SHADOW,
        ProductionEvolutionStage.APPROVAL_REQUIRED,
    ]


def test_rc_happy_path_preserves_exact_identity_through_monitoring():
    orchestrator, _, _ = _build()
    original = _run_one(orchestrator)
    approval = orchestrator.request_human_approval(original.session_id, approved_by="release-owner")
    manifest = orchestrator.promote(original.session_id, approval=approval, release_ref="release-1")
    monitored = orchestrator.begin_monitoring(original.session_id)
    state = orchestrator.start_post_promotion_monitor(
        original.session_id,
        baseline_metrics=(MetricValue("success_rate", 0.95),),
        policy=_policy(),
    )

    current = orchestrator.session(original.session_id)
    assert current.stage is ProductionEvolutionStage.MONITOR
    assert current.session_id == original.session_id
    assert current.candidate_id == original.candidate_id
    assert current.candidate_fingerprint == original.candidate_fingerprint
    assert current.evaluation_id == original.evaluation_id
    assert current.approval_id == approval.approval_id
    assert current.promotion_id == manifest.promotion_id
    assert current.release_ref == manifest.release_ref == "release-1"
    assert monitored.monitor_id is None
    assert current.monitor_id == state.monitor_id
    assert state.baseline.candidate_id == current.candidate_id
    assert state.baseline.candidate_fingerprint == current.candidate_fingerprint
    assert state.baseline.promotion_id == current.promotion_id
    assert state.baseline.release_ref == current.release_ref


def test_rc_approval_replay_is_rejected_across_candidates():
    orchestrator, _, _ = _build(("candidate-a", "candidate-b"))
    first = _run_one(orchestrator)
    first_approval = orchestrator.request_human_approval(first.session_id, approved_by="release-owner")
    orchestrator.promote(first.session_id, approval=first_approval, release_ref="release-a")

    second = _run_one(orchestrator)
    orchestrator.request_human_approval(second.session_id, approved_by="release-owner")
    with pytest.raises(ValueError, match="does not belong"):
        orchestrator.promote(second.session_id, approval=first_approval, release_ref="release-b")


def test_rc_cross_session_monitor_data_cannot_be_mixed():
    orchestrator, _, _ = _build(("candidate-a", "candidate-b"))
    first, _, _ = _promote_and_monitor(orchestrator, "release-a")
    second, _, _ = _promote_and_monitor(orchestrator, "release-b")

    first_state = orchestrator.monitoring_state(first.session_id)
    second_state = orchestrator.monitoring_state(second.session_id)
    assert first_state.monitor_id != second_state.monitor_id
    assert first_state.baseline.promotion_id != second_state.baseline.promotion_id
    assert first_state.baseline.release_ref != second_state.baseline.release_ref

    with pytest.raises(ValueError):
        orchestrator.recommend_rollback(second.session_id)


def test_rc_healthy_monitoring_never_creates_rollback_authority():
    orchestrator, _, _ = _build()
    session, _, _ = _promote_and_monitor(orchestrator)

    orchestrator.record_post_promotion_observation(
        session.session_id, metrics=(MetricValue("success_rate", 0.96),)
    )
    state = orchestrator.record_post_promotion_observation(
        session.session_id, metrics=(MetricValue("success_rate", 0.95),)
    )

    assert state.latest_assessment.verdict.value == "healthy"
    current = orchestrator.session(session.session_id)
    assert current.stage is ProductionEvolutionStage.MONITOR
    assert current.rollback_recommendation_id is None
    assert current.rollback_id is None
    with pytest.raises(ValueError, match="degradation_detected"):
        orchestrator.recommend_rollback(session.session_id)


def test_rc_degradation_requires_explicit_recommendation_and_governed_rollback():
    orchestrator, lifecycle, governance = _build(("known-good", "candidate-bad"))

    # Establish an older known-good promotion as the only valid rollback target.
    known_good = _run_one(orchestrator)
    known_good_approval = orchestrator.request_human_approval(
        known_good.session_id, approved_by="release-owner"
    )
    known_good_manifest = orchestrator.promote(
        known_good.session_id,
        approval=known_good_approval,
        release_ref="release-good",
    )

    bad, _, bad_manifest = _promote_and_monitor(orchestrator, "release-bad")
    orchestrator.record_post_promotion_observation(
        bad.session_id, metrics=(MetricValue("success_rate", 0.70),)
    )
    assert orchestrator.session(bad.session_id).stage is ProductionEvolutionStage.MONITOR

    orchestrator.record_post_promotion_observation(
        bad.session_id, metrics=(MetricValue("success_rate", 0.71),)
    )
    detected = orchestrator.session(bad.session_id)
    assert detected.stage is ProductionEvolutionStage.DEGRADATION_DETECTED
    assert detected.rollback_id is None

    with pytest.raises(ValueError, match="rollback_recommended"):
        orchestrator.rollback(
            bad.session_id,
            target_promotion_id=known_good_manifest.promotion_id,
            reason="too early",
            rolled_back_by="release-owner",
        )

    recommendation = orchestrator.recommend_rollback(bad.session_id)
    recommended = orchestrator.session(bad.session_id)
    assert recommended.stage is ProductionEvolutionStage.ROLLBACK_RECOMMENDED
    assert recommended.rollback_recommendation_id == recommendation.recommendation_id
    assert recommended.rollback_id is None

    record = orchestrator.rollback(
        bad.session_id,
        target_promotion_id=known_good_manifest.promotion_id,
        reason="confirmed post-promotion degradation",
        rolled_back_by="release-owner",
    )
    final = orchestrator.session(bad.session_id)
    assert record.promotion_id == bad_manifest.promotion_id
    assert final.stage is ProductionEvolutionStage.ROLLED_BACK
    assert final.rollback_id == record.rollback_id
    assert lifecycle.get(bad.candidate_id).state.value == "rolled_back"


def test_rc_terminal_rejection_cannot_reenter_approval_or_promotion():
    orchestrator, _, _ = _build()
    session = _run_one(orchestrator)
    rejected = orchestrator.reject(session.session_id, reason="release owner rejected candidate")

    assert rejected.stage is ProductionEvolutionStage.REJECTED
    assert rejected.terminal is True
    with pytest.raises(ValueError):
        orchestrator.request_human_approval(session.session_id, approved_by="release-owner")
    with pytest.raises(ValueError):
        orchestrator.begin_monitoring(session.session_id)


def test_rc_monitor_provider_failure_is_fail_closed_and_never_auto_rolls_back():
    orchestrator, _, _ = _build()
    session, _, _ = _promote_and_monitor(orchestrator)

    state = orchestrator.record_post_promotion_observation(
        session.session_id,
        metrics=(),
        provider_error="metrics provider unavailable",
    )
    assert state.latest_assessment.verdict.value == "provider_error"
    current = orchestrator.session(session.session_id)
    assert current.stage is ProductionEvolutionStage.DEGRADATION_DETECTED
    assert current.rollback_id is None
    assert current.rollback_recommendation_id is None


def test_rc_monitoring_budget_is_bounded():
    orchestrator, _, _ = _build()
    session, _, _ = _promote_and_monitor(orchestrator)

    for value in (0.96, 0.96, 0.96, 0.96):
        orchestrator.record_post_promotion_observation(
            session.session_id, metrics=(MetricValue("success_rate", value),)
        )

    state = orchestrator.monitoring_state(session.session_id)
    assert len(state.observations) == 4
    with pytest.raises(ValueError):
        orchestrator.record_post_promotion_observation(
            session.session_id, metrics=(MetricValue("success_rate", 0.96),)
        )


def test_rc_public_automated_components_have_no_direct_production_mutation_methods():
    from po_agent.harness.evolution_loop import AutonomousEvolutionLoop
    from po_agent.harness.evolution_loop_memory import MemoryIntegratedAutonomousEvolutionLoop
    from po_agent.harness.post_promotion_monitoring import PostPromotionMonitor
    from po_agent.harness.shadow_evaluation import ShadowEvaluator
    from po_agent.harness.skill_forge import SkillForge

    forbidden = {"promote", "rollback", "mark_promoted", "apply_release"}
    for cls in (
        AutonomousEvolutionLoop,
        MemoryIntegratedAutonomousEvolutionLoop,
        PostPromotionMonitor,
        ShadowEvaluator,
        SkillForge,
    ):
        public_names = {name for name in dir(cls) if not name.startswith("_")}
        assert forbidden.isdisjoint(public_names), f"{cls.__name__} exposes production mutation authority"
