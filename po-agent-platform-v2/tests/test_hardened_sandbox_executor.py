import sys
from dataclasses import replace
from pathlib import Path

import pytest

from po_agent.harness.hardened_sandbox_executor import (
    EVIDENCE_PREFIX,
    HardenedExecutorPolicy,
    HardenedSandboxExecutor,
    TrustedSandboxEvidenceRunner,
)
from po_agent.harness.sandbox_evidence import ValidationCommand
from po_agent.harness.sandbox_patch import PatchOperation, PatchProposal, ProposedFileChange


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


def executor():
    return HardenedSandboxExecutor(
        HardenedExecutorPolicy(allowed_executables=(Path(sys.executable).name,))
    )


def command(name, code, *, timeout=10, required=True):
    return ValidationCommand(name, (sys.executable, "-c", code), timeout_seconds=timeout, required=required)


def test_executes_structured_argv_and_signs_observation(tmp_path):
    exe = executor()
    cmd = command("targeted_tests", "print('ok')")
    observation = exe(cmd, tmp_path)
    assert observation.passed
    assert observation.trusted is True
    assert observation.signature
    assert observation.command_sha256
    assert observation.stdout_sha256
    assert exe.verify(cmd, observation)


def test_forged_observation_is_rejected(tmp_path):
    exe = executor()
    cmd = command("targeted_tests", "print('ok')")
    observation = exe(cmd, tmp_path)
    forged = replace(observation, stdout="forged")
    assert not exe.verify(cmd, forged)


def test_command_binding_rejects_replay_for_other_command(tmp_path):
    exe = executor()
    first = command("targeted_tests", "print('one')")
    second = command("targeted_tests", "print('two')")
    observation = exe(first, tmp_path)
    assert not exe.verify(second, observation)


def test_disallowed_executable_rejected_before_execution(tmp_path):
    exe = executor()
    cmd = ValidationCommand("targeted_tests", ("definitely-not-allowed", "x"))
    with pytest.raises(ValueError, match="not allowed"):
        exe(cmd, tmp_path)


def test_timeout_is_signed_failure(tmp_path):
    exe = executor()
    cmd = command("targeted_tests", "import time; time.sleep(2)", timeout=1)
    observation = exe(cmd, tmp_path)
    assert observation.timed_out is True
    assert observation.passed is False
    assert exe.verify(cmd, observation)


def test_environment_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("SHOULD_NOT_LEAK", "secret")
    exe = executor()
    cmd = command("targeted_tests", "import os; print(os.environ.get('SHOULD_NOT_LEAK', 'missing'))")
    observation = exe(cmd, tmp_path)
    assert observation.stdout.strip() == "missing"


def test_workspace_digest_detects_mutation(tmp_path):
    exe = executor()
    cmd = command("targeted_tests", "from pathlib import Path; Path('created.txt').write_text('x')")
    observation = exe(cmd, tmp_path)
    assert observation.workspace_before_sha256 != observation.workspace_after_sha256
    assert exe.verify(cmd, observation)


def test_trusted_runner_derives_green_from_signed_commands(tmp_path):
    exe = executor()
    metrics = '{"new_code_regressions":0,"safety_regressions":0,"improved_cases":2}'
    commands = (
        command("targeted_tests", "print('targeted ok')"),
        command("full_regression", "print('full ok')"),
        command("acceptance_contract", "print('acceptance ok')"),
        command("evidence_metrics", f"print({EVIDENCE_PREFIX!r} + {metrics!r})"),
    )
    report = TrustedSandboxEvidenceRunner(exe).run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands
    )
    assert report.evidence.targeted_tests_passed is True
    assert report.evidence.full_regression_passed is True
    assert report.evidence.acceptance_contract_passed is True
    assert report.evidence.improved_cases == 2
    assert all(item.trusted for item in report.observations)


def test_trusted_runner_cannot_be_given_manual_green_inputs(tmp_path):
    runner = TrustedSandboxEvidenceRunner(executor())
    with pytest.raises(TypeError):
        runner.run(
            proposal=proposal(),
            sandbox_root=tmp_path,
            commands=(),
            metrics={"new_code_regressions": 0},
            acceptance_contract_passed=True,
        )


def test_failed_acceptance_command_prevents_green(tmp_path):
    exe = executor()
    commands = (
        command("targeted_tests", "pass"),
        command("full_regression", "pass"),
        command("acceptance_contract", "raise SystemExit(1)"),
        command("evidence_metrics", f"print({EVIDENCE_PREFIX!r} + '{{}}')"),
    )
    evidence = TrustedSandboxEvidenceRunner(exe).run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands
    ).evidence
    assert evidence.targeted_tests_passed is False
    assert evidence.full_regression_passed is False
    assert evidence.acceptance_contract_passed is False


def test_metrics_failure_is_fail_closed(tmp_path):
    exe = executor()
    commands = (
        command("targeted_tests", "pass"),
        command("full_regression", "pass"),
        command("acceptance_contract", "pass"),
        command("evidence_metrics", "raise SystemExit(1)"),
    )
    evidence = TrustedSandboxEvidenceRunner(exe).run(
        proposal=proposal(), sandbox_root=tmp_path, commands=commands
    ).evidence
    assert evidence.provider_errors == 1
    assert evidence.targeted_tests_passed is False


def test_missing_evidence_payload_rejected(tmp_path):
    exe = executor()
    commands = (
        command("targeted_tests", "pass"),
        command("full_regression", "pass"),
        command("acceptance_contract", "pass"),
        command("evidence_metrics", "print('not evidence')"),
    )
    with pytest.raises(ValueError, match="exactly one evidence payload"):
        TrustedSandboxEvidenceRunner(exe).run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands
        )


def test_metrics_command_cannot_mutate_workspace_and_still_green(tmp_path):
    exe = executor()
    code = f"from pathlib import Path; Path('x.txt').write_text('x'); print({EVIDENCE_PREFIX!r} + '{{}}')"
    commands = (
        command("targeted_tests", "pass"),
        command("full_regression", "pass"),
        command("acceptance_contract", "pass"),
        command("evidence_metrics", code),
    )
    with pytest.raises(ValueError, match="mutated sandbox"):
        TrustedSandboxEvidenceRunner(exe).run(
            proposal=proposal(), sandbox_root=tmp_path, commands=commands
        )
