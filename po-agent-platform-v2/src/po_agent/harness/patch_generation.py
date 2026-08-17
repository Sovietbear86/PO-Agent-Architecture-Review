"""Bounded generation of concrete sandbox patch changes.

The engine turns externally generated file drafts into governed ProposedFileChange
objects. It never writes files, executes code, applies patches, or promotes a
candidate. Repository reads are supplied by the caller so generation remains
hermetic and testable.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Mapping, Sequence
import hashlib

from .sandbox_patch import PatchOperation, ProposedFileChange


@dataclass(frozen=True)
class PatchGenerationPolicy:
    allowed_roots: tuple[str, ...] = (
        "po-agent-platform-v2/src/po_agent/harness",
        "po-agent-platform-v2/tests",
    )
    max_files: int = 4
    max_total_chars: int = 80_000
    max_file_chars: int = 40_000

    def __post_init__(self) -> None:
        if not self.allowed_roots:
            raise ValueError("allowed_roots must not be empty")
        if min(self.max_files, self.max_total_chars, self.max_file_chars) < 1:
            raise ValueError("generation limits must be positive")


@dataclass(frozen=True)
class FileDraft:
    path: str
    content: str
    operation: PatchOperation | None = None

    def __post_init__(self) -> None:
        if not self.path:
            raise ValueError("draft path is required")
        if not isinstance(self.content, str) or not self.content:
            raise ValueError("draft content is required")


@dataclass(frozen=True)
class PatchGenerationResult:
    changes: tuple[ProposedFileChange, ...]
    total_chars: int
    target_files: tuple[str, ...]


class BoundedPatchGenerator:
    """Validate concrete drafts and bind them to a repository baseline."""

    def __init__(self, policy: PatchGenerationPolicy | None = None) -> None:
        self.policy = policy or PatchGenerationPolicy()

    def generate(
        self,
        *,
        drafts: Sequence[FileDraft],
        authorized_target_files: Sequence[str],
        baseline_files: Mapping[str, str | None] | None = None,
        baseline_reader: Callable[[str], str | None] | None = None,
    ) -> PatchGenerationResult:
        if not drafts:
            raise ValueError("at least one draft is required")
        if len(drafts) > self.policy.max_files:
            raise ValueError("generated patch exceeds max_files")
        if baseline_files is not None and baseline_reader is not None:
            raise ValueError("provide baseline_files or baseline_reader, not both")

        authorized = {self._validate_path(path) for path in authorized_target_files}
        if not authorized:
            raise ValueError("authorized_target_files are required")

        seen: set[str] = set()
        changes: list[ProposedFileChange] = []
        total_chars = 0
        for draft in drafts:
            path = self._validate_path(draft.path)
            if path not in authorized:
                raise ValueError(f"target file is not authorized: {path}")
            if path in seen:
                raise ValueError(f"duplicate target file: {path}")
            seen.add(path)

            size = len(draft.content)
            if size > self.policy.max_file_chars:
                raise ValueError(f"generated file exceeds max_file_chars: {path}")
            total_chars += size
            if total_chars > self.policy.max_total_chars:
                raise ValueError("generated patch exceeds max_total_chars")

            before = self._baseline(path, baseline_files, baseline_reader)
            inferred = PatchOperation.REPLACE if before is not None else PatchOperation.CREATE
            operation = draft.operation or inferred
            if operation is not inferred:
                raise ValueError(f"operation does not match repository baseline: {path}")
            before_hash = (
                hashlib.sha256(before.encode("utf-8")).hexdigest()
                if before is not None
                else None
            )
            changes.append(
                ProposedFileChange(
                    path=path,
                    operation=operation,
                    content=draft.content,
                    expected_before_sha256=before_hash,
                )
            )

        return PatchGenerationResult(
            changes=tuple(changes),
            total_chars=total_chars,
            target_files=tuple(change.path for change in changes),
        )

    @staticmethod
    def _baseline(
        path: str,
        baseline_files: Mapping[str, str | None] | None,
        baseline_reader: Callable[[str], str | None] | None,
    ) -> str | None:
        if baseline_reader is not None:
            return baseline_reader(path)
        if baseline_files is not None:
            return baseline_files.get(path)
        raise ValueError("repository baseline source is required")

    def _validate_path(self, raw: str) -> str:
        path = PurePosixPath(raw)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError(f"unsafe repository path: {raw}")
        normalized = path.as_posix()
        if not any(
            normalized == root or normalized.startswith(root.rstrip("/") + "/")
            for root in self.policy.allowed_roots
        ):
            raise ValueError(f"path outside allowed roots: {raw}")
        return normalized
