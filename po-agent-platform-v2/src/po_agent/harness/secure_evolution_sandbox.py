"""Secure, disposable execution environment for controlled self-evolution.

This module closes the gap between a non-executable PatchProposal and trusted
candidate evidence.  It snapshots an attested repository baseline into a fresh
disposable workspace, applies the governed patch only there, executes the
validation plan through HARD_OS isolation, evaluates signed evidence, and then
destroys the workspace.

Authority boundaries are intentionally strict:
- the source repository is read-only from this module's perspective;
- PatchProposal remains non-executable and requires human approval;
- the disposable workspace never contains .git metadata;
- validation must use a HARD_OS executor unless explicitly relaxed for tests;
- successful evidence yields APPROVAL_REQUIRED, never automatic promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
import hashlib
import os
import shutil
import tempfile

from .hardened_sandbox_executor import TrustedSandboxEvidenceRunner
from .os_isolation import IsolationLevel
from .sandbox_evidence import SandboxEvidenceReport, ValidationCommand
from .sandbox_patch import (
    PatchEvaluationGate,
    PatchEvaluationReport,
    PatchProposal,
    SandboxApplyResult,
    SandboxPatchApplicator,
)


BaselineAttestor = Callable[[Path], str]


@dataclass(frozen=True)
class SecureEvolutionSandboxPolicy:
    """Bounds and trust requirements for one candidate experiment."""

    require_hard_os: bool = True
    require_baseline_attestation: bool = True
    max_snapshot_files: int = 30_000
    max_snapshot_bytes: int = 500_000_000
    excluded_dir_names: tuple[str, ...] = (
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
    )
    retain_failed_workspace: bool = False

    def __post_init__(self) -> None:
        if self.max_snapshot_files < 1 or self.max_snapshot_bytes < 1:
            raise ValueError("snapshot bounds must be positive")
        if ".git" not in self.excluded_dir_names:
            raise ValueError(".git must remain excluded from disposable workspaces")


@dataclass(frozen=True)
class SecureEvolutionSandboxResult:
    proposal_id: str
    baseline_sha: str
    baseline_tree_sha256: str
    candidate_tree_sha256: str
    apply_result: SandboxApplyResult
    evidence_report: SandboxEvidenceReport
    evaluation_report: PatchEvaluationReport
    sandbox_root: str
    sandbox_destroyed: bool


class SecureEvolutionSandbox:
    """Materialize, patch, validate and destroy one isolated candidate workspace."""

    def __init__(
        self,
        evidence_runner: TrustedSandboxEvidenceRunner,
        *,
        baseline_attestor: BaselineAttestor | None,
        policy: SecureEvolutionSandboxPolicy | None = None,
        applicator: SandboxPatchApplicator | None = None,
        workspace_parent: str | Path | None = None,
    ) -> None:
        self.evidence_runner = evidence_runner
        self.baseline_attestor = baseline_attestor
        self.policy = policy or SecureEvolutionSandboxPolicy()
        self.applicator = applicator or SandboxPatchApplicator()
        self.workspace_parent = Path(workspace_parent).resolve() if workspace_parent else None

        if self.policy.require_baseline_attestation and self.baseline_attestor is None:
            raise ValueError("baseline_attestor is required by sandbox policy")
        if (
            self.policy.require_hard_os
            and self.evidence_runner.executor.isolation_level is not IsolationLevel.HARD_OS
        ):
            raise ValueError("SecureEvolutionSandbox requires a HARD_OS evidence executor")

    def run(
        self,
        *,
        proposal: PatchProposal,
        source_root: str | Path,
        commands: Sequence[ValidationCommand],
    ) -> SecureEvolutionSandboxResult:
        source = self._validate_source_root(Path(source_root))
        self._verify_baseline(proposal, source)

        temp_root = Path(
            tempfile.mkdtemp(
                prefix="po-agent-evolution-",
                dir=str(self.workspace_parent) if self.workspace_parent else None,
            )
        ).resolve()
        workspace = temp_root / "workspace"
        evaluation: PatchEvaluationReport | None = None
        destroyed = False

        try:
            self._copy_snapshot(source, workspace)
            baseline_tree = self._tree_digest(workspace)
            apply_result = self.applicator.apply(proposal, workspace)
            candidate_tree = self._tree_digest(workspace)
            if baseline_tree == candidate_tree:
                raise ValueError("candidate patch did not change disposable workspace")

            evidence = self.evidence_runner.run(
                proposal=proposal,
                sandbox_root=workspace,
                commands=commands,
            )
            evaluation = PatchEvaluationGate.evaluate(proposal, evidence.evidence)

            keep = self.policy.retain_failed_workspace and evaluation.verdict.value in {
                "blocked",
                "rejected",
            }
            if not keep:
                shutil.rmtree(temp_root)
                destroyed = True

            return SecureEvolutionSandboxResult(
                proposal_id=proposal.proposal_id,
                baseline_sha=proposal.baseline_sha,
                baseline_tree_sha256=baseline_tree,
                candidate_tree_sha256=candidate_tree,
                apply_result=apply_result,
                evidence_report=evidence,
                evaluation_report=evaluation,
                sandbox_root=str(workspace),
                sandbox_destroyed=destroyed,
            )
        except Exception:
            if temp_root.exists() and not self.policy.retain_failed_workspace:
                shutil.rmtree(temp_root, ignore_errors=True)
            raise

    def _verify_baseline(self, proposal: PatchProposal, source: Path) -> None:
        if self.baseline_attestor is None:
            return
        actual = str(self.baseline_attestor(source)).strip()
        if not actual:
            raise ValueError("baseline attestor returned an empty identity")
        if actual != proposal.baseline_sha:
            raise ValueError(
                f"baseline identity mismatch: expected {proposal.baseline_sha}, got {actual}"
            )

    def _validate_source_root(self, raw: Path) -> Path:
        source = raw.resolve()
        if not source.exists() or not source.is_dir():
            raise ValueError("source_root must be an existing directory")
        if source == Path("/").resolve() or source == Path.home().resolve():
            raise ValueError("filesystem root and user home cannot be evolution source roots")
        if self.workspace_parent and self._is_within(source, self.workspace_parent):
            raise ValueError("source repository cannot live inside disposable workspace parent")
        return source

    def _copy_snapshot(self, source: Path, destination: Path) -> None:
        destination.mkdir(parents=True, exist_ok=False)
        excluded = set(self.policy.excluded_dir_names)
        file_count = 0
        total_bytes = 0

        for current, dirs, files in os.walk(source, topdown=True, followlinks=False):
            current_path = Path(current)
            rel_dir = current_path.relative_to(source)

            safe_dirs: list[str] = []
            for name in dirs:
                child = current_path / name
                if name in excluded:
                    continue
                if child.is_symlink():
                    raise ValueError(f"symlink directory rejected in source snapshot: {child}")
                safe_dirs.append(name)
            dirs[:] = safe_dirs

            target_dir = destination / rel_dir
            target_dir.mkdir(parents=True, exist_ok=True)

            for name in files:
                src = current_path / name
                if src.is_symlink():
                    raise ValueError(f"symlink file rejected in source snapshot: {src}")
                if not src.is_file():
                    continue
                size = src.stat().st_size
                file_count += 1
                total_bytes += size
                if file_count > self.policy.max_snapshot_files:
                    raise ValueError("repository snapshot exceeds max_snapshot_files")
                if total_bytes > self.policy.max_snapshot_bytes:
                    raise ValueError("repository snapshot exceeds max_snapshot_bytes")
                dst = target_dir / name
                shutil.copyfile(src, dst)

        if (destination / ".git").exists():
            raise ValueError("disposable workspace must not contain git metadata")

    def _tree_digest(self, root: Path) -> str:
        digest = hashlib.sha256()
        files = 0
        total_bytes = 0
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if path.is_symlink():
                raise ValueError("symlink appeared inside disposable workspace")
            if not path.is_file():
                continue
            files += 1
            size = path.stat().st_size
            total_bytes += size
            if files > self.policy.max_snapshot_files:
                raise ValueError("workspace exceeds max_snapshot_files")
            if total_bytes > self.policy.max_snapshot_bytes:
                raise ValueError("workspace exceeds max_snapshot_bytes")
            rel = path.relative_to(root).as_posix()
            digest.update(f"F:{rel}:{size}\n".encode("utf-8"))
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
