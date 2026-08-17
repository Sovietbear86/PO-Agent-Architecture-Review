from __future__ import annotations

from pathlib import Path

import pytest

from po_agent.harness.improvement_candidates import ImprovementCandidate
from po_agent.harness.sandbox_patch import (
    PatchEvaluationGate,
    PatchOperation,
    PatchSynthesisPolicy,
    PatchValidationEvidence,
    PatchVerdict,
    ProposedFileChange,
    SandboxPatchApplicator,
    SandboxPatchSynthesizer,
)


def candidate() -> ImprovementCandidate:
    return ImprovementCandidate(
        candidate_id="cand-1",
        created_at="2026-08-17T00:00:00+00:00",
        kind="forge:routing_metadata",
        title="Improve semantic metadata",
        rationale="Observed a grounded routing failure cluster.",
        source_failure_key="intent_mismatch:sprint_health",
        source_eval_ids=("eval-1",),
        proposed_change={
            "forge_artifact_id": "forge-1",
            "acceptance_contract": {"must_pass_source_eval_ids": ["eval-1"]},
            "shadow_eval_plan": {"mode": "baseline_vs_candidate"},
            "apply": False,
            "executable": False,
        },
    )


def change(path: str = "po-agent-platform-v2/src/po_agent/harness/demo.py") -> ProposedFileChange:
    return ProposedFileChange(path=path, operation=PatchOperation.CREATE, content="VALUE = 1\n")


def proposal():
    return SandboxPatchSynthesizer().synthesize(
        candidate=candidate(),
        baseline_sha="abc123",
        changes=[change()],
        authorized_target_files=[change().path],
    )


def test_synthesizer_creates_non_executable_human_gated_proposal():
    result = proposal()
    assert result.executable is False
    assert result.apply is False
    assert result.requires_human_approval is True
    assert result.source_skill_artifact_id == "forge-1"


def test_synthesizer_requires_skill_forge_origin():
    item = candidate()
    item.proposed_change.pop("forge_artifact_id")
    with pytest.raises(ValueError, match="Skill Forge"):
        SandboxPatchSynthesizer().synthesize(
            candidate=item,
            baseline_sha="abc",
            changes=[change()],
            authorized_target_files=[change().path],
        )


def test_synthesizer_rejects_path_traversal():
    bad = ProposedFileChange(path="../outside.py", operation=PatchOperation.CREATE, content="x=1\n")
    with pytest.raises(ValueError, match="unsafe repository path"):
        SandboxPatchSynthesizer().synthesize(
            candidate=candidate(), baseline_sha="abc", changes=[bad], authorized_target_files=[bad.path]
        )


def test_synthesizer_rejects_undeclared_target():
    with pytest.raises(ValueError, match="not authorized"):
        SandboxPatchSynthesizer().synthesize(
            candidate=candidate(), baseline_sha="abc", changes=[change()], authorized_target_files=[]
        )


def test_synthesizer_enforces_scope_bounds():
    policy = PatchSynthesisPolicy(max_files=1)
    first = change("po-agent-platform-v2/src/po_agent/harness/a.py")
    second = change("po-agent-platform-v2/src/po_agent/harness/b.py")
    with pytest.raises(ValueError, match="max_files"):
        SandboxPatchSynthesizer(policy).synthesize(
            candidate=candidate(),
            baseline_sha="abc",
            changes=[first, second],
            authorized_target_files=[first.path, second.path],
        )


def test_sandbox_applicator_changes_only_sandbox(tmp_path: Path):
    result = SandboxPatchApplicator().apply(proposal(), tmp_path)
    target = tmp_path / change().path
    assert target.read_text(encoding="utf-8") == "VALUE = 1\n"
    assert result.changed_files == (change().path,)


def test_sandbox_applicator_checks_expected_baseline_hash(tmp_path: Path):
    target = tmp_path / "po-agent-platform-v2/src/po_agent/harness/demo.py"
    target.parent.mkdir(parents=True)
    target.write_text("OLD\n", encoding="utf-8")
    replacement = ProposedFileChange(
        path=change().path,
        operation=PatchOperation.REPLACE,
        content="NEW\n",
        expected_before_sha256="wrong",
    )
    p = SandboxPatchSynthesizer().synthesize(
        candidate=candidate(), baseline_sha="abc", changes=[replacement], authorized_target_files=[replacement.path]
    )
    with pytest.raises(ValueError, match="baseline content mismatch"):
        SandboxPatchApplicator().apply(p, tmp_path)


def test_safety_regression_is_blocked():
    report = PatchEvaluationGate.evaluate(
        proposal(),
        PatchValidationEvidence(
            targeted_tests_passed=True,
            full_regression_passed=True,
            acceptance_contract_passed=True,
            safety_regressions=1,
        ),
    )
    assert report.verdict is PatchVerdict.BLOCKED


def test_regular_regression_is_rejected():
    report = PatchEvaluationGate.evaluate(
        proposal(),
        PatchValidationEvidence(
            targeted_tests_passed=True,
            full_regression_passed=True,
            acceptance_contract_passed=True,
            regressed_cases=1,
        ),
    )
    assert report.verdict is PatchVerdict.REJECTED


def test_green_candidate_stops_at_approval_required():
    report = PatchEvaluationGate.evaluate(
        proposal(),
        PatchValidationEvidence(
            targeted_tests_passed=True,
            full_regression_passed=True,
            acceptance_contract_passed=True,
            improved_cases=1,
        ),
    )
    assert report.verdict is PatchVerdict.APPROVAL_REQUIRED
    assert report.requires_human_approval is True


def test_provider_failure_fails_closed():
    report = PatchEvaluationGate.evaluate(
        proposal(),
        PatchValidationEvidence(
            targeted_tests_passed=True,
            full_regression_passed=True,
            acceptance_contract_passed=True,
            provider_errors=1,
        ),
    )
    assert report.verdict is PatchVerdict.BLOCKED
