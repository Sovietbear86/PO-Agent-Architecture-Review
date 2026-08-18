"""Production composition root for the self-evolving PO Agent Harness.

This module deliberately contains no autonomous deployment logic.  It wires the
already hardened evolution, governance, persistence and monitoring boundaries
into one explicit production-facing object.  Human approval remains mandatory
and promotion/rollback authority remains owned by the governed service.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .eval_store import EvalSeed
from .evolution_lifecycle import ControlledImprovementLifecycle
from .governed_promotion import (
    ApprovalSigner,
    GovernedRollbackRecord,
    PromotionManifest,
    SQLiteGovernanceAuditStore,
    SignedPromotionApproval,
)
from .post_promotion_monitoring import (
    MetricValue,
    MonitoringPolicy,
    PostPromotionMonitor,
    PostPromotionMonitorState,
    RollbackRecommendation,
)
from .production_evolution_orchestrator import (
    EvolutionExperimentRunner,
    FingerprintResolver,
    ProductionEvolutionOrchestrator,
    ProductionEvolutionSession,
)
from .promotion_registry import VersionedPromotionRegistry
from .restart_safe_governance import (
    RestartSafeGovernedPromotionService,
    SQLiteGovernanceStateStore,
)


ReleaseApplier = Callable[[PromotionManifest], None]
RollbackApplier = Callable[[GovernedRollbackRecord], None]


@dataclass(frozen=True)
class ProductionHarnessRuntimeConfig:
    """Security-sensitive configuration for the production composition root."""

    state_db_path: str
    audit_db_path: str
    signing_key: bytes

    def __post_init__(self) -> None:
        if not str(self.state_db_path).strip():
            raise ValueError("state_db_path is required")
        if not str(self.audit_db_path).strip():
            raise ValueError("audit_db_path is required")
        if self.state_db_path == ":memory:" or self.audit_db_path == ":memory:":
            raise ValueError("production runtime requires durable on-disk governance databases")
        if not isinstance(self.signing_key, bytes) or len(self.signing_key) < 32:
            raise ValueError("production signing_key must contain at least 32 bytes")

    @classmethod
    def in_directory(
        cls,
        directory: str | Path,
        *,
        signing_key: bytes,
    ) -> "ProductionHarnessRuntimeConfig":
        root = Path(directory).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        return cls(
            state_db_path=str(root / "governance_state.sqlite3"),
            audit_db_path=str(root / "governance_audit.sqlite3"),
            signing_key=signing_key,
        )


@dataclass(frozen=True)
class ProductionHarnessRuntimeStatus:
    durable_governance: bool
    human_approval_required: bool
    autonomous_promotion_enabled: bool
    autonomous_rollback_enabled: bool
    monitoring_has_rollback_authority: bool


class ProductionHarnessRuntime:
    """Canonical production facade for controlled Harness evolution.

    The runtime is a composition boundary, not a new authority.  Its methods
    delegate to :class:`ProductionEvolutionOrchestrator`, whose production path
    stops at explicit human approval and uses governed promotion/rollback only.
    """

    def __init__(
        self,
        *,
        config: ProductionHarnessRuntimeConfig,
        experiment_runner: EvolutionExperimentRunner,
        lifecycle: ControlledImprovementLifecycle,
        fingerprint_resolver: FingerprintResolver,
        release_applier: ReleaseApplier | None = None,
        rollback_applier: RollbackApplier | None = None,
        post_promotion_monitor: PostPromotionMonitor | None = None,
    ) -> None:
        if lifecycle is None:
            raise ValueError("lifecycle is required")
        if not lifecycle.policy.require_human_approval:
            raise ValueError("production runtime requires human approval policy")
        if experiment_runner is None:
            raise ValueError("experiment_runner is required")
        if fingerprint_resolver is None:
            raise ValueError("fingerprint_resolver is required")

        self._config = config
        self._state_store = SQLiteGovernanceStateStore(config.state_db_path)
        self._registry = VersionedPromotionRegistry()
        self._audit_store = SQLiteGovernanceAuditStore(config.audit_db_path)
        self._governance = RestartSafeGovernedPromotionService(
            state_store=self._state_store,
            lifecycle=lifecycle,
            registry=self._registry,
            signer=ApprovalSigner(config.signing_key),
            audit_store=self._audit_store,
            release_applier=release_applier,
            rollback_applier=rollback_applier,
        )
        self._orchestrator = ProductionEvolutionOrchestrator(
            experiment_runner=experiment_runner,
            lifecycle=lifecycle,
            governance=self._governance,
            fingerprint_resolver=fingerprint_resolver,
            post_promotion_monitor=post_promotion_monitor,
        )
        self._closed = False

    @property
    def orchestrator(self) -> ProductionEvolutionOrchestrator:
        self._require_open()
        return self._orchestrator

    @property
    def governance(self) -> RestartSafeGovernedPromotionService:
        self._require_open()
        return self._governance

    @property
    def status(self) -> ProductionHarnessRuntimeStatus:
        self._require_open()
        return ProductionHarnessRuntimeStatus(
            durable_governance=True,
            human_approval_required=True,
            autonomous_promotion_enabled=False,
            autonomous_rollback_enabled=False,
            monitoring_has_rollback_authority=False,
        )

    def run_experiments(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> tuple[ProductionEvolutionSession, ...]:
        self._require_open()
        return self._orchestrator.run_experiments(
            seeds=seeds,
            source_root=source_root,
            baseline_sha=baseline_sha,
        )

    def request_human_approval(
        self,
        session_id: str,
        *,
        approved_by: str,
        note: str | None = None,
    ) -> SignedPromotionApproval:
        self._require_open()
        return self._orchestrator.request_human_approval(
            session_id,
            approved_by=approved_by,
            note=note,
        )

    def promote(
        self,
        session_id: str,
        *,
        approval: SignedPromotionApproval,
        release_ref: str,
    ) -> PromotionManifest:
        self._require_open()
        return self._orchestrator.promote(
            session_id,
            approval=approval,
            release_ref=release_ref,
        )

    def begin_monitoring(self, session_id: str) -> ProductionEvolutionSession:
        self._require_open()
        return self._orchestrator.begin_monitoring(session_id)

    def start_post_promotion_monitor(
        self,
        session_id: str,
        *,
        baseline_metrics: Iterable[MetricValue],
        policy: MonitoringPolicy,
    ) -> PostPromotionMonitorState:
        self._require_open()
        return self._orchestrator.start_post_promotion_monitor(
            session_id,
            baseline_metrics=baseline_metrics,
            policy=policy,
        )

    def record_post_promotion_observation(
        self,
        session_id: str,
        *,
        metrics: Iterable[MetricValue],
        provider_error: str | None = None,
    ) -> PostPromotionMonitorState:
        self._require_open()
        return self._orchestrator.record_post_promotion_observation(
            session_id,
            metrics=metrics,
            provider_error=provider_error,
        )

    def recommend_rollback(
        self,
        session_id: str,
        *,
        reason: str | None = None,
    ) -> RollbackRecommendation:
        self._require_open()
        return self._orchestrator.recommend_rollback(session_id, reason=reason)

    def rollback(
        self,
        session_id: str,
        *,
        target_promotion_id: str,
        reason: str,
        rolled_back_by: str,
    ) -> GovernedRollbackRecord:
        self._require_open()
        return self._orchestrator.rollback(
            session_id,
            target_promotion_id=target_promotion_id,
            reason=reason,
            rolled_back_by=rolled_back_by,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._state_store.close()
        self._closed = True

    def __enter__(self) -> "ProductionHarnessRuntime":
        self._require_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("production harness runtime is closed")


def build_production_harness_runtime(
    *,
    config: ProductionHarnessRuntimeConfig,
    experiment_runner: EvolutionExperimentRunner,
    lifecycle: ControlledImprovementLifecycle,
    fingerprint_resolver: FingerprintResolver,
    release_applier: ReleaseApplier | None = None,
    rollback_applier: RollbackApplier | None = None,
    post_promotion_monitor: PostPromotionMonitor | None = None,
) -> ProductionHarnessRuntime:
    """Build the canonical durable production runtime.

    Dependency injection is intentional: the experiment runner and deployment
    appliers remain explicit trust boundaries instead of being discovered from
    ambient process state.
    """
    return ProductionHarnessRuntime(
        config=config,
        experiment_runner=experiment_runner,
        lifecycle=lifecycle,
        fingerprint_resolver=fingerprint_resolver,
        release_applier=release_applier,
        rollback_applier=rollback_applier,
        post_promotion_monitor=post_promotion_monitor,
    )
