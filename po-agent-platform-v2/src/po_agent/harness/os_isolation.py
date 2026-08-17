"""OS-level isolation backends for sandbox evidence execution.

The previous hardened executor constrained cwd, argv, environment and evidence
signing, but an allowlisted interpreter could still access host paths.  This
module introduces an explicit execution trust boundary.  Production callers can
require HARD_OS isolation and use a container backend whose root filesystem is
read-only, network is disabled and only the sandbox workspace is writable.

No promotion logic lives here.  This module only executes one already-authorized
validation command and returns its raw process result.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence
import subprocess

from .sandbox_evidence import ValidationCommand


class IsolationLevel(str, Enum):
    """Strength of the execution boundary provided by a backend."""

    WORKSPACE_ONLY = "workspace_only"
    HARD_OS = "hard_os"


@dataclass(frozen=True)
class IsolatedProcessResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class IsolationBackend(Protocol):
    @property
    def isolation_level(self) -> IsolationLevel: ...

    def execute(
        self,
        command: ValidationCommand,
        sandbox_root: Path,
        env: Mapping[str, str],
    ) -> IsolatedProcessResult: ...


@dataclass(frozen=True)
class DockerIsolationPolicy:
    """Bounded container policy for validation commands.

    The image must be content-addressed.  This avoids silently changing the
    execution environment between baseline and candidate evaluation.
    """

    image: str
    docker_executable: str = "docker"
    workspace_mount: str = "/workspace"
    tmpfs_size: str = "64m"
    memory: str = "1g"
    cpus: str = "1.0"
    pids_limit: int = 256
    max_output_chars: int = 200_000

    def __post_init__(self) -> None:
        if "@sha256:" not in self.image:
            raise ValueError("container image must be pinned by sha256 digest")
        if not self.workspace_mount.startswith("/"):
            raise ValueError("workspace_mount must be absolute")
        if self.pids_limit < 1 or self.max_output_chars < 1:
            raise ValueError("container limits must be positive")


class DockerIsolationBackend:
    """Run a validation command in a locked-down Docker container.

    Security properties supplied by the generated invocation:
    - no network;
    - read-only container root filesystem;
    - all Linux capabilities dropped;
    - no-new-privileges;
    - bounded pids/memory/cpu;
    - only the supplied sandbox directory is mounted writable;
    - command is passed as argv, never through a shell.

    ``launcher`` is injectable so hermetic tests can verify the exact trust
    boundary without requiring Docker to be installed.
    """

    def __init__(
        self,
        policy: DockerIsolationPolicy,
        *,
        launcher: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.policy = policy
        self._launcher = launcher or subprocess.run

    @property
    def isolation_level(self) -> IsolationLevel:
        return IsolationLevel.HARD_OS

    def execute(
        self,
        command: ValidationCommand,
        sandbox_root: Path,
        env: Mapping[str, str],
    ) -> IsolatedProcessResult:
        root = sandbox_root.resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")

        argv = self._docker_argv(command, root, env)
        try:
            completed = self._launcher(
                argv,
                shell=False,
                capture_output=True,
                text=True,
                timeout=command.timeout_seconds,
                check=False,
            )
            return IsolatedProcessResult(
                returncode=int(completed.returncode),
                stdout=(completed.stdout or "")[: self.policy.max_output_chars],
                stderr=(completed.stderr or "")[: self.policy.max_output_chars],
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            return IsolatedProcessResult(
                returncode=124,
                stdout=self._text(exc.stdout)[: self.policy.max_output_chars],
                stderr=self._text(exc.stderr)[: self.policy.max_output_chars],
                timed_out=True,
            )

    def _docker_argv(
        self,
        command: ValidationCommand,
        root: Path,
        env: Mapping[str, str],
    ) -> list[str]:
        mount = self.policy.workspace_mount
        argv: list[str] = [
            self.policy.docker_executable,
            "run",
            "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges:true",
            f"--pids-limit={self.policy.pids_limit}",
            f"--memory={self.policy.memory}",
            f"--cpus={self.policy.cpus}",
            f"--tmpfs=/tmp:rw,noexec,nosuid,nodev,size={self.policy.tmpfs_size}",
            "--workdir",
            mount,
            "--mount",
            f"type=bind,src={root},dst={mount},rw",
        ]
        for name, value in sorted(env.items()):
            # Environment is already allowlisted by HardenedSandboxExecutor.
            argv.extend(["--env", f"{name}={value}"])
        argv.append(self.policy.image)
        argv.extend(command.argv)
        return argv

    @staticmethod
    def _text(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return str(value)


class WorkspaceOnlyIsolationBackend:
    """Explicit development backend; not a production security boundary."""

    @property
    def isolation_level(self) -> IsolationLevel:
        return IsolationLevel.WORKSPACE_ONLY

    def execute(
        self,
        command: ValidationCommand,
        sandbox_root: Path,
        env: Mapping[str, str],
    ) -> IsolatedProcessResult:
        try:
            completed = subprocess.run(
                list(command.argv),
                cwd=str(sandbox_root.resolve()),
                env=dict(env),
                shell=False,
                capture_output=True,
                text=True,
                timeout=command.timeout_seconds,
                check=False,
            )
            return IsolatedProcessResult(
                returncode=int(completed.returncode),
                stdout=completed.stdout or "",
                stderr=completed.stderr or "",
                timed_out=False,
            )
        except subprocess.TimeoutExpired as exc:
            return IsolatedProcessResult(
                returncode=124,
                stdout=DockerIsolationBackend._text(exc.stdout),
                stderr=DockerIsolationBackend._text(exc.stderr),
                timed_out=True,
            )
