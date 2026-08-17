"""Fail-closed evidence collection for already isolated sandbox validation.

This module owns orchestration and evidence normalization, not patch synthesis,
promotion, git operations, or production mutation. Command execution is injected
by the caller so policy can be tested hermetically and replaced by a hardened
sandbox backend in production.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

from .sandbox_patch import PatchProposal, PatchValidationEvidence


@dataclass(frozen=True)
class ValidationCommand:
    name: str
    argv: tuple[str, ...]
    timeout_seconds: int = 300
    required: bool = True

    def __post_init__(self) -> None:
        if not self.name or not self.argv:
            raise ValueError("validation command name and argv are required")
        if self.timeout_seconds < 1:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class CommandObservation:
    name: str
    returncode: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.returncode == 0 and not self.timed_out


@dataclass(frozen=True)
class SandboxEvidencePolicy:
    max_commands: int = 8
    max_timeout_seconds: int = 900
    require_targeted_tests: bool = True
    require_full_regression: bool = True

    def __post_init__(self) -> None:
        if self.max_commands < 1 or self.max_timeout_seconds < 1:
            raise ValueError("evidence policy limits must be positive")


@dataclass(frozen=True)
class SandboxEvidenceReport:
    proposal_id: str
    sandbox_root: str
    observations: tuple[CommandObservation, ...]
    evidence: PatchValidationEvidence


class SandboxEvidenceRunner:
    """Run a bounded validation plan via an injected isolated executor."""

    def __init__(self, policy: SandboxEvidencePolicy | None = None) -> None:
        self.policy = policy or SandboxEvidencePolicy()

    def run(
        self,
        *,
        proposal: PatchProposal,
        sandbox_root: str | Path,
        commands: Sequence[ValidationCommand],
        executor: Callable[[ValidationCommand, Path], CommandObservation],
        metrics: Mapping[str, int] | None = None,
        acceptance_contract_passed: bool = True,
    ) -> SandboxEvidenceReport:
        root = Path(sandbox_root).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")
        if not commands:
            raise ValueError("validation commands are required")
        if len(commands) > self.policy.max_commands:
            raise ValueError("validation plan exceeds max_commands")

        names = [command.name for command in commands]
        if len(names) != len(set(names)):
            raise ValueError("duplicate validation command name")
        if self.policy.require_targeted_tests and "targeted_tests" not in names:
            raise ValueError("targeted_tests command is required")
        if self.policy.require_full_regression and "full_regression" not in names:
            raise ValueError("full_regression command is required")

        observations: list[CommandObservation] = []
        for command in commands:
            if command.timeout_seconds > self.policy.max_timeout_seconds:
                raise ValueError(f"command timeout exceeds policy: {command.name}")
            try:
                observation = executor(command, root)
            except Exception as exc:
                observation = CommandObservation(
                    name=command.name,
                    returncode=1,
                    stderr=f"executor_error:{type(exc).__name__}",
                )
            if observation.name != command.name:
                raise ValueError("executor returned mismatched command observation")
            observations.append(observation)

        by_name = {item.name: item for item in observations}
        targeted_passed = by_name.get(
            "targeted_tests", CommandObservation("targeted_tests", 1)
        ).passed
        full_passed = by_name.get(
            "full_regression", CommandObservation("full_regression", 1)
        ).passed
        required_passed = all(
            by_name[command.name].passed for command in commands if command.required
        )
        values = dict(metrics or {})

        evidence = PatchValidationEvidence(
            targeted_tests_passed=targeted_passed and required_passed,
            full_regression_passed=full_passed and required_passed,
            acceptance_contract_passed=bool(acceptance_contract_passed) and required_passed,
            new_code_regressions=self._metric(values, "new_code_regressions"),
            safety_regressions=self._metric(values, "safety_regressions"),
            wrong_skill_selections=self._metric(values, "wrong_skill_selections"),
            hallucinated_entities=self._metric(values, "hallucinated_entities"),
            ungrounded_answers=self._metric(values, "ungrounded_answers"),
            provider_errors=self._metric(values, "provider_errors"),
            improved_cases=self._metric(values, "improved_cases"),
            regressed_cases=self._metric(values, "regressed_cases"),
            baseline_latency_ms=self._metric(values, "baseline_latency_ms"),
            candidate_latency_ms=self._metric(values, "candidate_latency_ms"),
            baseline_llm_calls=self._metric(values, "baseline_llm_calls"),
            candidate_llm_calls=self._metric(values, "candidate_llm_calls"),
        )
        return SandboxEvidenceReport(
            proposal_id=proposal.proposal_id,
            sandbox_root=str(root),
            observations=tuple(observations),
            evidence=evidence,
        )

    @staticmethod
    def _metric(values: Mapping[str, int], name: str) -> int:
        value = values.get(name, 0)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"invalid evidence metric: {name}")
        return value
