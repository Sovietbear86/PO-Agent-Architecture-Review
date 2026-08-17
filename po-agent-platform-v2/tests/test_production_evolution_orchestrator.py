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
FINGERPRINT = "b" * 64


def _candidate(candidate_id: str) -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id=candidate_id,
        created_at="2026-08-17T00:00:00+00:00",
        kind="routing_rule",
        title="candidate",
        rationale="test",
        source_failure_key="intent:test",
        source_eval_ids=("eval-seed",),
        proposed_change={"action": "review_router_rule", "apply": False},
    )


def _ready(lifecycle: ControlledImprovementLifecycle, candidate_id: str) -> None:
    lifecycle.register(_candidate(candidate_id))
    snapshot = EvaluationSnapshot.create(candidate_id=candidate_id, corpus_size=3, passed=3, failed=0)
    lifecycle.record_evaluation(snapshot)
    lifecycle.request_approval(candidate_id)


class _Runner:
    def __init__(self, lifecycle: ControlledImprovementLifecycle, candidate_ids: list[str]) -> None:
        self.lifecycle = lifecycle
        self.candidate_ids = list(candidate_ids)

    def run(self, *, seeds, source_root, baseline_sha):
        candidate_id = self.candidate_ids.pop(0)
        _ready(self.lifecycle, candidate_id)
        outcome = SimpleNamespace(
            candidate_id=candidate_id,
            cluster_key=f"cluster:{candidate_id}",
            outcome=EvolutionOutcome.APPROVAL_REQUIRED,
        )
        return SimpleNamespace(outcomes=(outcome,))


def _build(candidate_ids=("c1",)):
    lifecycle = ControlledImprovementLifecycle()
    registry = VersionedPromotionRegistry()
    governance = GovernedPromotionService(lifecycle=lifecycle, registry=registry, signer=ApprovalSigner(b"k" * 32))
    fingerprints = {candidate_id: FINGERPRINT[:-1] + str(index % 10) for index, candidate_id in enumerate(candidate_ids)}
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


def _monitor_policy():
    return MonitoringPolicy(
        rules=(MetricRule("success_rate", MetricDirection.HIGHER_IS_BETTER, 0.05),),
        min_observations=2,
        max_observations=4,
        breach_observations_required=2,
    )


def test_automated_path_stops_at_human_approval_boundary():
    orchestrator, lifecycle, _ = _build()
    session = _run_one(orchestrator)
    assert session.stage is ProductionEvolutionStage.APPROVAL_REQUIRED
    assert lifecycle.get(session.candidate_id).state.value == "approval_required"
    assert session.approval_id is None
    assert session.promotion_id is None
    assert [item.to_stage for item in session.transitions] == [
        ProductionEvolutionStage.OBSERVE,
        ProductionEvolutionStage.MINE,
        ProductionEvolutionStage.PROPOSE,
        ProductionEvolutionStage.SANDBOX,
        ProductionEvolutionStage.SHADOW,
        ProductionEvolutionStage.APPROVAL_REQUIRED,
    ]


def test_signed_approval_is_required_before_promotion():
    orchestrator, _, _ = _build()
    session = _run_one(orchestrator)
    with pytest.raises(ValueError, match="approved"):
        orchestrator.promote(session.session_id, approval=SimpleNamespace(approval_id="fake"), release_ref="release-1")
    approval = orchestrator.request_human_approval(session.session_id, approved_by="owner")
    approved = orchestrator.session(session.session_id)
    assert approved.stage is ProductionEvolutionStage.APPROVED
    assert approved.approval_id == approval.approval_id


def test_promotion_uses_exact_session_approval_and_binding():
    orchestrator, lifecycle, _ = _build()
    session = _run_one(orchestrator)
    approval = orchestrator.request_human_approval(session.session_id, approved_by="owner")
    manifest = orchestrator.promote(session.session_id, approval=approval, release_ref="release-1")
    promoted = orchestrator.session(session.session_id)
    assert promoted.stage is ProductionEvolutionStage.PROMOTED
    assert promoted.promotion_id == manifest.promotion_id
    assert promoted.release_ref == "release-1"
    assert lifecycle.get(session.candidate_id).state.value == "promoted"


def test_monitoring_cannot_start_before_governed_promotion():
    orchestrator, _, _ = _build()
    session = _run_one(orchestrator)
    with pytest.raises(ValueError, match="promoted"):
        orchestrator.begin_monitoring(session.session_id)


def test_promotion_approval_cannot_be_replayed_across_sessions():
    orchestrator, _, _ = _build(("c1", "c2"))
    first = _run_one(orchestrator)
    first_approval = orchestrator.request_human_approval(first.session_id, approved_by="owner")
    orchestrator.promote(first.session_id, approval=first_approval, release_ref="release-1")
    second = _run_one(orchestrator)
    orchestrator.request_human_approval(second.session_id, approved_by="owner")
    with pytest.raises(ValueError, match="does not belong"):
        orchestrator.promote(second.session_id, approval=first_approval, release_ref="release-2")


def test_reject_is_terminal_and_cannot_later_promote():
    orchestrator, lifecycle, _ = _build()
    session = _run_one(orchestrator)
    rejected = orchestrator.reject(session.session_id, reason="human rejected")
    assert rejected.stage is ProductionEvolutionStage.REJECTED
    assert rejected.terminal is True
    assert lifecycle.get(session.candidate_id).state.value == "rejected"
    with pytest.raises(ValueError):
        orchestrator.request_human_approval(session.session_id, approved_by="owner")


def test_full_governed_path_requires_monitor_evidence_before_rollback():
    orchestrator, lifecycle, governance = _build(("c1", "c2"))
    _ready(lifecycle, "known-good")
    known_good_record = lifecycle.get("known-good")
    known_good_binding = PromotionBinding(
        baseline_sha="0" * 40,
        candidate_id="known-good",
        candidate_fingerprint="1" * 64,
        evaluation_id=known_good_record.latest_evaluation.evaluation_id,
    )
    known_good_approval = governance.issue_human_approval(binding=known_good_binding, approved_by="owner")
    known_good = governance.promote(
        approval=known_good_approval,
        expected_binding=known_good_binding,
        release_ref="release-0",
    )

    session = _run_one(orchestrator)
    approval = orchestrator.request_human_approval(session.session_id, approved_by="owner")
    manifest = orchestrator.promote(session.session_id, approval=approval, release_ref="release-1")
    orchestrator.begin_monitoring(session.session_id)
    orchestrator.start_post_promotion_monitor(
        session.session_id,
        baseline_metrics=(MetricValue("success_rate", 0.95),),
        policy=_monitor_policy(),
    )
    with pytest.raises(ValueError, match="rollback_recommended"):
        orchestrator.rollback(
            session.session_id,
            target_promotion_id=known_good.promotion_id,
            reason="too early",
            rolled_back_by="owner",
        )

    orchestrator.record_post_promotion_observation(
        session.session_id, metrics=(MetricValue("success_rate", 0.70),)
    )
    orchestrator.record_post_promotion_observation(
        session.session_id, metrics=(MetricValue("success_rate", 0.72),)
    )
    detected = orchestrator.session(session.session_id)
    assert detected.stage is ProductionEvolutionStage.DEGRADATION_DETECTED

    recommendation = orchestrator.recommend_rollback(session.session_id)
    recommended = orchestrator.session(session.session_id)
    assert recommended.stage is ProductionEvolutionStage.ROLLBACK_RECOMMENDED
    assert recommended.rollback_recommendation_id == recommendation.recommendation_id

    rollback = orchestrator.rollback(
        session.session_id,
        target_promotion_id=known_good.promotion_id,
        reason="post-promotion degradation",
        rolled_back_by="owner",
    )
    final = orchestrator.session(session.session_id)
    assert rollback.promotion_id == manifest.promotion_id
    assert final.stage is ProductionEvolutionStage.ROLLED_BACK
    assert final.rollback_id == rollback.rollback_id
    assert lifecycle.get(session.candidate_id).state.value == "rolled_back"


def test_healthy_monitoring_never_creates_rollback_recommendation():
    orchestrator, _, _ = _build()
    session = _run_one(orchestrator)
    approval = orchestrator.request_human_approval(session.session_id, approved_by="owner")
    orchestrator.promote(session.session_id, approval=approval, release_ref="release-1")
    orchestrator.begin_monitoring(session.session_id)
    orchestrator.start_post_promotion_monitor(
        session.session_id,
        baseline_metrics=(MetricValue("success_rate", 0.95),),
        policy=_monitor_policy(),
    )
    orchestrator.record_post_promotion_observation(session.session_id, metrics=(MetricValue("success_rate", 0.96),))
    state = orchestrator.record_post_promotion_observation(
        session.session_id, metrics=(MetricValue("success_rate", 0.95),)
    )
    assert state.latest_assessment.verdict.value == "healthy"
    assert orchestrator.session(session.session_id).stage is ProductionEvolutionStage.MONITOR
    with pytest.raises(ValueError, match="degradation_detected"):
        orchestrator.recommend_rollback(session.session_id)


def test_empty_fingerprint_fails_closed_before_human_approval_session_is_created():
    lifecycle = ControlledImprovementLifecycle()
    governance = GovernedPromotionService(
        lifecycle=lifecycle,
        registry=VersionedPromotionRegistry(),
        signer=ApprovalSigner(b"k" * 32),
    )
    orchestrator = ProductionEvolutionOrchestrator(
        experiment_runner=_Runner(lifecycle, ["c1"]),
        lifecycle=lifecycle,
        governance=governance,
        fingerprint_resolver=lambda candidate_id: "",
    )
    with pytest.raises(ValueError, match="empty fingerprint"):
        _run_one(orchestrator)
