from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from po_agent.harness.eval_store import EvalSeed
from po_agent.harness.evolution_budget import EvolutionBudget, EvolutionBudgetPolicy
from po_agent.harness.evolution_lifecycle import ControlledImprovementLifecycle, PromotionPolicy
from po_agent.harness.evolution_loop import (
    AutonomousEvolutionLoop,
    AutonomousEvolutionPolicy,
    EvolutionOutcome,
    PatchGenerationContext,
)
from po_agent.harness.failure_miner import FailureMiner
from po_agent.harness.sandbox_patch import (
    PatchEvaluationReport,
    PatchProposal,
    PatchValidationEvidence,
    PatchVerdict,
    ProposedFileChange,
    PatchOperation,
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


class PatchGeneratorFake:
    def __init__(self, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls = 0

    def generate(self, context: PatchGenerationContext) -> PatchProposal:
        self.calls += 1
        if self.fail_first and self.calls == 1:
            raise RuntimeError("synthetic generation failure")
        return PatchProposal(
            proposal_id=f"proposal-{self.calls}",
            created_at=datetime.now(timezone.utc).isoformat(),
            source_candidate_id=context.candidate.candidate_id,
            source_skill_artifact_id=context.artifact.artifact_id,
            rationale="test",
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
    def __init__(self, verdict: PatchVerdict = PatchVerdict.APPROVAL_REQUIRED) -> None:
        self.verdict = verdict
        self.calls = 0

    def run(self, *, proposal, source_root, commands):
        self.calls += 1
        reasons = (
            ("all_automated_gates_passed_human_approval_required",)
            if self.verdict is PatchVerdict.APPROVAL_REQUIRED
            else ("synthetic_failure",)
        )
        report = PatchEvaluationReport(
            report_id=f"report-{self.calls}",
            proposal_id=proposal.proposal_id,
            baseline_sha=proposal.baseline_sha,
            changed_files=proposal.target_files,
            verdict=self.verdict,
            reasons=reasons,
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
    def __init__(self, *, regress: bool = False) -> None:
        self.regress = regress

    def run(self, seed, candidate):
        if self.regress:
            return ShadowObservation(intent="wrong_intent", wrong_skill_selection=True)
        return ShadowObservation(intent=seed.expected_intent)


def _loop(*, generator=None, sandbox=None, candidate_runner=None, attempts=2):
    return AutonomousEvolutionLoop(
        failure_miner=FailureMiner(),
        skill_forge=SkillForge(),
        patch_generator=generator or PatchGeneratorFake(),
        secure_sandbox=sandbox or SandboxFake(),
        shadow_evaluator=ShadowEvaluator(),
        lifecycle=ControlledImprovementLifecycle(
            PromotionPolicy(min_corpus_size=2, min_pass_rate=1.0)
        ),
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


def test_green_candidate_stops_at_human_approval_boundary() -> None:
    loop = _loop()
    report = loop.run(
        seeds=[_seed("e1"), _seed("e2")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    assert len(report.outcomes) == 1
    outcome = report.outcomes[0]
    assert outcome.outcome is EvolutionOutcome.APPROVAL_REQUIRED
    assert outcome.lifecycle_state == "approval_required"
    record = loop.lifecycle.get(outcome.candidate_id)
    assert record is not None
    assert record.approved_by is None
    assert record.promoted_ref is None


def test_no_repeated_cluster_means_no_autonomous_change() -> None:
    loop = _loop()
    report = loop.run(
        seeds=[_seed("e1")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    assert report.mined_cluster_count == 0
    assert report.outcomes == ()


def test_blocked_sandbox_never_reaches_shadow_or_approval() -> None:
    loop = _loop(sandbox=SandboxFake(PatchVerdict.BLOCKED), attempts=1)
    report = loop.run(
        seeds=[_seed("e1"), _seed("e2")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    outcome = report.outcomes[0]
    assert outcome.outcome is EvolutionOutcome.BLOCKED
    assert outcome.lifecycle_state == "rejected"
    assert outcome.latest_shadow_report_id is None


def test_shadow_safety_regression_is_rejected() -> None:
    loop = _loop(candidate_runner=CandidateRunner(regress=True), attempts=1)
    report = loop.run(
        seeds=[_seed("e1"), _seed("e2")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    outcome = report.outcomes[0]
    assert outcome.outcome is EvolutionOutcome.REJECTED
    assert outcome.lifecycle_state == "rejected"
    assert "shadow_safety_regression" in outcome.reasons


def test_patch_generation_can_retry_within_bound() -> None:
    generator = PatchGeneratorFake(fail_first=True)
    loop = _loop(generator=generator, attempts=2)
    report = loop.run(
        seeds=[_seed("e1"), _seed("e2")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    assert generator.calls == 2
    assert report.outcomes[0].outcome is EvolutionOutcome.APPROVAL_REQUIRED
    assert len(report.outcomes[0].attempts) == 2


def test_patch_generation_budget_exhaustion_fails_closed() -> None:
    generator = PatchGeneratorFake(fail_first=True)
    loop = _loop(generator=generator, attempts=1)
    report = loop.run(
        seeds=[_seed("e1"), _seed("e2")],
        source_root="/unused/by/fake",
        baseline_sha=BASELINE_SHA,
    )
    assert report.outcomes[0].outcome is EvolutionOutcome.REJECTED
    assert report.outcomes[0].lifecycle_state == "rejected"


def test_empty_seed_set_is_no_action() -> None:
    loop = _loop()
    report = loop.run(seeds=[], source_root="/unused", baseline_sha=BASELINE_SHA)
    assert report.outcomes == ()
    assert report.mined_cluster_count == 0
