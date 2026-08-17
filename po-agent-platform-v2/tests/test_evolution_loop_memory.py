from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from po_agent.harness.eval_store import EvalSeed
from po_agent.harness.evolution_budget import EvolutionBudget, EvolutionBudgetPolicy
from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, PromotionPolicy
from po_agent.harness.evolution_loop import AutonomousEvolutionPolicy, PatchGenerationContext
from po_agent.harness.evolution_loop_memory import MemoryIntegratedAutonomousEvolutionLoop
from po_agent.harness.evolution_memory import EvolutionMemory, EvolutionMemoryOutcome, EvolutionMemoryPolicy
from po_agent.harness.failure_miner import FailureMiner
from po_agent.harness.sandbox_patch import (
    PatchEvaluationReport,
    PatchOperation,
    PatchProposal,
    PatchValidationEvidence,
    PatchVerdict,
    ProposedFileChange,
)
from po_agent.harness.shadow_evaluation import ShadowEvaluator, ShadowObservation
from po_agent.harness.skill_forge import SkillForge


BASELINE_SHA = "a" * 40


def _seed(eval_id: str) -> EvalSeed:
    return EvalSeed(
        eval_id=eval_id,
        source_trace_id=f"trace-{eval_id}",
        source_feedback_id=None,
        created_at=datetime.now(timezone.utc).isoformat(),
        query="Покажи задачи по OLAP",
        expected_intent="task_search_product",
        source_versions={"skill_id": "task_search"},
    )


class StablePatchGenerator:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, context: PatchGenerationContext) -> PatchProposal:
        self.calls += 1
        return PatchProposal(
            proposal_id=f"proposal-{self.calls}",
            created_at=datetime.now(timezone.utc).isoformat(),
            source_candidate_id=context.candidate.candidate_id,
            source_skill_artifact_id=context.artifact.artifact_id,
            rationale="same semantic patch",
            baseline_sha=context.baseline_sha,
            changes=(
                ProposedFileChange(
                    path="po-agent-platform-v2/src/po_agent/harness/generated_candidate.py",
                    operation=PatchOperation.CREATE,
                    content="VALUE = 1\n",
                ),
            ),
            acceptance_contract=dict(context.artifact.acceptance_contract),
            shadow_eval_plan=dict(context.artifact.shadow_eval_plan),
            risk_classification="low",
        )


class SandboxFake:
    def __init__(self, verdict: PatchVerdict) -> None:
        self.verdict = verdict
        self.calls = 0

    def run(self, *, proposal, source_root, commands):
        self.calls += 1
        report = PatchEvaluationReport(
            report_id=f"sandbox-{self.calls}",
            proposal_id=proposal.proposal_id,
            baseline_sha=proposal.baseline_sha,
            changed_files=proposal.target_files,
            verdict=self.verdict,
            reasons=("synthetic",),
            evidence=PatchValidationEvidence(
                targeted_tests_passed=self.verdict is PatchVerdict.APPROVAL_REQUIRED,
                full_regression_passed=self.verdict is PatchVerdict.APPROVAL_REQUIRED,
                acceptance_contract_passed=self.verdict is PatchVerdict.APPROVAL_REQUIRED,
            ),
        )
        return SimpleNamespace(evaluation_report=report)


class BaselineRunner:
    def run(self, seed, candidate):
        return ShadowObservation(intent="wrong_intent")


class CandidateRunner:
    def __init__(self, regress: bool = False) -> None:
        self.regress = regress

    def run(self, seed, candidate):
        if self.regress:
            return ShadowObservation(intent="wrong_intent", wrong_skill_selection=True)
        return ShadowObservation(intent=seed.expected_intent)


def _loop(*, memory, sandbox, attempts=2, candidate_runner=None):
    return MemoryIntegratedAutonomousEvolutionLoop(
        evolution_memory=memory,
        failure_miner=FailureMiner(),
        skill_forge=SkillForge(),
        patch_generator=StablePatchGenerator(),
        secure_sandbox=sandbox,
        shadow_evaluator=ShadowEvaluator(),
        lifecycle=ControlledImprovementLifecycle(PromotionPolicy(min_corpus_size=2, min_pass_rate=1.0)),
        baseline_runner=BaselineRunner(),
        candidate_runner=candidate_runner or CandidateRunner(),
        commands_factory=lambda proposal: [SimpleNamespace(name="targeted")],
        budget=EvolutionBudget(
            EvolutionBudgetPolicy(
                max_clusters=2,
                max_candidates=2,
                max_attempts_per_candidate=attempts,
                max_llm_calls=20,
                max_elapsed_seconds=100,
            )
        ),
        policy=AutonomousEvolutionPolicy(min_failure_occurrences=2, min_improved_cases=1),
    )


def test_blocked_outcome_is_written_to_memory() -> None:
    memory = EvolutionMemory(EvolutionMemoryPolicy(max_same_fingerprint_failures=2))
    sandbox = SandboxFake(PatchVerdict.BLOCKED)
    loop = _loop(memory=memory, sandbox=sandbox, attempts=1)
    report = loop.run(seeds=[_seed("e1"), _seed("e2")], source_root="/unused", baseline_sha=BASELINE_SHA)
    assert report.outcomes[0].outcome.value == "blocked"
    assert any(entry.outcome is EvolutionMemoryOutcome.BLOCKED for entry in memory.snapshot())


def test_known_bad_fingerprint_is_stopped_before_second_sandbox_execution() -> None:
    memory = EvolutionMemory(EvolutionMemoryPolicy(max_same_fingerprint_failures=1))
    first_sandbox = SandboxFake(PatchVerdict.BLOCKED)
    first = _loop(memory=memory, sandbox=first_sandbox, attempts=1)
    first.run(seeds=[_seed("e1"), _seed("e2")], source_root="/unused", baseline_sha=BASELINE_SHA)
    assert first_sandbox.calls == 1

    second_sandbox = SandboxFake(PatchVerdict.APPROVAL_REQUIRED)
    second = _loop(memory=memory, sandbox=second_sandbox, attempts=1)
    report = second.run(seeds=[_seed("e3"), _seed("e4")], source_root="/unused", baseline_sha=BASELINE_SHA)
    assert second_sandbox.calls == 0
    assert report.outcomes[0].outcome.value == "blocked"
    assert "empty_validation_plan" in report.outcomes[0].reasons


def test_shadow_regression_is_recorded_as_rejected_memory() -> None:
    memory = EvolutionMemory()
    sandbox = SandboxFake(PatchVerdict.APPROVAL_REQUIRED)
    loop = _loop(memory=memory, sandbox=sandbox, attempts=1, candidate_runner=CandidateRunner(regress=True))
    report = loop.run(seeds=[_seed("e1"), _seed("e2")], source_root="/unused", baseline_sha=BASELINE_SHA)
    assert report.outcomes[0].outcome.value == "rejected"
    assert any(entry.outcome is EvolutionMemoryOutcome.REJECTED for entry in memory.snapshot())


def test_green_candidate_records_approval_required_but_never_approval() -> None:
    memory = EvolutionMemory()
    sandbox = SandboxFake(PatchVerdict.APPROVAL_REQUIRED)
    loop = _loop(memory=memory, sandbox=sandbox, attempts=1)
    report = loop.run(seeds=[_seed("e1"), _seed("e2")], source_root="/unused", baseline_sha=BASELINE_SHA)
    outcome = report.outcomes[0]
    assert outcome.outcome.value == "approval_required"
    assert any(entry.outcome is EvolutionMemoryOutcome.APPROVAL_REQUIRED for entry in memory.snapshot())
    record = loop.lifecycle.get(outcome.candidate_id)
    assert record.approved_by is None
    assert record.promoted_ref is None


def test_external_write_without_wrapper_authority_remains_blocked() -> None:
    memory = EvolutionMemory()
    sandbox = SandboxFake(PatchVerdict.APPROVAL_REQUIRED)
    loop = _loop(memory=memory, sandbox=sandbox, attempts=1)
    assert not hasattr(loop, "_MemoryIntegratedAutonomousEvolutionLoop__write_authority")
    assert not hasattr(memory, "_EvolutionMemory__write_authority")
    assert not hasattr(memory, "_entries")
    entry = next(iter(memory.snapshot()), None)
    assert entry is None
    from po_agent.harness.evolution_memory import EvolutionMemoryEntry
    forged = EvolutionMemoryEntry.create(
        failure_key="forged",
        candidate_id="attacker",
        outcome=EvolutionMemoryOutcome.PROMOTED,
        target_files=("x.py",),
        proposal_material="evil",
    )
    try:
        memory.append(forged)
    except PermissionError:
        pass
    else:
        raise AssertionError("untrusted caller unexpectedly wrote EvolutionMemory")


def test_memory_instance_exposes_no_mutable_internal_collection_or_authority() -> None:
    memory = EvolutionMemory()
    loop = _loop(memory=memory, sandbox=SandboxFake(PatchVerdict.APPROVAL_REQUIRED), attempts=1)
    assert not hasattr(memory, "__dict__")
    assert not hasattr(memory, "_entries")
    assert not hasattr(memory, "_ids")
    assert not hasattr(memory, "_EvolutionMemory__write_authority")
    assert not hasattr(loop, "evolution_memory")
    assert isinstance(memory.snapshot(), tuple)


def test_coordinator_contains_no_writer_closure_or_authority() -> None:
    memory = EvolutionMemory()
    loop = _loop(memory=memory, sandbox=SandboxFake(PatchVerdict.APPROVAL_REQUIRED), attempts=1)
    coordinator = loop._coordinator
    values = vars(coordinator).values()
    assert all(type(value).__name__ != "EvolutionMemoryWriteAuthority" for value in values)
    assert not hasattr(coordinator, "_MemoryCoordinator__write_entry")


def test_legacy_loop_is_not_in_public_harness_api() -> None:
    import po_agent.harness as harness

    assert not hasattr(harness, "AutonomousEvolutionLoop")
    assert "AutonomousEvolutionLoop" not in harness.__all__
    assert hasattr(harness, "MemoryIntegratedAutonomousEvolutionLoop")
