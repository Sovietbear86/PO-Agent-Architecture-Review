"""OS-level isolation backends for sandbox evidence execution.

Production execution is fail-closed: container images are content-addressed,
Docker CLI paths are explicit, sandbox host roots are policy-authorized, and
containers run without network/capabilities/privilege as a non-root user.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol
import re
import subprocess

from .sandbox_evidence import ValidationCommand


_SHA256_IMAGE_RE = re.compile(r"^.+@sha256:[0-9a-fA-F]{64}$")


class IsolationLevel(str, Enum):
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
    """Fail-closed policy for Docker-backed validation.

    ``allowed_sandbox_roots`` contains host directories under which writable
    sandbox workspaces may be mounted.  Empty means no host path is authorized.
    """

    image: str
    docker_executable: str = "/usr/bin/docker"
    allowed_sandbox_roots: tuple[str, ...] = ()
    workspace_mount: str = "/workspace"
    tmpfs_size: str = "64m"
    memory: str = "1g"
    cpus: str = "1.0"
    pids_limit: int = 256
    max_output_chars: int = 200_000
    container_user: str = "65532:65532"
    apparmor_profile: str | None = None
    env_allowlist: tuple[str, ...] = ("PATH", "LANG", "LC_ALL")

    def __post_init__(self) -> None:
        if not _SHA256_IMAGE_RE.fullmatch(self.image):
            raise ValueError("container image must end with @sha256:<64 hex chars>")
        docker_path = Path(self.docker_executable)
        if not docker_path.is_absolute():
            raise ValueError("docker_executable must be an absolute path")
        if not self.workspace_mount.startswith("/"):
            raise ValueError("workspace_mount must be absolute")
        if self.pids_limit < 1 or self.max_output_chars < 1:
            raise ValueError("container limits must be positive")
        if not self.container_user or self.container_user.startswith("0"):
            raise ValueError("container_user must be explicitly non-root")
        for root in self.allowed_sandbox_roots:
            if not Path(root).is_absolute():
                raise ValueError("allowed_sandbox_roots entries must be absolute")


class DockerIsolationBackend:
    """Execute one validation command in a locked-down Docker container."""

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
        root = self._authorized_root(sandbox_root)
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

    def _authorized_root(self, sandbox_root: Path) -> Path:
        root = sandbox_root.resolve(strict=True)
        if not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")
        allowed = [Path(item).resolve(strict=True) for item in self.policy.allowed_sandbox_roots]
        if not allowed:
            raise ValueError("no sandbox roots are authorized by policy")
        for base in allowed:
            if not base.is_dir():
                continue
            try:
                root.relative_to(base)
            except ValueError:
                continue
            if root == base:
                raise ValueError("sandbox root must be a child of an authorized root")
            return root
        raise ValueError("sandbox root is outside authorized host roots")

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
            "--security-opt=seccomp=builtin",
            "--user",
            self.policy.container_user,
            f"--pids-limit={self.policy.pids_limit}",
            f"--memory={self.policy.memory}",
            f"--cpus={self.policy.cpus}",
            f"--tmpfs=/tmp:rw,noexec,nosuid,nodev,size={self.policy.tmpfs_size}",
            "--workdir",
            mount,
            "--mount",
            f"type=bind,src={root},dst={mount},rw",
        ]
        if self.policy.apparmor_profile:
            argv.append(f"--security-opt=apparmor={self.policy.apparmor_profile}")
        for name in sorted(self.policy.env_allowlist):
            value = env.get(name)
            if value is not None:
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
