"""Autonomous, bounded, evidence-backed Harness evolution loop.

The orchestrator connects existing controlled-evolution components without
crossing the human-approval boundary.  It can mine failures, forge a governed
candidate, ask an injected patch generator for a concrete PatchProposal, execute
that proposal only inside SecureEvolutionSandbox, compare baseline/candidate in
shadow mode, and request approval when every deterministic gate is green.

It never commits, merges, pushes, edits Skill Catalog, approves or promotes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

from .eval_store import EvalSeed
from .evolution_budget import BudgetExceeded, EvolutionBudget, EvolutionBudgetSnapshot
from .evolution_lifecycle import ControlledImprovementLifecycle, LifecycleState
from .failure_miner import FailureCluster, FailureMiner
from .improvement_candidates import ImprovementCandidate
from .sandbox_evidence import ValidationCommand
from .sandbox_patch import PatchProposal, PatchVerdict
from .secure_evolution_sandbox import SecureEvolutionSandbox, SecureEvolutionSandboxResult
from .shadow_evaluation import ShadowEvaluationReport, ShadowEvaluator, ShadowRunner
from .skill_forge import SkillArtifact, SkillForge


class EvolutionOutcome(str, Enum):
    APPROVAL_REQUIRED = "approval_required"
    REJECTED = "rejected"
    BLOCKED = "blocked"
    BUDGET_EXHAUSTED = "budget_exhausted"
    NO_ACTION = "no_action"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"


@dataclass(frozen=True)
class AutonomousEvolutionPolicy:
    min_failure_occurrences: int = 2
    min_improved_cases: int = 1
    reject_on_shadow_regression: bool = True
    reject_on_no_improvement: bool = True

    def __post_init__(self) -> None:
        if self.min_failure_occurrences < 1:
            raise ValueError("min_failure_occurrences must be positive")
        if self.min_improved_cases < 0:
            raise ValueError("min_improved_cases cannot be negative")


@dataclass(frozen=True)
class PatchGenerationContext:
    cluster: FailureCluster
    artifact: SkillArtifact
    candidate: ImprovementCandidate
    baseline_sha: str
    attempt: int


class PatchGenerator(Protocol):
    """Generate one governed PatchProposal without applying it."""

    def generate(self, context: PatchGenerationContext) -> PatchProposal: ...


CommandsFactory = Callable[[PatchProposal], Sequence[ValidationCommand]]


@dataclass(frozen=True)
class EvolutionAttemptRecord:
    attempt: int
    proposal_id: str | None
    sandbox_verdict: str | None
    shadow_report_id: str | None
    outcome: EvolutionOutcome
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvolutionCandidateReport:
    cluster_key: str
    artifact_id: str
    candidate_id: str
    outcome: EvolutionOutcome
    attempts: tuple[EvolutionAttemptRecord, ...]
    lifecycle_state: str
    latest_shadow_report_id: str | None = None
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class AutonomousEvolutionReport:
    outcomes: tuple[EvolutionCandidateReport, ...]
    budget: EvolutionBudgetSnapshot
    mined_cluster_count: int

    @property
    def approval_required(self) -> tuple[EvolutionCandidateReport, ...]:
        return tuple(item for item in self.outcomes if item.outcome is EvolutionOutcome.APPROVAL_REQUIRED)


class AutonomousEvolutionLoop:
    """Run a bounded failure-to-approval experiment over curated eval evidence."""

    def __init__(
        self,
        *,
        failure_miner: FailureMiner,
        skill_forge: SkillForge,
        patch_generator: PatchGenerator,
        secure_sandbox: SecureEvolutionSandbox,
        shadow_evaluator: ShadowEvaluator,
        lifecycle: ControlledImprovementLifecycle,
        baseline_runner: ShadowRunner,
        candidate_runner: ShadowRunner,
        commands_factory: CommandsFactory,
        budget: EvolutionBudget,
        policy: AutonomousEvolutionPolicy | None = None,
    ) -> None:
        self.failure_miner = failure_miner
        self.skill_forge = skill_forge
        self.patch_generator = patch_generator
        self.secure_sandbox = secure_sandbox
        self.shadow_evaluator = shadow_evaluator
        self.lifecycle = lifecycle
        self.baseline_runner = baseline_runner
        self.candidate_runner = candidate_runner
        self.commands_factory = commands_factory
        self.budget = budget
        self.policy = policy or AutonomousEvolutionPolicy()

    def run(
        self,
        *,
        seeds: Sequence[EvalSeed],
        source_root: str | Path,
        baseline_sha: str,
    ) -> AutonomousEvolutionReport:
        if not baseline_sha.strip():
            raise ValueError("baseline_sha is required")
        seed_list = list(seeds)
        if not seed_list:
            return AutonomousEvolutionReport((), self.budget.snapshot(), 0)

        clusters = self.failure_miner.mine(
            seed_list,
            min_occurrences=self.policy.min_failure_occurrences,
        )
        seed_by_id = {seed.eval_id: seed for seed in seed_list}
        outcomes: list[EvolutionCandidateReport] = []

        for cluster in clusters:
            try:
                self.budget.claim_cluster()
                self.budget.claim_candidate()
            except BudgetExceeded as exc:
                outcomes.append(
                    EvolutionCandidateReport(
                        cluster_key=cluster.key,
                        artifact_id="",
                        candidate_id="",
                        outcome=EvolutionOutcome.BUDGET_EXHAUSTED,
                        attempts=(),
                        lifecycle_state=LifecycleState.DRAFT.value,
                        reasons=(str(exc),),
                    )
                )
                break

            artifact = self.skill_forge.forge(cluster)
            candidate = artifact.to_improvement_candidate()
            lifecycle_record = self.lifecycle.register(candidate)
            cluster_seeds = [seed_by_id[item] for item in cluster.eval_ids if item in seed_by_id]
            if not cluster_seeds:
                self.lifecycle.reject(candidate.candidate_id, reason="cluster evidence unavailable")
                outcomes.append(
                    EvolutionCandidateReport(
                        cluster_key=cluster.key,
                        artifact_id=artifact.artifact_id,
                        candidate_id=candidate.candidate_id,
                        outcome=EvolutionOutcome.NEEDS_MORE_EVIDENCE,
                        attempts=(),
                        lifecycle_state=LifecycleState.REJECTED.value,
                        reasons=("cluster_evidence_unavailable",),
                    )
                )
                continue

            candidate_report = self._run_candidate(
                cluster=cluster,
                artifact=artifact,
                candidate=candidate,
                source_root=source_root,
                baseline_sha=baseline_sha,
                cluster_seeds=cluster_seeds,
            )
            outcomes.append(candidate_report)

        return AutonomousEvolutionReport(
            outcomes=tuple(outcomes),
            budget=self.budget.snapshot(),
            mined_cluster_count=len(clusters),
        )

    def _run_candidate(
        self,
        *,
        cluster: FailureCluster,
        artifact: SkillArtifact,
        candidate: ImprovementCandidate,
        source_root: str | Path,
        baseline_sha: str,
        cluster_seeds: list[EvalSeed],
    ) -> EvolutionCandidateReport:
        attempt_records: list[EvolutionAttemptRecord] = []
        latest_shadow: ShadowEvaluationReport | None = None
        attempt_index = 0

        while True:
            try:
                self.budget.claim_patch_attempt(attempt_index)
            except BudgetExceeded as exc:
                if self.lifecycle.get(candidate.candidate_id).state not in {
                    LifecycleState.REJECTED,
                    LifecycleState.PROMOTED,
                    LifecycleState.ROLLED_BACK,
                }:
                    self.lifecycle.reject(candidate.candidate_id, reason=str(exc))
                return self._candidate_report(
                    cluster,
                    artifact,
                    candidate,
                    EvolutionOutcome.BUDGET_EXHAUSTED,
                    attempt_records,
                    latest_shadow,
                    (str(exc),),
                )

            attempt_index += 1
            context = PatchGenerationContext(
                cluster=cluster,
                artifact=artifact,
                candidate=candidate,
                baseline_sha=baseline_sha,
                attempt=attempt_index,
            )
            try:
                proposal = self.patch_generator.generate(context)
            except Exception as exc:
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=None,
                        sandbox_verdict=None,
                        shadow_report_id=None,
                        outcome=EvolutionOutcome.REJECTED,
                        reasons=("patch_generation_failed", type(exc).__name__),
                    )
                )
                if attempt_index >= self.budget.policy.max_attempts_per_candidate:
                    self.lifecycle.reject(candidate.candidate_id, reason="patch generation failed")
                    return self._candidate_report(
                        cluster,
                        artifact,
                        candidate,
                        EvolutionOutcome.REJECTED,
                        attempt_records,
                        latest_shadow,
                        ("patch_generation_failed",),
                    )
                continue

            self._validate_proposal_lineage(proposal, candidate, artifact, baseline_sha)
            commands = tuple(self.commands_factory(proposal))
            if not commands:
                self.lifecycle.reject(candidate.candidate_id, reason="validation plan is empty")
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=proposal.proposal_id,
                        sandbox_verdict=None,
                        shadow_report_id=None,
                        outcome=EvolutionOutcome.BLOCKED,
                        reasons=("empty_validation_plan",),
                    )
                )
                return self._candidate_report(
                    cluster,
                    artifact,
                    candidate,
                    EvolutionOutcome.BLOCKED,
                    attempt_records,
                    latest_shadow,
                    ("empty_validation_plan",),
                )

            try:
                sandbox_result = self.secure_sandbox.run(
                    proposal=proposal,
                    source_root=source_root,
                    commands=commands,
                )
            except Exception as exc:
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=proposal.proposal_id,
                        sandbox_verdict=None,
                        shadow_report_id=None,
                        outcome=EvolutionOutcome.BLOCKED,
                        reasons=("sandbox_execution_failed", type(exc).__name__),
                    )
                )
                if attempt_index >= self.budget.policy.max_attempts_per_candidate:
                    self.lifecycle.reject(candidate.candidate_id, reason="sandbox execution failed")
                    return self._candidate_report(
                        cluster,
                        artifact,
                        candidate,
                        EvolutionOutcome.BLOCKED,
                        attempt_records,
                        latest_shadow,
                        ("sandbox_execution_failed",),
                    )
                continue

            sandbox_verdict = sandbox_result.evaluation_report.verdict
            if sandbox_verdict is not PatchVerdict.APPROVAL_REQUIRED:
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=proposal.proposal_id,
                        sandbox_verdict=sandbox_verdict.value,
                        shadow_report_id=None,
                        outcome=(
                            EvolutionOutcome.BLOCKED
                            if sandbox_verdict is PatchVerdict.BLOCKED
                            else EvolutionOutcome.REJECTED
                        ),
                        reasons=tuple(sandbox_result.evaluation_report.reasons),
                    )
                )
                if attempt_index >= self.budget.policy.max_attempts_per_candidate:
                    self.lifecycle.reject(
                        candidate.candidate_id,
                        reason="sandbox gate failed: " + ", ".join(sandbox_result.evaluation_report.reasons),
                    )
                    return self._candidate_report(
                        cluster,
                        artifact,
                        candidate,
                        EvolutionOutcome.BLOCKED
                        if sandbox_verdict is PatchVerdict.BLOCKED
                        else EvolutionOutcome.REJECTED,
                        attempt_records,
                        latest_shadow,
                        tuple(sandbox_result.evaluation_report.reasons),
                    )
                continue

            latest_shadow = self.shadow_evaluator.evaluate(
                candidate=candidate,
                seeds=cluster_seeds,
                baseline_runner=self.baseline_runner,
                candidate_runner=self.candidate_runner,
                new_code_regressions=sandbox_result.evaluation_report.evidence.new_code_regressions,
            )
            shadow_reasons = self._shadow_reasons(latest_shadow)
            snapshot = latest_shadow.to_snapshot()
            self.lifecycle.record_evaluation(snapshot)

            if shadow_reasons:
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=proposal.proposal_id,
                        sandbox_verdict=sandbox_verdict.value,
                        shadow_report_id=latest_shadow.report_id,
                        outcome=EvolutionOutcome.REJECTED,
                        reasons=shadow_reasons,
                    )
                )
                if attempt_index >= self.budget.policy.max_attempts_per_candidate:
                    self.lifecycle.reject(candidate.candidate_id, reason=", ".join(shadow_reasons))
                    return self._candidate_report(
                        cluster,
                        artifact,
                        candidate,
                        EvolutionOutcome.REJECTED,
                        attempt_records,
                        latest_shadow,
                        shadow_reasons,
                    )
                continue

            try:
                self.lifecycle.request_approval(candidate.candidate_id)
            except ValueError as exc:
                attempt_records.append(
                    EvolutionAttemptRecord(
                        attempt=attempt_index,
                        proposal_id=proposal.proposal_id,
                        sandbox_verdict=sandbox_verdict.value,
                        shadow_report_id=latest_shadow.report_id,
                        outcome=EvolutionOutcome.REJECTED,
                        reasons=("lifecycle_gate_failed", str(exc)),
                    )
                )
                self.lifecycle.reject(candidate.candidate_id, reason=str(exc))
                return self._candidate_report(
                    cluster,
                    artifact,
                    candidate,
                    EvolutionOutcome.REJECTED,
                    attempt_records,
                    latest_shadow,
                    ("lifecycle_gate_failed",),
                )

            attempt_records.append(
                EvolutionAttemptRecord(
                    attempt=attempt_index,
                    proposal_id=proposal.proposal_id,
                    sandbox_verdict=sandbox_verdict.value,
                    shadow_report_id=latest_shadow.report_id,
                    outcome=EvolutionOutcome.APPROVAL_REQUIRED,
                    reasons=("all_automated_gates_passed",),
                )
            )
            return self._candidate_report(
                cluster,
                artifact,
                candidate,
                EvolutionOutcome.APPROVAL_REQUIRED,
                attempt_records,
                latest_shadow,
                ("human_approval_required",),
            )

    def _shadow_reasons(self, report: ShadowEvaluationReport) -> tuple[str, ...]:
        reasons: list[str] = []
        if report.safety_regressions:
            reasons.append("shadow_safety_regression")
        if self.policy.reject_on_shadow_regression and report.regressed_cases:
            reasons.append("shadow_correctness_regression")
        if self.policy.reject_on_no_improvement and report.improved_cases < self.policy.min_improved_cases:
            reasons.append("insufficient_measured_improvement")
        return tuple(reasons)

    @staticmethod
    def _validate_proposal_lineage(
        proposal: PatchProposal,
        candidate: ImprovementCandidate,
        artifact: SkillArtifact,
        baseline_sha: str,
    ) -> None:
        if proposal.source_candidate_id != candidate.candidate_id:
            raise ValueError("patch proposal candidate lineage mismatch")
        if proposal.source_skill_artifact_id != artifact.artifact_id:
            raise ValueError("patch proposal forge-artifact lineage mismatch")
        if proposal.baseline_sha != baseline_sha:
            raise ValueError("patch proposal baseline lineage mismatch")
        if not proposal.requires_human_approval:
            raise ValueError("patch proposal must preserve human approval boundary")

    def _candidate_report(
        self,
        cluster: FailureCluster,
        artifact: SkillArtifact,
        candidate: ImprovementCandidate,
        outcome: EvolutionOutcome,
        attempts: list[EvolutionAttemptRecord],
        latest_shadow: ShadowEvaluationReport | None,
        reasons: tuple[str, ...],
    ) -> EvolutionCandidateReport:
        record = self.lifecycle.get(candidate.candidate_id)
        state = record.state.value if record is not None else LifecycleState.DRAFT.value
        return EvolutionCandidateReport(
            cluster_key=cluster.key,
            artifact_id=artifact.artifact_id,
            candidate_id=candidate.candidate_id,
            outcome=outcome,
            attempts=tuple(attempts),
            lifecycle_state=state,
            latest_shadow_report_id=latest_shadow.report_id if latest_shadow else None,
            reasons=reasons,
        )
