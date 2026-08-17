"""OS-level isolation backends for sandbox evidence execution.

This module is the execution trust boundary for self-evolution validation.
Production callers can require HARD_OS isolation.  The Docker backend is
fail-closed, content-addressed, non-root, networkless and mounts exactly one
validated disposable workspace writable.

No promotion logic lives here.  A successful process result is only evidence;
it never authorizes a production mutation by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol
import os
import re
import subprocess

from .sandbox_evidence import ValidationCommand


_SHA256_IMAGE_RE = re.compile(r"^[^\s@]+@sha256:[0-9a-fA-F]{64}$")
_DEFAULT_DOCKER_ROOTS = (
    "/usr/bin",
    "/usr/local/bin",
    "/opt/homebrew/bin",
    "/Applications/Docker.app/Contents/Resources/bin",
)


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

    ``image`` must use a real sha256 digest, not merely contain ``@sha256:``.
    ``docker_executable`` is an absolute, explicitly trusted host binary path.
    The container runs as an unprivileged uid/gid and receives a minimal env.
    """

    image: str
    docker_executable: str = "/usr/bin/docker"
    trusted_docker_roots: tuple[str, ...] = _DEFAULT_DOCKER_ROOTS
    workspace_mount: str = "/workspace"
    tmpfs_size: str = "64m"
    memory: str = "1g"
    cpus: str = "1.0"
    pids_limit: int = 256
    max_output_chars: int = 200_000
    container_user: str = "65532:65532"

    def __post_init__(self) -> None:
        if not _SHA256_IMAGE_RE.fullmatch(self.image):
            raise ValueError("container image must be pinned by a 64-hex sha256 digest")
        docker = Path(self.docker_executable)
        if not docker.is_absolute():
            raise ValueError("docker_executable must be an absolute trusted path")
        resolved = docker.resolve(strict=False)
        if not any(_is_within(resolved, Path(root).resolve(strict=False)) for root in self.trusted_docker_roots):
            raise ValueError("docker_executable is outside trusted docker roots")
        if not self.workspace_mount.startswith("/") or self.workspace_mount == "/":
            raise ValueError("workspace_mount must be an absolute non-root path")
        if self.pids_limit < 1 or self.max_output_chars < 1:
            raise ValueError("container limits must be positive")
        if not self.container_user or self.container_user in {"0", "0:0", "root"}:
            raise ValueError("container must run as a non-root user")


class DockerIsolationBackend:
    """Run one validation command in a locked-down Docker container.

    Generated invocation guarantees:
    - no network;
    - read-only container root filesystem;
    - all Linux capabilities dropped;
    - no-new-privileges;
    - non-root uid/gid;
    - bounded pids/memory/cpu/tmpfs;
    - exactly one validated writable host bind mount;
    - argv execution only (never a shell string).

    Docker's default seccomp profile remains enabled because this backend never
    passes ``seccomp=unconfined``.  ``launcher`` is injectable for hermetic
    verification; production should use the trusted Docker CLI.
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
        root = _validated_disposable_sandbox_root(sandbox_root)
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
            f"--user={self.policy.container_user}",
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
    """Explicit development backend; never a production security boundary."""

    @property
    def isolation_level(self) -> IsolationLevel:
        return IsolationLevel.WORKSPACE_ONLY

    def execute(
        self,
        command: ValidationCommand,
        sandbox_root: Path,
        env: Mapping[str, str],
    ) -> IsolatedProcessResult:
        root = Path(sandbox_root).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")
        try:
            completed = subprocess.run(
                list(command.argv),
                cwd=str(root),
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


def _validated_disposable_sandbox_root(raw_root: Path) -> Path:
    """Reject host-sensitive roots even if a caller tries to mount them directly."""

    root = Path(raw_root).resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("sandbox root must be an existing directory")

    forbidden = {Path("/").resolve(), Path.home().resolve()}
    if root in forbidden:
        raise ValueError("sensitive host directory cannot be used as sandbox root")
    if ".git" in root.parts or (root / ".git").exists():
        raise ValueError("git repository roots cannot be mounted as disposable sandboxes")

    # Refuse roots that resolve to a parent of HOME; this closes '/'-like broad mounts.
    home = Path.home().resolve()
    if _is_within(home, root):
        raise ValueError("sandbox root is too broad and contains the user home directory")

    return root


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False
