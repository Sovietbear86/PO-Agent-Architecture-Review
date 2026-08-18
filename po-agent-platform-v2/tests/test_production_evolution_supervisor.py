from __future__ import annotations

from types import SimpleNamespace

import pytest

from po_agent.harness.production_evolution_orchestrator import (
    ProductionEvolutionSession,
    ProductionEvolutionStage,
)
from po_agent.harness.production_evolution_supervisor import (
    ProductionEvolutionSupervisor,
    SupervisorCycleState,
)


def _session(stage: ProductionEvolutionStage, *, session_id: str = "s1") -> ProductionEvolutionSession:
    return ProductionEvolutionSession(
        session_id=session_id,
        baseline_sha="b" * 40,
        candidate_id="candidate-1",
        cluster_key="cluster-1",
        evaluation_id="eval-1",
        candidate_fingerprint="f" * 64,
        stage=stage,
        transitions=(),
    )


class _FakeRuntime:
    def __init__(self, sessions: tuple[ProductionEvolutionSession, ...]) -> None:
        self.sessions = sessions
        self.calls: list[tuple[str, str]] = []

    def run_experiments(self, **kwargs):
        self.calls.append(("run_experiments", kwargs["baseline_sha"]))
        return self.sessions

    def request_human_approval(self, session_id: str, **kwargs):
        self.calls.append(("request_human_approval", session_id))
        return SimpleNamespace(approval_id="approval-1")

    def promote(self, session_id: str, **kwargs):
        self.calls.append(("promote", session_id))
        return SimpleNamespace(promotion_id="promotion-1", release_ref=kwargs["release_ref"])

    def begin_monitoring(self, session_id: str):
        self.calls.append(("begin_monitoring", session_id))
        session = _session(ProductionEvolutionStage.MONITOR, session_id=session_id)
        return session

    def start_post_promotion_monitor(self, session_id: str, **kwargs):
        self.calls.append(("start_monitor", session_id))
        return SimpleNamespace(monitor_id="monitor-1")

    def record_post_promotion_observation(self, session_id: str, **kwargs):
        self.calls.append(("observe", session_id))
        verdict = SimpleNamespace(value="degradation_detected")
        return SimpleNamespace(latest_assessment=SimpleNamespace(verdict=verdict))

    def recommend_rollback(self, session_id: str, **kwargs):
        self.calls.append(("recommend_rollback", session_id))
        return SimpleNamespace(recommendation_id="recommendation-1")

    def rollback(self, session_id: str, **kwargs):
        self.calls.append(("rollback", session_id))
        return SimpleNamespace(rollback_id="rollback-1")


def test_discovery_maps_approval_boundary_without_crossing_it(tmp_path) -> None:
    runtime = _FakeRuntime((_session(ProductionEvolutionStage.APPROVAL_REQUIRED),))
    supervisor = ProductionEvolutionSupervisor(runtime)

    cycles = supervisor.run_cycle_discovery(
        seeds=(),
        source_root=tmp_path,
        baseline_sha="b" * 40,
    )

    assert len(cycles) == 1
    assert cycles[0].state is SupervisorCycleState.AWAITING_HUMAN_APPROVAL
    assert supervisor.pending_approvals() == cycles
    assert [name for name, _ in runtime.calls] == ["run_experiments"]


def test_supervisor_cannot_promote_without_explicit_human_approval(tmp_path) -> None:
    runtime = _FakeRuntime((_session(ProductionEvolutionStage.APPROVAL_REQUIRED),))
    supervisor = ProductionEvolutionSupervisor(runtime)
    cycle = supervisor.run_cycle_discovery(seeds=(), source_root=tmp_path, baseline_sha="b" * 40)[0]

    with pytest.raises(ValueError, match="expected human_approved"):
        supervisor.promote(cycle.cycle_id, release_ref="release/v1")

    assert all(name != "promote" for name, _ in runtime.calls)


def test_explicit_approval_then_promotion_enters_monitoring(tmp_path) -> None:
    runtime = _FakeRuntime((_session(ProductionEvolutionStage.APPROVAL_REQUIRED),))
    supervisor = ProductionEvolutionSupervisor(runtime)
    cycle = supervisor.run_cycle_discovery(seeds=(), source_root=tmp_path, baseline_sha="b" * 40)[0]

    approval = supervisor.approve(cycle.cycle_id, approved_by="victor", note="reviewed")
    assert approval.approval_id == "approval-1"
    assert supervisor.cycle(cycle.cycle_id).state is SupervisorCycleState.HUMAN_APPROVED

    manifest = supervisor.promote(cycle.cycle_id, release_ref="release/v1")
    assert manifest.promotion_id == "promotion-1"
    updated = supervisor.cycle(cycle.cycle_id)
    assert updated.state is SupervisorCycleState.MONITORING
    assert updated.production_stage is ProductionEvolutionStage.MONITOR
    assert [name for name, _ in runtime.calls][-3:] == [
        "request_human_approval",
        "promote",
        "begin_monitoring",
    ]


def test_monitoring_can_recommend_but_not_execute_rollback(tmp_path) -> None:
    runtime = _FakeRuntime((_session(ProductionEvolutionStage.APPROVAL_REQUIRED),))
    supervisor = ProductionEvolutionSupervisor(runtime)
    cycle = supervisor.run_cycle_discovery(seeds=(), source_root=tmp_path, baseline_sha="b" * 40)[0]
    supervisor.approve(cycle.cycle_id, approved_by="human")
    supervisor.promote(cycle.cycle_id, release_ref="release/v1")

    supervisor.observe(cycle.cycle_id, metrics=())
    assert supervisor.cycle(cycle.cycle_id).state is SupervisorCycleState.DEGRADATION_DETECTED

    recommendation = supervisor.recommend_rollback(cycle.cycle_id, reason="regression")
    assert recommendation.recommendation_id == "recommendation-1"
    assert supervisor.cycle(cycle.cycle_id).state is SupervisorCycleState.ROLLBACK_RECOMMENDED
    assert all(name != "rollback" for name, _ in runtime.calls)


def test_rollback_requires_explicit_actor_and_reason(tmp_path) -> None:
    runtime = _FakeRuntime((_session(ProductionEvolutionStage.APPROVAL_REQUIRED),))
    supervisor = ProductionEvolutionSupervisor(runtime)
    cycle = supervisor.run_cycle_discovery(seeds=(), source_root=tmp_path, baseline_sha="b" * 40)[0]
    supervisor.approve(cycle.cycle_id, approved_by="human")
    supervisor.promote(cycle.cycle_id, release_ref="release/v1")
    supervisor.observe(cycle.cycle_id, metrics=())
    supervisor.recommend_rollback(cycle.cycle_id)

    with pytest.raises(ValueError, match="rollback reason"):
        supervisor.rollback(
            cycle.cycle_id,
            target_promotion_id="previous",
            reason="",
            rolled_back_by="human",
        )
    with pytest.raises(ValueError, match="rolled_back_by"):
        supervisor.rollback(
            cycle.cycle_id,
            target_promotion_id="previous",
            reason="degraded",
            rolled_back_by="",
        )

    record = supervisor.rollback(
        cycle.cycle_id,
        target_promotion_id="previous",
        reason="degraded",
        rolled_back_by="human",
    )
    assert record.rollback_id == "rollback-1"
    assert supervisor.cycle(cycle.cycle_id).state is SupervisorCycleState.ROLLED_BACK


def test_terminal_experiment_outcomes_remain_terminal(tmp_path) -> None:
    runtime = _FakeRuntime(
        (
            _session(ProductionEvolutionStage.BLOCKED, session_id="blocked"),
            _session(ProductionEvolutionStage.FAILED, session_id="failed"),
        )
    )
    supervisor = ProductionEvolutionSupervisor(runtime)

    cycles = supervisor.run_cycle_discovery(seeds=(), source_root=tmp_path, baseline_sha="b" * 40)
    assert {cycle.state for cycle in cycles} == {SupervisorCycleState.TERMINAL}
    assert supervisor.pending_approvals() == ()


def test_public_supervisor_has_no_automatic_mutation_methods() -> None:
    supervisor = ProductionEvolutionSupervisor(_FakeRuntime(()))
    assert not hasattr(supervisor, "auto_approve")
    assert not hasattr(supervisor, "auto_promote")
    assert not hasattr(supervisor, "auto_rollback")
    assert not hasattr(supervisor, "apply_release")
