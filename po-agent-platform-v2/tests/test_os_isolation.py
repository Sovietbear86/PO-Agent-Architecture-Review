from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from po_agent.harness.hardened_sandbox_executor import (
    HardenedExecutorPolicy,
    HardenedSandboxExecutor,
)
from po_agent.harness.os_isolation import (
    DockerIsolationBackend,
    DockerIsolationPolicy,
    IsolationLevel,
    IsolatedProcessResult,
    WorkspaceOnlyIsolationBackend,
)
from po_agent.harness.sandbox_evidence import ValidationCommand


PINNED_IMAGE = "python:3.12-slim@sha256:" + "a" * 64


def _command() -> ValidationCommand:
    return ValidationCommand(
        name="targeted_tests",
        argv=("python", "-m", "pytest", "tests/test_sample.py"),
        timeout_seconds=30,
    )


def test_docker_policy_requires_digest_pinned_image() -> None:
    with pytest.raises(ValueError, match="pinned"):
        DockerIsolationPolicy(image="python:3.12-slim")


def test_workspace_backend_is_explicitly_not_hard_os() -> None:
    assert WorkspaceOnlyIsolationBackend().isolation_level is IsolationLevel.WORKSPACE_ONLY


def test_executor_fails_closed_when_hard_os_required(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="HARD_OS"):
        HardenedSandboxExecutor(
            HardenedExecutorPolicy(require_os_isolation=True),
            isolation_backend=WorkspaceOnlyIsolationBackend(),
        )


def test_docker_backend_declares_hard_os() -> None:
    backend = DockerIsolationBackend(DockerIsolationPolicy(image=PINNED_IMAGE), launcher=lambda *a, **k: None)
    assert backend.isolation_level is IsolationLevel.HARD_OS


def test_docker_invocation_has_required_security_controls(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def launcher(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    backend = DockerIsolationBackend(
        DockerIsolationPolicy(image=PINNED_IMAGE),
        launcher=launcher,
    )
    result = backend.execute(_command(), tmp_path, {"LANG": "C"})

    argv = captured["argv"]
    assert isinstance(argv, list)
    assert "--network=none" in argv
    assert "--read-only" in argv
    assert "--cap-drop=ALL" in argv
    assert "--security-opt=no-new-privileges:true" in argv
    assert any(str(item).startswith("--pids-limit=") for item in argv)
    assert any(str(item).startswith("--memory=") for item in argv)
    assert any(str(item).startswith("--cpus=") for item in argv)
    assert any(str(item).startswith("--tmpfs=/tmp:rw,noexec,nosuid,nodev") for item in argv)
    assert "--workdir" in argv
    assert "/workspace" in argv
    assert "--mount" in argv
    assert any(str(item).startswith(f"type=bind,src={tmp_path.resolve()},dst=/workspace,rw") for item in argv)
    assert PINNED_IMAGE in argv
    assert argv[-4:] == ["python", "-m", "pytest", "tests/test_sample.py"]
    assert captured["kwargs"]["shell"] is False
    assert result.returncode == 0


def test_container_command_never_uses_shell_string(tmp_path: Path) -> None:
    captured = {}

    def launcher(argv, **kwargs):
        captured["argv"] = argv
        captured["shell"] = kwargs["shell"]
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    backend = DockerIsolationBackend(DockerIsolationPolicy(image=PINNED_IMAGE), launcher=launcher)
    backend.execute(
        ValidationCommand(name="x", argv=("python", "-c", "print('x')"), timeout_seconds=5),
        tmp_path,
        {},
    )
    assert isinstance(captured["argv"], list)
    assert captured["shell"] is False


def test_timeout_is_fail_closed(tmp_path: Path) -> None:
    def launcher(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"], output="partial", stderr="slow")

    backend = DockerIsolationBackend(DockerIsolationPolicy(image=PINNED_IMAGE), launcher=launcher)
    result = backend.execute(_command(), tmp_path, {})
    assert result.timed_out is True
    assert result.returncode == 124
    assert result.stdout == "partial"
    assert result.stderr == "slow"


def test_production_executor_accepts_hard_os_backend(tmp_path: Path) -> None:
    def launcher(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    backend = DockerIsolationBackend(DockerIsolationPolicy(image=PINNED_IMAGE), launcher=launcher)
    executor = HardenedSandboxExecutor(
        HardenedExecutorPolicy(require_os_isolation=True),
        signing_key=b"x" * 32,
        isolation_backend=backend,
    )
    observation = executor(_command(), tmp_path)
    assert executor.isolation_level is IsolationLevel.HARD_OS
    assert observation.passed
    assert observation.trusted
    assert executor.verify(_command(), observation)


def test_backend_result_contract_is_data_only() -> None:
    result = IsolatedProcessResult(returncode=0, stdout="x", stderr="", timed_out=False)
    assert result.returncode == 0
    assert result.stdout == "x"
