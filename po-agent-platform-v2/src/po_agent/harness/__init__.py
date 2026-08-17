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
from .evolution_budget import (
    BudgetExceeded,
    EvolutionBudget,
    EvolutionBudgetPolicy,
    EvolutionBudgetSnapshot,
)
from .evolution_lifecycle import (
    ControlledImprovementLifecycle,
    EvaluationSnapshot,
    LifecycleRecord,
    LifecycleState,
    PromotionDecision,
    PromotionPolicy,
)
from .evolution_loop import (
    AutonomousEvolutionPolicy,
    AutonomousEvolutionReport,
    EvolutionAttemptRecord,
    EvolutionCandidateReport,
    EvolutionOutcome,
    PatchGenerationContext,
    PatchGenerator,
)
from .evolution_loop_memory import MemoryIntegratedAutonomousEvolutionLoop
from .evolution_memory import (
    EvolutionMemory,
    EvolutionMemoryEntry,
    EvolutionMemoryOutcome,
    EvolutionMemoryPolicy,
    SQLiteEvolutionMemoryStore,
    evolution_fingerprint,
)
from .governed_promotion import (
    ApprovalSigner,
    GovernanceAuditEvent,
    GovernanceEventType,
    GovernedPromotionService,
    GovernedRollbackRecord,
    PromotionBinding,
    PromotionManifest,
    SignedPromotionApproval,
    SQLiteGovernanceAuditStore,
)
from .hardened_sandbox_executor import (
    EVIDENCE_PREFIX,
    HardenedExecutorPolicy,
    HardenedSandboxExecutor,
    TrustedEvidencePolicy,
    TrustedSandboxEvidenceRunner,
)
from .os_isolation import (
    DockerIsolationBackend,
    DockerIsolationPolicy,
    IsolatedProcessResult,
    IsolationBackend,
    IsolationLevel,
    WorkspaceOnlyIsolationBackend,
)
from .operational_history import ActiveVersions, ExecutionRecord, SQLiteHistoryStore
from .observed_runtime import ObservedHarnessRuntime
from .promotion_registry import (
    HumanApprovalRecord,
    PromotionRecord,
    ReleaseState,
    RollbackRecord,
    SQLitePromotionAuditStore,
    VersionedPromotionRegistry,
)
from .runtime import HarnessRuntime, build_fake_runtime as _build_unobserved_fake_runtime
from .sandbox_evidence import (
    CommandObservation,
    SandboxEvidencePolicy,
    SandboxEvidenceReport,
    SandboxEvidenceRunner,
    ValidationCommand,
)
from .sandbox_patch import (
    PatchEvaluationGate,
    PatchEvaluationReport,
    PatchOperation,
    PatchProposal,
    PatchSynthesisPolicy,
    PatchValidationEvidence,
    PatchVerdict,
    ProposedFileChange,
    SandboxApplyResult,
    SandboxPatchApplicator,
    SandboxPatchSynthesizer,
)
from .secure_evolution_sandbox import (
    BaselineAttestor,
    SecureEvolutionSandbox,
    SecureEvolutionSandboxPolicy,
    SecureEvolutionSandboxResult,
)
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
    "BudgetExceeded",
    "EvolutionBudget",
    "EvolutionBudgetPolicy",
    "EvolutionBudgetSnapshot",
    "MemoryIntegratedAutonomousEvolutionLoop",
    "AutonomousEvolutionPolicy",
    "AutonomousEvolutionReport",
    "EvolutionAttemptRecord",
    "EvolutionCandidateReport",
    "EvolutionOutcome",
    "PatchGenerationContext",
    "PatchGenerator",
    "EvolutionMemory",
    "EvolutionMemoryEntry",
    "EvolutionMemoryOutcome",
    "EvolutionMemoryPolicy",
    "SQLiteEvolutionMemoryStore",
    "evolution_fingerprint",
    "ApprovalSigner",
    "GovernanceAuditEvent",
    "GovernanceEventType",
    "GovernedPromotionService",
    "GovernedRollbackRecord",
    "PromotionBinding",
    "PromotionManifest",
    "SignedPromotionApproval",
    "SQLiteGovernanceAuditStore",
    "HumanApprovalRecord",
    "PromotionRecord",
    "ReleaseState",
    "RollbackRecord",
    "SQLitePromotionAuditStore",
    "VersionedPromotionRegistry",
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
    "PatchEvaluationGate",
    "PatchEvaluationReport",
    "PatchOperation",
    "PatchProposal",
    "PatchSynthesisPolicy",
    "PatchValidationEvidence",
    "PatchVerdict",
    "ProposedFileChange",
    "SandboxApplyResult",
    "SandboxPatchApplicator",
    "SandboxPatchSynthesizer",
    "ValidationCommand",
    "CommandObservation",
    "SandboxEvidencePolicy",
    "SandboxEvidenceReport",
    "SandboxEvidenceRunner",
    "EVIDENCE_PREFIX",
    "HardenedExecutorPolicy",
    "HardenedSandboxExecutor",
    "TrustedEvidencePolicy",
    "TrustedSandboxEvidenceRunner",
    "DockerIsolationBackend",
    "DockerIsolationPolicy",
    "IsolatedProcessResult",
    "IsolationBackend",
    "IsolationLevel",
    "WorkspaceOnlyIsolationBackend",
    "BaselineAttestor",
    "SecureEvolutionSandbox",
    "SecureEvolutionSandboxPolicy",
    "SecureEvolutionSandboxResult",
    "build_fake_runtime",
]
