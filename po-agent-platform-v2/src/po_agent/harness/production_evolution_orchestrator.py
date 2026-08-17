"""Canonical production orchestration for governed Harness evolution.

This module connects the bounded autonomous experiment loop with human-gated
promotion and bounded post-promotion health monitoring.  The production path is:

OBSERVE -> MINE -> PROPOSE -> SANDBOX -> SHADOW -> APPROVAL_REQUIRED
        -> APPROVED -> PROMOTED -> MONITOR
        -> DEGRADATION_DETECTED -> ROLLBACK_RECOMMENDED -> ROLLED_BACK

Healthy monitoring remains in MONITOR.  Detection and recommendation never have
deployment authority: rollback is still delegated exclusively to
GovernedPromotionService.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Protocol, Sequence

from .eval_store import EvalSeed
from .evolution_lifecycle import ControlledImprovementLifecycle, LifecycleState
from .evolution_loop import AutonomousEvolutionReport, EvolutionOutcome
from .governed_promotion import (
    GovernedPromotionService,
    GovernedRollbackRecord,
    PromotionBinding,
    PromotionManifest,
    SignedPromotionApproval,
)
from .post_promotion_monitoring import (
    HealthObservation,
    MetricValue,
    MonitoringBaseline,
    MonitoringPolicy,
    MonitoringVerdict,
    PostPromotionMonitor,
    PostPromotionMonitorState,
    RollbackRecommendation,
)


class ProductionEvolutionStage(str, Enum):
    OBSERVE = "observe"
    MINE = "mine"
    PROPOSE = "propose"
    SANDBOX = "sandbox"
    SHADOW = "shadow"
    APPROVAL_REQUIRED = "approval_required"
    APPROVED = "approved"
    PROMOTED = "promoted"
    MONITOR = "monitor"
    DEGRADATION_DETECTED = "degradation_detected"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    ROLLED_BACK = "rolled_back"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    FAILED = "failed"
    BUDGET_EXHAUSTED = "budget_exhausted"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


TERMINAL_STAGES = frozenset(
    {
        ProductionEvolutionStage.ROLLED_BACK,
        ProductionEvolutionStage.REJECTED,
        ProductionEvolutionStage.BLOCKED,
        ProductionEvolutionStage.FAILED,
        ProductionEvolutionStage.BUDGET_EXHAUSTED,
        ProductionEvolutionStage.NEEDS_MORE_EVIDENCE,
    }
)


@dataclass(frozen=True)
class ProductionEvolutionTransition:
    from_stage: ProductionEvolutionStage | None
    to_stage: ProductionEvolutionStage
    reason: str


@dataclass(frozen=True)
class ProductionEvolutionSession:
    session_id: str
    baseline_sha: str
    candidate_id: str
    cluster_key: str
    evaluation_id: str | None
    candidate_fingerprint: str | None
    stage: ProductionEvolutionStage
    transitions: tuple[ProductionEvolutionTransition, ...]
    approval_id: str | None = None
    promotion_id: str | None = None
    release_ref: str | None = None
    monitor_id: str | None = None
    rollback_recommendation_id: str | None = None
    rollback_id: str | None = None

    @property
    def terminal(self) -> bool:
        return self.stage in TERMINAL_STAGES


class EvolutionExperimentRunner(Protocol):
    def run(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> AutonomousEvolutionReport: ...


FingerprintResolver = Callable[[str], str]


class ProductionEvolutionOrchestrator:
    """Trusted state-machine facade for the full production evolution path."""

    _ALLOWED_TRANSITIONS: dict[ProductionEvolutionStage, frozenset[ProductionEvolutionStage]] = {
        ProductionEvolutionStage.APPROVAL_REQUIRED: frozenset(
            {ProductionEvolutionStage.APPROVED, ProductionEvolutionStage.REJECTED}
        ),
        ProductionEvolutionStage.APPROVED: frozenset(
            {ProductionEvolutionStage.PROMOTED, ProductionEvolutionStage.REJECTED}
        ),
        ProductionEvolutionStage.PROMOTED: frozenset({ProductionEvolutionStage.MONITOR}),
        ProductionEvolutionStage.MONITOR: frozenset({ProductionEvolutionStage.DEGRADATION_DETECTED}),
        ProductionEvolutionStage.DEGRADATION_DETECTED: frozenset(
            {ProductionEvolutionStage.ROLLBACK_RECOMMENDED}
        ),
        ProductionEvolutionStage.ROLLBACK_RECOMMENDED: frozenset(
            {ProductionEvolutionStage.ROLLED_BACK}
        ),
    }

    def __init__(
        self,
        *,
        experiment_runner: EvolutionExperimentRunner,
        lifecycle: ControlledImprovementLifecycle,
        governance: GovernedPromotionService,
        fingerprint_resolver: FingerprintResolver,
        post_promotion_monitor: PostPromotionMonitor | None = None,
    ) -> None:
        self._experiment_runner = experiment_runner
        self._lifecycle = lifecycle
        self._governance = governance
        self._fingerprint_resolver = fingerprint_resolver
        self._post_promotion_monitor = post_promotion_monitor or PostPromotionMonitor()
        self._sessions: dict[str, ProductionEvolutionSession] = {}

    def run_experiments(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> tuple[ProductionEvolutionSession, ...]:
        if not baseline_sha.strip():
            raise ValueError("baseline_sha is required")
        report = self._experiment_runner.run(
            seeds=seeds,
            source_root=source_root,
            baseline_sha=baseline_sha,
        )
        sessions: list[ProductionEvolutionSession] = []
        for outcome in report.outcomes:
            stage = self._stage_for_outcome(outcome.outcome)
            evaluation_id: str | None = None
            fingerprint: str | None = None
            transitions = self._automated_trace(stage)
            if outcome.candidate_id:
                record = self._lifecycle.get(outcome.candidate_id)
                if record is not None and record.latest_evaluation is not None:
                    evaluation_id = record.latest_evaluation.evaluation_id
                if stage is ProductionEvolutionStage.APPROVAL_REQUIRED:
                    if record is None or record.state is not LifecycleState.APPROVAL_REQUIRED:
                        raise ValueError("experiment reported approval_required without matching lifecycle state")
                    fingerprint = self._required_fingerprint(outcome.candidate_id)
            session = ProductionEvolutionSession(
                session_id=str(uuid.uuid4()),
                baseline_sha=baseline_sha.strip(),
                candidate_id=outcome.candidate_id,
                cluster_key=outcome.cluster_key,
                evaluation_id=evaluation_id,
                candidate_fingerprint=fingerprint,
                stage=stage,
                transitions=transitions,
            )
            self._sessions[session.session_id] = session
            sessions.append(session)
        return tuple(sessions)

    def session(self, session_id: str) -> ProductionEvolutionSession | None:
        return self._sessions.get(session_id)

    def monitoring_state(self, session_id: str) -> PostPromotionMonitorState | None:
        session = self._require_session(session_id)
        if session.monitor_id is None:
            return None
        return self._post_promotion_monitor.state(session.monitor_id)

    def request_human_approval(
        self,
        session_id: str,
        *,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.APPROVAL_REQUIRED)
        approval = self._governance.issue_human_approval(
            binding=self._binding(session),
            approved_by=approved_by,
            note=note,
        )
        self._replace_session(
            session,
            stage=ProductionEvolutionStage.APPROVED,
            reason="signed_human_approval_issued",
            approval_id=approval.approval_id,
        )
        return approval

    def promote(
        self,
        session_id: str,
        *,
        approval: SignedPromotionApproval,
        release_ref: str,
    ) -> PromotionManifest:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.APPROVED)
        if not session.approval_id or approval.approval_id != session.approval_id:
            raise ValueError("promotion approval does not belong to this orchestration session")
        manifest = self._governance.promote(
            approval=approval,
            expected_binding=self._binding(session),
            release_ref=release_ref,
        )
        self._replace_session(
            session,
            stage=ProductionEvolutionStage.PROMOTED,
            reason="governed_promotion_completed",
            promotion_id=manifest.promotion_id,
            release_ref=manifest.release_ref,
        )
        return manifest

    def begin_monitoring(self, session_id: str) -> ProductionEvolutionSession:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.PROMOTED)
        return self._replace_session(
            session,
            stage=ProductionEvolutionStage.MONITOR,
            reason="post_promotion_monitoring_started",
        )

    def start_post_promotion_monitor(
        self,
        session_id: str,
        *,
        baseline_metrics: Iterable[MetricValue],
        policy: MonitoringPolicy,
    ) -> PostPromotionMonitorState:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.MONITOR)
        if session.monitor_id is not None:
            raise ValueError("post-promotion monitor already started for session")
        if not session.promotion_id or not session.release_ref or not session.candidate_fingerprint:
            raise ValueError("session lacks exact promoted release binding")
        baseline = MonitoringBaseline.create(
            promotion_id=session.promotion_id,
            candidate_id=session.candidate_id,
            candidate_fingerprint=session.candidate_fingerprint,
            release_ref=session.release_ref,
            metrics=baseline_metrics,
        )
        state = self._post_promotion_monitor.start(baseline=baseline, policy=policy)
        self._store_session(replace(session, monitor_id=state.monitor_id))
        return state

    def record_post_promotion_observation(
        self,
        session_id: str,
        *,
        metrics: Iterable[MetricValue],
        provider_error: str | None = None,
    ) -> PostPromotionMonitorState:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.MONITOR)
        state = self._required_monitoring_state(session)
        observation = HealthObservation.create(
            promotion_id=state.baseline.promotion_id,
            release_ref=state.baseline.release_ref,
            sequence=len(state.observations) + 1,
            metrics=metrics,
            provider_error=provider_error,
        )
        updated = self._post_promotion_monitor.record(state.monitor_id, observation)
        if updated.latest_assessment.verdict in {
            MonitoringVerdict.DEGRADATION_DETECTED,
            MonitoringVerdict.PROVIDER_ERROR,
        }:
            session = self._require_session(session_id)
            self._replace_session(
                session,
                stage=ProductionEvolutionStage.DEGRADATION_DETECTED,
                reason=updated.latest_assessment.reason,
            )
        return updated

    def recommend_rollback(
        self,
        session_id: str,
        *,
        reason: str | None = None,
    ) -> RollbackRecommendation:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.DEGRADATION_DETECTED)
        state = self._required_monitoring_state(session)
        recommendation = self._post_promotion_monitor.recommend_rollback(state.monitor_id, reason=reason)
        self._replace_session(
            session,
            stage=ProductionEvolutionStage.ROLLBACK_RECOMMENDED,
            reason="bounded_monitor_recommended_rollback",
            rollback_recommendation_id=recommendation.recommendation_id,
        )
        return recommendation

    def rollback(
        self,
        session_id: str,
        *,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.ROLLBACK_RECOMMENDED)
        if not session.promotion_id:
            raise ValueError("session has no governed promotion to roll back")
        if not session.rollback_recommendation_id:
            raise ValueError("session has no rollback recommendation")
        record = self._governance.rollback(
            promotion_id=session.promotion_id,
            target_promotion_id=target_promotion_id,
            reason=reason,
            rolled_back_by=rolled_back_by,
        )
        self._replace_session(
            session,
            stage=ProductionEvolutionStage.ROLLED_BACK,
            reason="governed_rollback_completed",
            rollback_id=record.rollback_id,
        )
        return record

    def reject(self, session_id: str, *, reason: str) -> ProductionEvolutionSession:
        session = self._require_session(session_id)
        if session.stage not in {
            ProductionEvolutionStage.APPROVAL_REQUIRED,
            ProductionEvolutionStage.APPROVED,
        }:
            raise ValueError(f"cannot reject production evolution session from {session.stage.value}")
        if session.candidate_id:
            record = self._lifecycle.get(session.candidate_id)
            if record is not None and record.state not in {
                LifecycleState.REJECTED,
                LifecycleState.PROMOTED,
                LifecycleState.ROLLED_BACK,
            }:
                self._lifecycle.reject(session.candidate_id, reason=reason)
        return self._replace_session(session, stage=ProductionEvolutionStage.REJECTED, reason=reason)

    def _binding(self, session: ProductionEvolutionSession) -> PromotionBinding:
        if not session.candidate_id or not session.evaluation_id or not session.candidate_fingerprint:
            raise ValueError("session lacks exact evaluated candidate binding")
        return PromotionBinding(
            baseline_sha=session.baseline_sha,
            candidate_id=session.candidate_id,
            candidate_fingerprint=session.candidate_fingerprint,
            evaluation_id=session.evaluation_id,
        )

    def _required_fingerprint(self, candidate_id: str) -> str:
        fingerprint = str(self._fingerprint_resolver(candidate_id)).strip()
        if not fingerprint:
            raise ValueError("fingerprint_resolver returned an empty fingerprint")
        return fingerprint

    def _required_monitoring_state(self, session: ProductionEvolutionSession) -> PostPromotionMonitorState:
        if not session.monitor_id:
            raise ValueError("post-promotion monitor has not been started")
        state = self._post_promotion_monitor.state(session.monitor_id)
        if state is None:
            raise ValueError("post-promotion monitoring state is missing")
        if state.baseline.promotion_id != session.promotion_id:
            raise ValueError("monitoring promotion binding mismatch")
        if state.baseline.release_ref != session.release_ref:
            raise ValueError("monitoring release binding mismatch")
        if state.baseline.candidate_id != session.candidate_id:
            raise ValueError("monitoring candidate binding mismatch")
        if state.baseline.candidate_fingerprint != session.candidate_fingerprint:
            raise ValueError("monitoring fingerprint binding mismatch")
        return state

    def _replace_session(
        self,
        session: ProductionEvolutionSession,
        *,
        stage: ProductionEvolutionStage,
        reason: str,
        approval_id: str | None = None,
        promotion_id: str | None = None,
        release_ref: str | None = None,
        rollback_recommendation_id: str | None = None,
        rollback_id: str | None = None,
    ) -> ProductionEvolutionSession:
        allowed = self._ALLOWED_TRANSITIONS.get(session.stage, frozenset())
        if stage not in allowed:
            raise ValueError(f"invalid production evolution transition: {session.stage.value} -> {stage.value}")
        updated = replace(
            session,
            stage=stage,
            transitions=(*session.transitions, ProductionEvolutionTransition(session.stage, stage, reason)),
            approval_id=approval_id if approval_id is not None else session.approval_id,
            promotion_id=promotion_id if promotion_id is not None else session.promotion_id,
            release_ref=release_ref if release_ref is not None else session.release_ref,
            rollback_recommendation_id=(
                rollback_recommendation_id
                if rollback_recommendation_id is not None
                else session.rollback_recommendation_id
            ),
            rollback_id=rollback_id if rollback_id is not None else session.rollback_id,
        )
        return self._store_session(updated)

    def _store_session(self, session: ProductionEvolutionSession) -> ProductionEvolutionSession:
        self._sessions[session.session_id] = session
        return session

    def _require_session(self, session_id: str) -> ProductionEvolutionSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise ValueError("unknown production evolution session")
        return session

    @staticmethod
    def _require_stage(session: ProductionEvolutionSession, expected: ProductionEvolutionStage) -> None:
        if session.stage is not expected:
            raise ValueError(f"session must be in {expected.value}, got {session.stage.value}")

    @staticmethod
    def _stage_for_outcome(outcome: EvolutionOutcome) -> ProductionEvolutionStage:
        mapping = {
            EvolutionOutcome.APPROVAL_REQUIRED: ProductionEvolutionStage.APPROVAL_REQUIRED,
            EvolutionOutcome.REJECTED: ProductionEvolutionStage.REJECTED,
            EvolutionOutcome.BLOCKED: ProductionEvolutionStage.BLOCKED,
            EvolutionOutcome.BUDGET_EXHAUSTED: ProductionEvolutionStage.BUDGET_EXHAUSTED,
            EvolutionOutcome.NO_ACTION: ProductionEvolutionStage.NEEDS_MORE_EVIDENCE,
            EvolutionOutcome.NEEDS_MORE_EVIDENCE: ProductionEvolutionStage.NEEDS_MORE_EVIDENCE,
        }
        return mapping[outcome]

    @staticmethod
    def _automated_trace(final_stage: ProductionEvolutionStage) -> tuple[ProductionEvolutionTransition, ...]:
        trace: list[ProductionEvolutionTransition] = []
        automated = (
            ProductionEvolutionStage.OBSERVE,
            ProductionEvolutionStage.MINE,
            ProductionEvolutionStage.PROPOSE,
            ProductionEvolutionStage.SANDBOX,
            ProductionEvolutionStage.SHADOW,
        )
        previous: ProductionEvolutionStage | None = None
        for stage in automated:
            trace.append(ProductionEvolutionTransition(previous, stage, "automated_evolution_stage"))
            previous = stage
        trace.append(ProductionEvolutionTransition(previous, final_stage, "automated_evolution_outcome"))
        return tuple(trace)
