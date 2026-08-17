from pathlib import Path
import pytest

from po_agent.harness.sandbox_evidence import (
    CommandObservation,
    SandboxEvidencePolicy,
    SandboxEvidenceRunner,
    ValidationCommand,
)
from po_agent.harness.sandbox_patch import (
    PatchOperation,
    PatchProposal,
    ProposedFileChange,
)


def proposal():
    return PatchProposal(
        proposal_id="p1",
        created_at="2026-08-17T00:00:00+00:00",
        source_candidate_id="c1",
        source_skill_artifact_id="a1",
        rationale="test",
        baseline_sha="abc",
        changes=(ProposedFileChange("po-agent-platform-v2/tests/x.py", PatchOperation.CREATE, "x"),),
        acceptance_contract={},
        shadow_eval_plan={},
        risk_classification="medium",
    )


def commands():
    return (
        ValidationCommand("targeted_tests", ("pytest", "targeted")),
        ValidationCommand("full_regression", ("pytest", "all")),
    )


def passing_executor(command, root):
    return CommandObservation(command.name, 0, stdout="ok")


def test_green_plan_produces_green_evidence(tmp_path):
    report = SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor
    )
    assert report.evidence.targeted_tests_passed is True
    assert report.evidence.full_regression_passed is True
    assert report.evidence.acceptance_contract_passed is True


def test_failed_required_command_fails_all_required_gates(tmp_path):
    def executor(command, root):
        return CommandObservation(command.name, 1 if command.name == "targeted_tests" else 0)
    evidence = SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=executor
    ).evidence
    assert evidence.targeted_tests_passed is False
    assert evidence.full_regression_passed is False
    assert evidence.acceptance_contract_passed is False


def test_timeout_is_failure(tmp_path):
    def executor(command, root):
        return CommandObservation(command.name, 0, timed_out=command.name == "targeted_tests")
    assert not SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=executor
    ).evidence.targeted_tests_passed


def test_executor_exception_fails_closed(tmp_path):
    def executor(command, root):
        if command.name == "targeted_tests":
            raise RuntimeError("boom")
        return CommandObservation(command.name, 0)
    report = SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=executor
    )
    assert report.observations[0].passed is False
    assert "executor_error:RuntimeError" in report.observations[0].stderr


def test_requires_existing_sandbox(tmp_path):
    with pytest.raises(ValueError, match="existing directory"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path / "missing", commands=commands(), executor=passing_executor
        )


def test_requires_targeted_command(tmp_path):
    with pytest.raises(ValueError, match="targeted_tests"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path,
            commands=(ValidationCommand("full_regression", ("pytest",)),), executor=passing_executor
        )


def test_requires_full_regression_command(tmp_path):
    with pytest.raises(ValueError, match="full_regression"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path,
            commands=(ValidationCommand("targeted_tests", ("pytest",)),), executor=passing_executor
        )


def test_rejects_duplicate_command_names(tmp_path):
    duplicate = (ValidationCommand("targeted_tests", ("a",)), ValidationCommand("targeted_tests", ("b",)))
    with pytest.raises(ValueError, match="duplicate"):
        SandboxEvidenceRunner(SandboxEvidencePolicy(require_full_regression=False)).run(
            proposal=proposal(), sandbox_root=tmp_path, commands=duplicate, executor=passing_executor
        )


def test_enforces_command_count(tmp_path):
    policy = SandboxEvidencePolicy(max_commands=1)
    with pytest.raises(ValueError, match="max_commands"):
        SandboxEvidenceRunner(policy).run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor
        )


def test_enforces_timeout_policy(tmp_path):
    plan = (ValidationCommand("targeted_tests", ("x",), timeout_seconds=901), ValidationCommand("full_regression", ("y",)))
    with pytest.raises(ValueError, match="timeout exceeds policy"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path, commands=plan, executor=passing_executor
        )


def test_rejects_mismatched_observation_name(tmp_path):
    def executor(command, root):
        return CommandObservation("other", 0)
    with pytest.raises(ValueError, match="mismatched"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=executor
        )


def test_metrics_are_transferred(tmp_path):
    evidence = SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor,
        metrics={"improved_cases": 3, "candidate_latency_ms": 12, "provider_errors": 1},
    ).evidence
    assert evidence.improved_cases == 3
    assert evidence.candidate_latency_ms == 12
    assert evidence.provider_errors == 1


def test_negative_metric_rejected(tmp_path):
    with pytest.raises(ValueError, match="invalid evidence metric"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor,
            metrics={"safety_regressions": -1},
        )


def test_boolean_metric_rejected(tmp_path):
    with pytest.raises(ValueError, match="invalid evidence metric"):
        SandboxEvidenceRunner().run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor,
            metrics={"provider_errors": True},
        )


def test_optional_failed_command_does_not_poison_required_gates(tmp_path):
    plan = commands() + (ValidationCommand("performance", ("bench",), required=False),)
    def executor(command, root):
        return CommandObservation(command.name, 1 if command.name == "performance" else 0)
    evidence = SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=plan, executor=executor
    ).evidence
    assert evidence.targeted_tests_passed
    assert evidence.full_regression_passed


def test_runner_does_not_mutate_sandbox(tmp_path):
    marker = tmp_path / "marker.txt"
    marker.write_text("before")
    SandboxEvidenceRunner().run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands(), executor=passing_executor
    )
    assert marker.read_text() == "before"
