from __future__ import annotations

from pathlib import Path
import subprocess

import pytest

from po_agent.harness.hardened_sandbox_executor import HardenedExecutorPolicy, HardenedSandboxExecutor
from po_agent.harness.os_isolation import DockerIsolationBackend, DockerIsolationPolicy
from po_agent.harness.sandbox_evidence import ValidationCommand


PINNED_IMAGE = "python:3.12-slim@sha256:" + "a" * 64


@pytest.mark.parametrize(
    "image",
    [
        "python:latest",
        "python:3.12@sha256:",
        "python:3.12@sha256:abc",
        "python:3.12@sha256:" + "g" * 64,
        "python:3.12@sha256:" + "a" * 63,
        "python:3.12@sha256:" + "a" * 65,
    ],
)
def test_image_digest_validation_is_exact(image: str) -> None:
    with pytest.raises(ValueError, match="64-hex"):
        DockerIsolationPolicy(image=image)


def test_docker_executable_must_be_absolute_and_trusted() -> None:
    with pytest.raises(ValueError, match="absolute"):
        DockerIsolationPolicy(image=PINNED_IMAGE, docker_executable="docker")
    with pytest.raises(ValueError, match="trusted"):
        DockerIsolationPolicy(image=PINNED_IMAGE, docker_executable="/tmp/docker")


def test_container_is_non_root_and_host_env_is_minimal(tmp_path: Path) -> None:
    captured = {}

    def launcher(argv, **kwargs):
        captured["argv"] = argv
        return subprocess.CompletedProcess(argv, 0, stdout="ok", stderr="")

    backend = DockerIsolationBackend(DockerIsolationPolicy(image=PINNED_IMAGE), launcher=launcher)
    executor = HardenedSandboxExecutor(
        HardenedExecutorPolicy(require_os_isolation=True),
        signing_key=b"s" * 32,
        isolation_backend=backend,
    )
    command = ValidationCommand("targeted_tests", ("python", "-c", "pass"), timeout_seconds=5)
    executor(command, tmp_path)

    argv = captured["argv"]
    assert "--user=65532:65532" in argv
    joined = "\n".join(str(item) for item in argv)
    assert "HOME=" not in joined
    assert "PYTHONPATH=" not in joined
    assert "--network=none" in argv
    assert "--read-only" in argv
    assert "--cap-drop=ALL" in argv


def test_git_repository_root_cannot_be_directly_mounted(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    backend = DockerIsolationBackend(
        DockerIsolationPolicy(image=PINNED_IMAGE),
        launcher=lambda *a, **k: subprocess.CompletedProcess([], 0, stdout="", stderr=""),
    )
    command = ValidationCommand("x", ("python", "-c", "pass"), timeout_seconds=5)
    with pytest.raises(ValueError, match="git repository roots"):
        backend.execute(command, tmp_path, {})
