"""Hardened execution boundary for sandbox validation.

The executor executes only structured argv commands, with a bounded environment,
timeout and cryptographically bound observations.  Execution itself is delegated
to an explicit isolation backend.  Production callers can require HARD_OS
isolation; workspace-only subprocess execution is then rejected fail-closed.

TrustedSandboxEvidenceRunner removes caller-supplied GREEN inputs: acceptance
and metrics are derived from signed command observations produced by this
executor. Human approval and promotion remain outside this module.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence
import hashlib
import hmac
import json
import os

from .os_isolation import (
    IsolationBackend,
    IsolationLevel,
    WorkspaceOnlyIsolationBackend,
)
from .sandbox_evidence import (
    CommandObservation,
    SandboxEvidenceReport,
    SandboxEvidenceRunner,
    SandboxEvidencePolicy,
    ValidationCommand,
)
from .sandbox_patch import PatchProposal


EVIDENCE_PREFIX = "HARNESS_EVIDENCE_JSON="


@dataclass(frozen=True)
class HardenedExecutorPolicy:
    allowed_executables: tuple[str, ...] = ("python", "python3", "pytest")
    max_output_chars: int = 200_000
    max_hashed_files: int = 20_000
    max_hashed_bytes: int = 200_000_000
    # Do not leak host HOME/PATH/PYTHONPATH into HARD_OS containers.  LANG/LC_ALL
    # are sufficient for deterministic text handling; the container supplies its
    # own executable PATH and Python environment.
    env_allowlist: tuple[str, ...] = ("LANG", "LC_ALL")
    require_os_isolation: bool = False

    def __post_init__(self) -> None:
        if not self.allowed_executables:
            raise ValueError("allowed_executables must not be empty")
        if self.max_output_chars < 1 or self.max_hashed_files < 1 or self.max_hashed_bytes < 1:
            raise ValueError("executor limits must be positive")


class HardenedSandboxExecutor:
    """Structured, bounded executor restricted to a declared isolation backend."""

    def __init__(
        self,
        policy: HardenedExecutorPolicy | None = None,
        *,
        signing_key: bytes | None = None,
        isolation_backend: IsolationBackend | None = None,
    ) -> None:
        self.policy = policy or HardenedExecutorPolicy()
        self._signing_key = signing_key or os.urandom(32)
        self.isolation_backend = isolation_backend or WorkspaceOnlyIsolationBackend()
        if (
            self.policy.require_os_isolation
            and self.isolation_backend.isolation_level is not IsolationLevel.HARD_OS
        ):
            raise ValueError("HARD_OS isolation backend is required by executor policy")

    @property
    def isolation_level(self) -> IsolationLevel:
        return self.isolation_backend.isolation_level

    def __call__(self, command: ValidationCommand, sandbox_root: Path) -> CommandObservation:
        root = sandbox_root.resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")
        self._validate_command(command)
        if (
            self.policy.require_os_isolation
            and self.isolation_backend.isolation_level is not IsolationLevel.HARD_OS
        ):
            raise ValueError("execution refused: HARD_OS isolation is unavailable")

        before = self._workspace_digest(root)
        started = datetime.now(timezone.utc).isoformat()
        result = self.isolation_backend.execute(command, root, self._sanitized_env())
        finished = datetime.now(timezone.utc).isoformat()
        after = self._workspace_digest(root)

        stdout = result.stdout[: self.policy.max_output_chars]
        stderr = result.stderr[: self.policy.max_output_chars]
        observation = CommandObservation(
            name=command.name,
            returncode=int(result.returncode),
            stdout=stdout,
            stderr=stderr,
            timed_out=bool(result.timed_out),
            command_sha256=self._command_digest(command),
            stdout_sha256=self._digest_text(stdout),
            stderr_sha256=self._digest_text(stderr),
            workspace_before_sha256=before,
            workspace_after_sha256=after,
            started_at=started,
            finished_at=finished,
            trusted=True,
        )
        return replace(observation, signature=self._sign(observation))

    def verify(self, command: ValidationCommand, observation: CommandObservation) -> bool:
        if not observation.trusted or not observation.signature:
            return False
        if observation.name != command.name:
            return False
        if observation.command_sha256 != self._command_digest(command):
            return False
        unsigned = replace(observation, signature="")
        expected = self._sign(unsigned)
        return hmac.compare_digest(expected, observation.signature)

    def _validate_command(self, command: ValidationCommand) -> None:
        executable = Path(command.argv[0]).name
        if executable not in self.policy.allowed_executables:
            raise ValueError(f"executable is not allowed: {executable}")
        for arg in command.argv:
            if "\x00" in arg:
                raise ValueError("NUL byte in argv")
        if executable in {"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"}:
            raise ValueError("shell execution is forbidden")

    def _sanitized_env(self) -> dict[str, str]:
        env: dict[str, str] = {}
        for name in self.policy.env_allowlist:
            value = os.environ.get(name)
            if value is not None:
                env[name] = value
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        return env

    def _workspace_digest(self, root: Path) -> str:
        digest = hashlib.sha256()
        files = 0
        total_bytes = 0
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_symlink():
                digest.update(f"L:{path.relative_to(root).as_posix()}->{os.readlink(path)}\n".encode())
                continue
            if not path.is_file():
                continue
            files += 1
            if files > self.policy.max_hashed_files:
                raise ValueError("sandbox exceeds max_hashed_files")
            size = path.stat().st_size
            total_bytes += size
            if total_bytes > self.policy.max_hashed_bytes:
                raise ValueError("sandbox exceeds max_hashed_bytes")
            digest.update(f"F:{path.relative_to(root).as_posix()}:{size}\n".encode())
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()

    def _command_digest(self, command: ValidationCommand) -> str:
        payload = json.dumps(
            {
                "name": command.name,
                "argv": list(command.argv),
                "timeout_seconds": command.timeout_seconds,
                "required": command.required,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return self._digest_text(payload)

    def _sign(self, observation: CommandObservation) -> str:
        payload = asdict(replace(observation, signature=""))
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hmac.new(self._signing_key, encoded, hashlib.sha256).hexdigest()

    @staticmethod
    def _digest_text(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TrustedEvidencePolicy:
    acceptance_command_name: str = "acceptance_contract"
    metrics_command_name: str = "evidence_metrics"
    require_workspace_unchanged_for_metrics: bool = True


class TrustedSandboxEvidenceRunner:
    """Derive all GREEN inputs from signed observations, never caller claims."""

    def __init__(
        self,
        executor: HardenedSandboxExecutor,
        *,
        evidence_policy: SandboxEvidencePolicy | None = None,
        trusted_policy: TrustedEvidencePolicy | None = None,
    ) -> None:
        self.executor = executor
        self.base_runner = SandboxEvidenceRunner(evidence_policy)
        self.policy = trusted_policy or TrustedEvidencePolicy()

    def run(
        self,
        *,
        proposal: PatchProposal,
        sandbox_root: str | Path,
        commands: Sequence[ValidationCommand],
    ) -> SandboxEvidenceReport:
        names = {command.name for command in commands}
        required = {
            "targeted_tests",
            "full_regression",
            self.policy.acceptance_command_name,
            self.policy.metrics_command_name,
        }
        missing = required - names
        if missing:
            raise ValueError(f"trusted evidence plan missing commands: {sorted(missing)}")

        observations: dict[str, CommandObservation] = {}

        def verified_executor(command: ValidationCommand, root: Path) -> CommandObservation:
            observation = self.executor(command, root)
            if not self.executor.verify(command, observation):
                raise ValueError("untrusted command observation")
            observations[command.name] = observation
            return observation

        preliminary = self.base_runner.run(
            proposal=proposal,
            sandbox_root=sandbox_root,
            commands=commands,
            executor=verified_executor,
            metrics={},
            acceptance_contract_passed=False,
        )

        acceptance = observations[self.policy.acceptance_command_name].passed
        metric_observation = observations[self.policy.metrics_command_name]
        if not metric_observation.passed:
            metrics: Mapping[str, int] = {"provider_errors": 1}
        else:
            if (
                self.policy.require_workspace_unchanged_for_metrics
                and metric_observation.workspace_before_sha256
                != metric_observation.workspace_after_sha256
            ):
                raise ValueError("metrics command mutated sandbox workspace")
            metrics = self._parse_metrics(metric_observation.stdout)

        evidence = preliminary.evidence
        values = dict(metrics)
        required_passed = all(
            observations[command.name].passed for command in commands if command.required
        )
        evidence = replace(
            evidence,
            targeted_tests_passed=observations["targeted_tests"].passed and required_passed,
            full_regression_passed=observations["full_regression"].passed and required_passed,
            acceptance_contract_passed=acceptance and required_passed,
            new_code_regressions=self.base_runner._metric(values, "new_code_regressions"),
            safety_regressions=self.base_runner._metric(values, "safety_regressions"),
            wrong_skill_selections=self.base_runner._metric(values, "wrong_skill_selections"),
            hallucinated_entities=self.base_runner._metric(values, "hallucinated_entities"),
            ungrounded_answers=self.base_runner._metric(values, "ungrounded_answers"),
            provider_errors=self.base_runner._metric(values, "provider_errors"),
            improved_cases=self.base_runner._metric(values, "improved_cases"),
            regressed_cases=self.base_runner._metric(values, "regressed_cases"),
            baseline_latency_ms=self.base_runner._metric(values, "baseline_latency_ms"),
            candidate_latency_ms=self.base_runner._metric(values, "candidate_latency_ms"),
            baseline_llm_calls=self.base_runner._metric(values, "baseline_llm_calls"),
            candidate_llm_calls=self.base_runner._metric(values, "candidate_llm_calls"),
        )
        return replace(preliminary, evidence=evidence)

    @staticmethod
    def _parse_metrics(stdout: str) -> Mapping[str, int]:
        lines = [line for line in stdout.splitlines() if line.startswith(EVIDENCE_PREFIX)]
        if len(lines) != 1:
            raise ValueError("metrics command must emit exactly one evidence payload")
        payload = json.loads(lines[0][len(EVIDENCE_PREFIX) :])
        if not isinstance(payload, dict):
            raise ValueError("evidence payload must be an object")
        return payload
