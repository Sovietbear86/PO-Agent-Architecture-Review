"""Executable harness core for PO Agent Platform.

The public factory returns an observed runtime: business execution remains in
HarnessRuntime while operational history is recorded by a decorator.
"""

from .contracts import (
    CapabilityResult,
    Evidence,
    HarnessRequest,
    HarnessResponse,
    ResponseStatus,
)
from .evolution_lifecycle import (
    ControlledImprovementLifecycle,
    EvaluationSnapshot,
    LifecycleRecord,
    LifecycleState,
    PromotionDecision,
    PromotionPolicy,
)
from .operational_history import ActiveVersions, ExecutionRecord, SQLiteHistoryStore
from .observed_runtime import ObservedHarnessRuntime
from .runtime import HarnessRuntime, build_fake_runtime as _build_unobserved_fake_runtime
from .shadow_evaluation import (
    SeedComparison,
    ShadowEvaluationAuditStore,
    ShadowEvaluationReport,
    ShadowEvaluator,
    ShadowObservation,
    ShadowRunner,
    SQLiteShadowEvaluationAuditStore,
)
from .skill_forge import ForgeArtifactKind, ForgePolicy, SkillArtifact, SkillForge


def build_fake_runtime() -> ObservedHarnessRuntime:
    """Build deterministic FakeAS21 Harness with append-only execution history."""
    return ObservedHarnessRuntime(_build_unobserved_fake_runtime())


__all__ = [
    "CapabilityResult",
    "Evidence",
    "HarnessRequest",
    "HarnessResponse",
    "ResponseStatus",
    "HarnessRuntime",
    "ObservedHarnessRuntime",
    "ActiveVersions",
    "ExecutionRecord",
    "SQLiteHistoryStore",
    "ControlledImprovementLifecycle",
    "EvaluationSnapshot",
    "LifecycleRecord",
    "LifecycleState",
    "PromotionDecision",
    "PromotionPolicy",
    "SeedComparison",
    "ShadowEvaluationAuditStore",
    "ShadowEvaluationReport",
    "ShadowEvaluator",
    "ShadowObservation",
    "ShadowRunner",
    "SQLiteShadowEvaluationAuditStore",
    "ForgeArtifactKind",
    "ForgePolicy",
    "SkillArtifact",
    "SkillForge",
    "build_fake_runtime",
]
