"""High-level production supervisor for the governed Harness evolution path.

The supervisor intentionally has no deployment authority of its own. It coordinates
existing production runtime operations, keeps a compact cycle registry, and makes
human boundaries explicit. Autonomous work may discover/evaluate candidates, but
approval, promotion and rollback always require explicit caller actions.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Iterable, Protocol, Sequence

from .eval_store import EvalSeed
from .governed_promotion import GovernedRollbackRecord, PromotionManifest, SignedPromotionApproval
from .post_promotion_monitoring import (
    MetricValue,
    MonitoringPolicy,
    PostPromotionMonitorState,
    RollbackRecommendation,
)
from .production_evolution_orchestrator import ProductionEvolutionSession, ProductionEvolutionStage


class SupervisorCycleState(str, Enum):
    DISCOVERED = "discovered"
    AWAITING_HUMAN_APPROVAL = "awaiting_human_approval"
    HUMAN_APPROVED = "human_approved"
    PROMOTED = "promoted"
    MONITORING = "monitoring"
    DEGRADATION_DETECTED = "degradation_detected"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    ROLLED_BACK = "rolled_back"
    TERMINAL = "terminal"


@dataclass(frozen=True)
class SupervisedEvolutionCycle:
    cycle_id: str
    session_id: str
    candidate_id: str
    cluster_key: str
    state: SupervisorCycleState
    production_stage: ProductionEvolutionStage
    approval_id: str | None = None
    promotion_id: str | None = None
    release_ref: str | None = None
    rollback_recommendation_id: str | None = None
    rollback_id: str | None = None


class ProductionRuntimePort(Protocol):
    def run_experiments(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> tuple[ProductionEvolutionSession, ...]: ...

    def request_human_approval(
        self,
        session_id: str,
        *,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval: ...

    def promote(
        self,
        session_id: str,
        *,
        approval: SignedPromotionApproval,
        release_ref: str,
    ) -> PromotionManifest: ...

    def begin_monitoring(self, session_id: str) -> ProductionEvolutionSession: ...

    def start_post_promotion_monitor(
        self,
        session_id: str,
        *,
        baseline_metrics: Iterable[MetricValue],
        policy: MonitoringPolicy,
    ) -> PostPromotionMonitorState: ...

    def record_post_promotion_observation(
        self,
        session_id: str,
        *,
        metrics: Iterable[MetricValue],
        provider_error: str | None = None,
    ) -> PostPromotionMonitorState: ...

    def recommend_rollback(
        self,
        session_id: str,
        *,
        reason: str | None = None,
    ) -> RollbackRecommendation: ...

    def rollback(
        self,
        session_id: str,
        *,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord: ...


class ProductionEvolutionSupervisor:
    """Canonical top-level coordinator for production evolution cycles.

    Safety properties:
    - experiment execution may be automated;
    - approval can only be created by explicit ``approve``;
    - promotion can only happen via explicit ``promote`` with stored approval;
    - monitoring can recommend rollback but never execute it;
    - rollback can only happen via explicit ``rollback``.
    """

    def __init__(self, runtime: ProductionRuntimePort) -> None:
        if runtime is None:
            raise ValueError("runtime is required")
        self._runtime = runtime
        self._cycles: dict[str, SupervisedEvolutionCycle] = {}
        self._approvals: dict[str, SignedPromotionApproval] = {}

    def run_cycle_discovery(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> tuple[SupervisedEvolutionCycle, ...]:
        sessions = self._runtime.run_experiments(
            seeds=seeds,
            source_root=source_root,
            baseline_sha=baseline_sha,
        )
        cycles: list[SupervisedEvolutionCycle] = []
        for session in sessions:
            cycle = SupervisedEvolutionCycle(
                cycle_id=session.session_id,
                session_id=session.session_id,
                candidate_id=session.candidate_id,
                cluster_key=session.cluster_key,
                state=self._state_for_stage(session.stage),
                production_stage=session.stage,
                approval_id=session.approval_id,
                promotion_id=session.promotion_id,
                release_ref=session.release_ref,
                rollback_recommendation_id=session.rollback_recommendation_id,
                rollback_id=session.rollback_id,
            )
            self._cycles[cycle.cycle_id] = cycle
            cycles.append(cycle)
        return tuple(cycles)

    def cycle(self, cycle_id: str) -> SupervisedEvolutionCycle | None:
        return self._cycles.get(cycle_id)

    def cycles(self) -> tuple[SupervisedEvolutionCycle, ...]:
        return tuple(self._cycles.values())

    def pending_approvals(self) -> tuple[SupervisedEvolutionCycle, ...]:
        return tuple(
            cycle
            for cycle in self._cycles.values()
            if cycle.state is SupervisorCycleState.AWAITING_HUMAN_APPROVAL
        )

    def approve(
        self,
        cycle_id: str,
        *,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.AWAITING_HUMAN_APPROVAL)
        if not str(approved_by).strip():
            raise ValueError("approved_by is required")
        approval = self._runtime.request_human_approval(
            cycle.session_id,
            approved_by=approved_by,
            note=note,
        )
        self._approvals[cycle_id] = approval
        self._store(
            replace(
                cycle,
                state=SupervisorCycleState.HUMAN_APPROVED,
                production_stage=ProductionEvolutionStage.APPROVED,
                approval_id=approval.approval_id,
            )
        )
        return approval

    def promote(self, cycle_id: str, *, release_ref: str) -> PromotionManifest:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.HUMAN_APPROVED)
        if not str(release_ref).strip():
            raise ValueError("release_ref is required")
        approval = self._approvals.get(cycle_id)
        if approval is None or approval.approval_id != cycle.approval_id:
            raise ValueError("cycle has no matching signed human approval")
        manifest = self._runtime.promote(
            cycle.session_id,
            approval=approval,
            release_ref=release_ref,
        )
        session = self._runtime.begin_monitoring(cycle.session_id)
        self._store(
            replace(
                cycle,
                state=SupervisorCycleState.MONITORING,
                production_stage=session.stage,
                promotion_id=manifest.promotion_id,
                release_ref=manifest.release_ref,
            )
        )
        return manifest

    def start_monitoring(
        self,
        cycle_id: str,
        *,
        baseline_metrics: Iterable[MetricValue],
        policy: MonitoringPolicy,
    ) -> PostPromotionMonitorState:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.MONITORING)
        return self._runtime.start_post_promotion_monitor(
            cycle.session_id,
            baseline_metrics=baseline_metrics,
            policy=policy,
        )

    def observe(
        self,
        cycle_id: str,
        *,
        metrics: Iterable[MetricValue],
        provider_error: str | None = None,
    ) -> PostPromotionMonitorState:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.MONITORING)
        state = self._runtime.record_post_promotion_observation(
            cycle.session_id,
            metrics=metrics,
            provider_error=provider_error,
        )
        if state.latest_assessment.verdict.value in {"degradation_detected", "provider_error"}:
            self._store(
                replace(
                    cycle,
                    state=SupervisorCycleState.DEGRADATION_DETECTED,
                    production_stage=ProductionEvolutionStage.DEGRADATION_DETECTED,
                )
            )
        return state

    def recommend_rollback(
        self,
        cycle_id: str,
        *,
        reason: str | None = None,
    ) -> RollbackRecommendation:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.DEGRADATION_DETECTED)
        recommendation = self._runtime.recommend_rollback(cycle.session_id, reason=reason)
        self._store(
            replace(
                cycle,
                state=SupervisorCycleState.ROLLBACK_RECOMMENDED,
                production_stage=ProductionEvolutionStage.ROLLBACK_RECOMMENDED,
                rollback_recommendation_id=recommendation.recommendation_id,
            )
        )
        return recommendation

    def rollback(
        self,
        cycle_id: str,
        *,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord:
        cycle = self._require_cycle(cycle_id)
        self._require_state(cycle, SupervisorCycleState.ROLLBACK_RECOMMENDED)
        if not str(reason).strip():
            raise ValueError("rollback reason is required")
        if not str(rolled_back_by).strip():
            raise ValueError("rolled_back_by is required")
        record = self._runtime.rollback(
            cycle.session_id,
            target_promotion_id=target_promotion_id,
            reason=reason,
            rolled_back_by=rolled_back_by,
        )
        self._store(
            replace(
                cycle,
                state=SupervisorCycleState.ROLLED_BACK,
                production_stage=ProductionEvolutionStage.ROLLED_BACK,
                rollback_id=record.rollback_id,
            )
        )
        return record

    def _require_cycle(self, cycle_id: str) -> SupervisedEvolutionCycle:
        cycle = self._cycles.get(cycle_id)
        if cycle is None:
            raise ValueError(f"unknown supervised evolution cycle: {cycle_id}")
        return cycle

    @staticmethod
    def _require_state(cycle: SupervisedEvolutionCycle, expected: SupervisorCycleState) -> None:
        if cycle.state is not expected:
            raise ValueError(
                f"supervisor cycle {cycle.cycle_id} is {cycle.state.value}, expected {expected.value}"
            )

    def _store(self, cycle: SupervisedEvolutionCycle) -> SupervisedEvolutionCycle:
        self._cycles[cycle.cycle_id] = cycle
        return cycle

    @staticmethod
    def _state_for_stage(stage: ProductionEvolutionStage) -> SupervisorCycleState:
        if stage is ProductionEvolutionStage.APPROVAL_REQUIRED:
            return SupervisorCycleState.AWAITING_HUMAN_APPROVAL
        if stage is ProductionEvolutionStage.APPROVED:
            return SupervisorCycleState.HUMAN_APPROVED
        if stage is ProductionEvolutionStage.PROMOTED:
            return SupervisorCycleState.PROMOTED
        if stage is ProductionEvolutionStage.MONITOR:
            return SupervisorCycleState.MONITORING
        if stage is ProductionEvolutionStage.DEGRADATION_DETECTED:
            return SupervisorCycleState.DEGRADATION_DETECTED
        if stage is ProductionEvolutionStage.ROLLBACK_RECOMMENDED:
            return SupervisorCycleState.ROLLBACK_RECOMMENDED
        if stage is ProductionEvolutionStage.ROLLED_BACK:
            return SupervisorCycleState.ROLLED_BACK
        if stage in {
            ProductionEvolutionStage.REJECTED,
            ProductionEvolutionStage.BLOCKED,
            ProductionEvolutionStage.FAILED,
            ProductionEvolutionStage.BUDGET_EXHAUSTED,
            ProductionEvolutionStage.NEEDS_MORE_EVIDENCE,
        }:
            return SupervisorCycleState.TERMINAL
        return SupervisorCycleState.DISCOVERED
