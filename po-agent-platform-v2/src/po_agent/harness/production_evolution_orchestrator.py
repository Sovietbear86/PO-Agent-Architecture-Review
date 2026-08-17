"""Canonical production orchestration for governed Harness evolution.

This module connects the already-bounded autonomous experiment loop with the
human-gated promotion service.  It deliberately does not duplicate mining,
patching, sandboxing or shadow evaluation.  Instead, it owns the production
state machine and makes the trusted transition path explicit:

OBSERVE -> MINE -> PROPOSE -> SANDBOX -> SHADOW -> APPROVAL_REQUIRED
        -> APPROVED -> PROMOTED -> MONITOR -> ROLLED_BACK

Rejected/blocked/failed outcomes are terminal.  Promotion can happen only via
GovernedPromotionService; no direct lifecycle mark_promoted() path is exposed.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol, Sequence

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
    """Trusted state-machine facade for the full production evolution path.

    The autonomous experiment runner may only advance a candidate as far as
    APPROVAL_REQUIRED.  Human approval and promotion are delegated exclusively
    to GovernedPromotionService.  The orchestrator keeps a canonical transition
    history so downstream monitoring and audit code does not have to infer state
    from several components.
    """

    _ALLOWED_TRANSITIONS: dict[ProductionEvolutionStage, frozenset[ProductionEvolutionStage]] = {
        ProductionEvolutionStage.APPROVAL_REQUIRED: frozenset(
            {ProductionEvolutionStage.APPROVED, ProductionEvolutionStage.REJECTED}
        ),
        ProductionEvolutionStage.APPROVED: frozenset(
            {ProductionEvolutionStage.PROMOTED, ProductionEvolutionStage.REJECTED}
        ),
        ProductionEvolutionStage.PROMOTED: frozenset({ProductionEvolutionStage.MONITOR}),
        ProductionEvolutionStage.MONITOR: frozenset({ProductionEvolutionStage.ROLLED_BACK}),
    }

    def __init__(
        self,
        *,
        experiment_runner: EvolutionExperimentRunner,
        lifecycle: ControlledImprovementLifecycle,
        governance: GovernedPromotionService,
        fingerprint_resolver: FingerprintResolver,
    ) -> None:
        self._experiment_runner = experiment_runner
        self._lifecycle = lifecycle
        self._governance = governance
        self._fingerprint_resolver = fingerprint_resolver
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

    def request_human_approval(
        self,
        session_id: str,
        *,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.APPROVAL_REQUIRED)
        binding = self._binding(session)
        approval = self._governance.issue_human_approval(
            binding=binding,
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

    def rollback(
        self,
        session_id: str,
        *,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord:
        session = self._require_session(session_id)
        self._require_stage(session, ProductionEvolutionStage.MONITOR)
        if not session.promotion_id:
            raise ValueError("session has no governed promotion to roll back")
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
            if record is not None and record.state not in {LifecycleState.REJECTED, LifecycleState.PROMOTED, LifecycleState.ROLLED_BACK}:
                self._lifecycle.reject(session.candidate_id, reason=reason)
        return self._replace_session(
            session,
            stage=ProductionEvolutionStage.REJECTED,
            reason=reason,
        )

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

    def _replace_session(
        self,
        session: ProductionEvolutionSession,
        *,
        stage: ProductionEvolutionStage,
        reason: str,
        approval_id: str | None = None,
        promotion_id: str | None = None,
        release_ref: str | None = None,
        rollback_id: str | None = None,
    ) -> ProductionEvolutionSession:
        allowed = self._ALLOWED_TRANSITIONS.get(session.stage, frozenset())
        if stage not in allowed:
            raise ValueError(f"invalid production evolution transition: {session.stage.value} -> {stage.value}")
        transition = ProductionEvolutionTransition(session.stage, stage, reason)
        updated = replace(
            session,
            stage=stage,
            transitions=(*session.transitions, transition),
            approval_id=approval_id if approval_id is not None else session.approval_id,
            promotion_id=promotion_id if promotion_id is not None else session.promotion_id,
            release_ref=release_ref if release_ref is not None else session.release_ref,
            rollback_id=rollback_id if rollback_id is not None else session.rollback_id,
        )
        self._sessions[session.session_id] = updated
        return updated

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
