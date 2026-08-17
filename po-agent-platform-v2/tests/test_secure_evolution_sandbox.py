from __future__ import annotations

from pathlib import Path

import pytest

from po_agent.harness.hardened_sandbox_executor import (
    EVIDENCE_PREFIX,
    HardenedExecutorPolicy,
    HardenedSandboxExecutor,
    TrustedSandboxEvidenceRunner,
)
from po_agent.harness.os_isolation import IsolationLevel, IsolatedProcessResult, WorkspaceOnlyIsolationBackend
from po_agent.harness.sandbox_evidence import ValidationCommand
from po_agent.harness.sandbox_patch import (
    PatchOperation,
    PatchProposal,
    PatchVerdict,
    ProposedFileChange,
)
from po_agent.harness.secure_evolution_sandbox import (
    SecureEvolutionSandbox,
    SecureEvolutionSandboxPolicy,
)


class FakeHardOSBackend:
    isolation_level = IsolationLevel.HARD_OS

    def execute(self, command, sandbox_root, env):
        stdout = ""
        if command.name == "evidence_metrics":
            stdout = EVIDENCE_PREFIX + (
                '{"new_code_regressions":0,"safety_regressions":0,'
                '"wrong_skill_selections":0,"hallucinated_entities":0,'
                '"ungrounded_answers":0,"provider_errors":0,'
                '"improved_cases":1,"regressed_cases":0}'
            )
        return IsolatedProcessResult(returncode=0, stdout=stdout)


def _proposal() -> PatchProposal:
    return PatchProposal(
        proposal_id="proposal-1",
        created_at="2026-08-17T00:00:00+00:00",
        source_candidate_id="candidate-1",
        source_skill_artifact_id="forge-1",
        rationale="test candidate",
        baseline_sha="baseline-123",
        changes=(
            ProposedFileChange(
                path="po-agent-platform-v2/src/po_agent/harness/sample.py",
                operation=PatchOperation.REPLACE,
                content="VALUE = 2\n",
            ),
        ),
        acceptance_contract={"required": True},
        shadow_eval_plan={"mode": "baseline_vs_candidate"},
        risk_classification="medium",
    )


def _commands() -> tuple[ValidationCommand, ...]:
    return (
        ValidationCommand("targeted_tests", ("python", "-c", "pass")),
        ValidationCommand("full_regression", ("python", "-c", "pass")),
        ValidationCommand("acceptance_contract", ("python", "-c", "pass")),
        ValidationCommand("evidence_metrics", ("python", "-c", "pass")),
    )


def _source(tmp_path: Path) -> Path:
    source = tmp_path / "repo-source"
    target = source / "po-agent-platform-v2/src/po_agent/harness/sample.py"
    target.parent.mkdir(parents=True)
    target.write_text("VALUE = 1\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git/config").write_text("secret metadata", encoding="utf-8")
    return source


def _runner() -> TrustedSandboxEvidenceRunner:
    executor = HardenedSandboxExecutor(
        HardenedExecutorPolicy(require_os_isolation=True),
        signing_key=b"k" * 32,
        isolation_backend=FakeHardOSBackend(),
    )
    return TrustedSandboxEvidenceRunner(executor)


def test_secure_sandbox_applies_validates_evaluates_and_destroys(tmp_path: Path) -> None:
    source = _source(tmp_path)
    sandbox = SecureEvolutionSandbox(
        _runner(),
        baseline_attestor=lambda _: "baseline-123",
        workspace_parent=tmp_path / "workspaces",
    )
    (tmp_path / "workspaces").mkdir()

    result = sandbox.run(proposal=_proposal(), source_root=source, commands=_commands())

    assert result.evaluation_report.verdict is PatchVerdict.APPROVAL_REQUIRED
    assert result.evidence_report.evidence.improved_cases == 1
    assert result.baseline_tree_sha256 != result.candidate_tree_sha256
    assert result.sandbox_destroyed is True
    assert not Path(result.sandbox_root).exists()
    assert (source / "po-agent-platform-v2/src/po_agent/harness/sample.py").read_text() == "VALUE = 1\n"


def test_secure_sandbox_requires_hard_os_by_default(tmp_path: Path) -> None:
    executor = HardenedSandboxExecutor(
        HardenedExecutorPolicy(require_os_isolation=False),
        isolation_backend=WorkspaceOnlyIsolationBackend(),
    )
    with pytest.raises(ValueError, match="HARD_OS"):
        SecureEvolutionSandbox(
            TrustedSandboxEvidenceRunner(executor),
            baseline_attestor=lambda _: "baseline-123",
        )


def test_secure_sandbox_fails_closed_on_baseline_mismatch(tmp_path: Path) -> None:
    source = _source(tmp_path)
    sandbox = SecureEvolutionSandbox(
        _runner(),
        baseline_attestor=lambda _: "different-sha",
    )
    with pytest.raises(ValueError, match="baseline identity mismatch"):
        sandbox.run(proposal=_proposal(), source_root=source, commands=_commands())


def test_secure_sandbox_requires_attestor_by_default() -> None:
    with pytest.raises(ValueError, match="baseline_attestor"):
        SecureEvolutionSandbox(_runner(), baseline_attestor=None)


def test_git_metadata_never_enters_disposable_workspace(tmp_path: Path) -> None:
    source = _source(tmp_path)
    workspace_parent = tmp_path / "workspaces"
    workspace_parent.mkdir()
    policy = SecureEvolutionSandboxPolicy(retain_failed_workspace=True)
    sandbox = SecureEvolutionSandbox(
        _runner(),
        baseline_attestor=lambda _: "baseline-123",
        policy=policy,
        workspace_parent=workspace_parent,
    )

    result = sandbox.run(proposal=_proposal(), source_root=source, commands=_commands())
    # GREEN/approval-required candidates are destroyed even when failure retention is enabled.
    assert result.sandbox_destroyed is True
    assert not Path(result.sandbox_root).exists()
