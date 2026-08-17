"""Memory-integrated controlled evolution orchestration.

This module composes the existing AutonomousEvolutionLoop with the append-only
EvolutionMemory trust boundary. Known-bad proposal fingerprints are checked
before sandbox execution; trusted outcomes are written as soon as a retry-relevant
gate resolves. The wrapper never approves, promotes, commits, merges, pushes, or
mutates the Skill Catalog.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Sequence

from .evolution_loop import (
    AutonomousEvolutionLoop,
    AutonomousEvolutionPolicy,
    AutonomousEvolutionReport,
    CommandsFactory,
    PatchGenerationContext,
    PatchGenerator,
)
from .evolution_memory import (
    EvolutionMemory,
    EvolutionMemoryEntry,
    EvolutionMemoryOutcome,
    EvolutionMemoryWriteAuthority,
)
from .sandbox_patch import PatchProposal, PatchVerdict
from .secure_evolution_sandbox import SecureEvolutionSandbox
from .shadow_evaluation import ShadowEvaluationReport, ShadowEvaluator


def _proposal_material(proposal: PatchProposal) -> str:
    """Return deterministic proposal material used by EvolutionMemory fingerprinting."""
    return json.dumps(
        {
            "baseline_sha": proposal.baseline_sha,
            "risk_classification": proposal.risk_classification,
            "changes": [
                {
                    "path": change.path,
                    "operation": change.operation.value,
                    "content": change.content,
                    "expected_before_sha256": change.expected_before_sha256,
                }
                for change in proposal.changes
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class _ProposalContext:
    failure_key: str
    candidate_id: str
    proposal: PatchProposal
    material: str


class _MemoryCoordinator:
    def __init__(
        self,
        *,
        memory: EvolutionMemory,
        authority: EvolutionMemoryWriteAuthority,
        policy: AutonomousEvolutionPolicy,
    ) -> None:
        self.memory = memory
        self.authority = authority
        self.policy = policy
        self.by_proposal: dict[str, _ProposalContext] = {}
        self.latest_by_candidate: dict[str, _ProposalContext] = {}
        self.denied_proposals: dict[str, tuple[str, ...]] = {}
        self._recorded: set[tuple[str, str, EvolutionMemoryOutcome]] = set()

    def register(self, context: PatchGenerationContext, proposal: PatchProposal) -> None:
        proposal_context = _ProposalContext(
            failure_key=context.cluster.key,
            candidate_id=context.candidate.candidate_id,
            proposal=proposal,
            material=_proposal_material(proposal),
        )
        self.by_proposal[proposal.proposal_id] = proposal_context
        self.latest_by_candidate[context.candidate.candidate_id] = proposal_context
        fingerprint = EvolutionMemoryEntry.create(
            failure_key=proposal_context.failure_key,
            candidate_id=proposal_context.candidate_id,
            outcome=EvolutionMemoryOutcome.ERROR,
            proposal_id=proposal.proposal_id,
            target_files=proposal.target_files,
            proposal_material=proposal_context.material,
        ).fingerprint
        allowed, reasons = self.memory.should_attempt(fingerprint)
        if not allowed:
            self.denied_proposals[proposal.proposal_id] = reasons

    def record(
        self,
        *,
        proposal_id: str,
        outcome: EvolutionMemoryOutcome,
        reasons: Sequence[str] = (),
        evaluation_id: str | None = None,
    ) -> None:
        context = self.by_proposal.get(proposal_id)
        if context is None:
            return
        key = (context.candidate_id, proposal_id, outcome)
        if key in self._recorded:
            return
        entry = EvolutionMemoryEntry.create(
            failure_key=context.failure_key,
            candidate_id=context.candidate_id,
            outcome=outcome,
            proposal_id=proposal_id,
            target_files=context.proposal.target_files,
            proposal_material=context.material,
            reasons=reasons,
            evaluation_id=evaluation_id,
        )
        self.memory.append(entry, authority=self.authority)
        self._recorded.add(key)

    def record_latest(
        self,
        *,
        candidate_id: str,
        outcome: EvolutionMemoryOutcome,
        reasons: Sequence[str] = (),
        evaluation_id: str | None = None,
    ) -> None:
        context = self.latest_by_candidate.get(candidate_id)
        if context is not None:
            self.record(
                proposal_id=context.proposal.proposal_id,
                outcome=outcome,
                reasons=reasons,
                evaluation_id=evaluation_id,
            )


class _MemoryAwarePatchGenerator:
    def __init__(self, delegate: PatchGenerator, coordinator: _MemoryCoordinator) -> None:
        self.delegate = delegate
        self.coordinator = coordinator

    def generate(self, context: PatchGenerationContext) -> PatchProposal:
        proposal = self.delegate.generate(context)
        self.coordinator.register(context, proposal)
        return proposal


class _MemoryAwareCommandsFactory:
    def __init__(self, delegate: CommandsFactory, coordinator: _MemoryCoordinator) -> None:
        self.delegate = delegate
        self.coordinator = coordinator

    def __call__(self, proposal: PatchProposal):
        denied = self.coordinator.denied_proposals.get(proposal.proposal_id)
        if denied is not None:
            self.coordinator.record(
                proposal_id=proposal.proposal_id,
                outcome=EvolutionMemoryOutcome.BLOCKED,
                reasons=("evolution_memory_retry_guard", *denied),
            )
            return ()
        commands = tuple(self.delegate(proposal))
        if not commands:
            self.coordinator.record(
                proposal_id=proposal.proposal_id,
                outcome=EvolutionMemoryOutcome.BLOCKED,
                reasons=("empty_validation_plan",),
            )
        return commands


class _MemoryAwareSandbox:
    def __init__(self, delegate: SecureEvolutionSandbox, coordinator: _MemoryCoordinator) -> None:
        self.delegate = delegate
        self.coordinator = coordinator

    def run(self, *, proposal, source_root, commands):
        try:
            result = self.delegate.run(proposal=proposal, source_root=source_root, commands=commands)
        except Exception as exc:
            self.coordinator.record(
                proposal_id=proposal.proposal_id,
                outcome=EvolutionMemoryOutcome.ERROR,
                reasons=("sandbox_execution_failed", type(exc).__name__),
            )
            raise
        verdict = result.evaluation_report.verdict
        if verdict is PatchVerdict.BLOCKED:
            outcome = EvolutionMemoryOutcome.BLOCKED
        elif verdict is PatchVerdict.REJECTED:
            outcome = EvolutionMemoryOutcome.REJECTED
        else:
            outcome = None
        if outcome is not None:
            self.coordinator.record(
                proposal_id=proposal.proposal_id,
                outcome=outcome,
                reasons=tuple(result.evaluation_report.reasons),
            )
        return result


class _MemoryAwareShadowEvaluator:
    def __init__(self, delegate: ShadowEvaluator, coordinator: _MemoryCoordinator) -> None:
        self.delegate = delegate
        self.coordinator = coordinator

    def evaluate(self, *, candidate, seeds, baseline_runner, candidate_runner, new_code_regressions=0):
        report: ShadowEvaluationReport = self.delegate.evaluate(
            candidate=candidate,
            seeds=seeds,
            baseline_runner=baseline_runner,
            candidate_runner=candidate_runner,
            new_code_regressions=new_code_regressions,
        )
        reasons: list[str] = []
        if report.safety_regressions:
            reasons.append("shadow_safety_regression")
        if self.coordinator.policy.reject_on_shadow_regression and report.regressed_cases:
            reasons.append("shadow_correctness_regression")
        if (
            self.coordinator.policy.reject_on_no_improvement
            and report.improved_cases < self.coordinator.policy.min_improved_cases
        ):
            reasons.append("insufficient_measured_improvement")
        if reasons:
            self.coordinator.record_latest(
                candidate_id=candidate.candidate_id,
                outcome=EvolutionMemoryOutcome.REJECTED,
                reasons=tuple(reasons),
                evaluation_id=report.report_id,
            )
        return report


class MemoryIntegratedAutonomousEvolutionLoop:
    """AutonomousEvolutionLoop with trusted EvolutionMemory retry enforcement.

    Ownership rule: the write authority is retained only by this trusted wrapper.
    Callers receive the memory object for read/query use but never receive the
    capability used for append operations.
    """

    def __init__(
        self,
        *,
        evolution_memory: EvolutionMemory,
        failure_miner,
        skill_forge,
        patch_generator: PatchGenerator,
        secure_sandbox: SecureEvolutionSandbox,
        shadow_evaluator: ShadowEvaluator,
        lifecycle,
        baseline_runner,
        candidate_runner,
        commands_factory: CommandsFactory,
        budget,
        policy: AutonomousEvolutionPolicy | None = None,
    ) -> None:
        resolved_policy = policy or AutonomousEvolutionPolicy()
        authority = EvolutionMemoryWriteAuthority()
        # Rebind memory to a wrapper-owned authority by requiring callers to pass
        # a memory instance that was intentionally created for this loop.
        if getattr(evolution_memory, "_EvolutionMemory__write_authority", None) is not None:
            raise ValueError("evolution_memory must not be pre-bound to an external write authority")
        setattr(evolution_memory, "_EvolutionMemory__write_authority", authority)
        self.evolution_memory = evolution_memory
        self.__write_authority = authority
        self._coordinator = _MemoryCoordinator(
            memory=evolution_memory,
            authority=authority,
            policy=resolved_policy,
        )
        self._loop = AutonomousEvolutionLoop(
            failure_miner=failure_miner,
            skill_forge=skill_forge,
            patch_generator=_MemoryAwarePatchGenerator(patch_generator, self._coordinator),
            secure_sandbox=_MemoryAwareSandbox(secure_sandbox, self._coordinator),
            shadow_evaluator=_MemoryAwareShadowEvaluator(shadow_evaluator, self._coordinator),
            lifecycle=lifecycle,
            baseline_runner=baseline_runner,
            candidate_runner=candidate_runner,
            commands_factory=_MemoryAwareCommandsFactory(commands_factory, self._coordinator),
            budget=budget,
            policy=resolved_policy,
        )

    @property
    def lifecycle(self):
        return self._loop.lifecycle

    @property
    def budget(self):
        return self._loop.budget

    @property
    def policy(self):
        return self._loop.policy

    def run(self, *, seeds, source_root, baseline_sha) -> AutonomousEvolutionReport:
        report = self._loop.run(seeds=seeds, source_root=source_root, baseline_sha=baseline_sha)
        for candidate_report in report.outcomes:
            if candidate_report.outcome.value == EvolutionMemoryOutcome.APPROVAL_REQUIRED.value:
                self._coordinator.record_latest(
                    candidate_id=candidate_report.candidate_id,
                    outcome=EvolutionMemoryOutcome.APPROVAL_REQUIRED,
                    reasons=candidate_report.reasons,
                    evaluation_id=candidate_report.latest_shadow_report_id,
                )
            elif candidate_report.outcome.value == EvolutionMemoryOutcome.REJECTED.value:
                self._coordinator.record_latest(
                    candidate_id=candidate_report.candidate_id,
                    outcome=EvolutionMemoryOutcome.REJECTED,
                    reasons=candidate_report.reasons,
                    evaluation_id=candidate_report.latest_shadow_report_id,
                )
            elif candidate_report.outcome.value == EvolutionMemoryOutcome.BLOCKED.value:
                self._coordinator.record_latest(
                    candidate_id=candidate_report.candidate_id,
                    outcome=EvolutionMemoryOutcome.BLOCKED,
                    reasons=candidate_report.reasons,
                    evaluation_id=candidate_report.latest_shadow_report_id,
                )
        return report
