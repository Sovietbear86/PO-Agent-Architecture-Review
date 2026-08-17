"""Governed patch proposals and sandbox-only application for Harness evolution.

This module deliberately separates three authorities:
1. synthesis: validate a concrete proposed change and package evidence;
2. application: materialize it only below an explicit sandbox root;
3. evaluation: classify externally supplied validation evidence.

Nothing here can commit, merge, push, mutate Skill Catalog, or promote a
candidate.  Production application remains outside this module and requires the
existing controlled lifecycle plus human approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence
import hashlib
import uuid

from .improvement_candidates import ImprovementCandidate


class PatchOperation(str, Enum):
    CREATE = "create"
    REPLACE = "replace"


class PatchVerdict(str, Enum):
    BLOCKED = "blocked"
    REJECTED = "rejected"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True)
class PatchSynthesisPolicy:
    """Hard bounds for proposed source changes."""

    allowed_roots: tuple[str, ...] = (
        "po-agent-platform-v2/src/po_agent/harness",
        "po-agent-platform-v2/tests",
    )
    max_files: int = 4
    max_total_chars: int = 80_000
    require_human_approval: bool = True

    def __post_init__(self) -> None:
        if self.max_files < 1:
            raise ValueError("max_files must be positive")
        if self.max_total_chars < 1:
            raise ValueError("max_total_chars must be positive")
        if not self.allowed_roots:
            raise ValueError("allowed_roots must not be empty")


@dataclass(frozen=True)
class ProposedFileChange:
    path: str
    operation: PatchOperation
    content: str
    expected_before_sha256: str | None = None

    def __post_init__(self) -> None:
        if not self.path or not self.content:
            raise ValueError("path and content are required")


@dataclass(frozen=True)
class PatchProposal:
    proposal_id: str
    created_at: str
    source_candidate_id: str
    source_skill_artifact_id: str
    rationale: str
    baseline_sha: str
    changes: tuple[ProposedFileChange, ...]
    acceptance_contract: dict[str, object]
    shadow_eval_plan: dict[str, object]
    risk_classification: str
    executable: bool = False
    apply: bool = False
    requires_human_approval: bool = True

    def __post_init__(self) -> None:
        if not self.proposal_id or not self.source_candidate_id:
            raise ValueError("proposal and candidate ids are required")
        if not self.baseline_sha:
            raise ValueError("baseline_sha is required")
        if not self.changes:
            raise ValueError("at least one file change is required")
        if self.executable or self.apply:
            raise ValueError("PatchProposal must remain non-executable/non-applying")
        if not self.requires_human_approval:
            raise ValueError("human approval is mandatory")

    @property
    def target_files(self) -> tuple[str, ...]:
        return tuple(change.path for change in self.changes)


class SandboxPatchSynthesizer:
    """Create bounded PatchProposal objects; never touches the filesystem."""

    def __init__(self, policy: PatchSynthesisPolicy | None = None) -> None:
        self.policy = policy or PatchSynthesisPolicy()

    def synthesize(
        self,
        *,
        candidate: ImprovementCandidate,
        baseline_sha: str,
        changes: Sequence[ProposedFileChange],
        authorized_target_files: Sequence[str],
        risk_classification: str = "medium",
    ) -> PatchProposal:
        proposal = candidate.proposed_change
        if bool(proposal.get("apply")) or bool(proposal.get("executable")):
            raise ValueError("candidate must be non-applying and non-executable")
        artifact_id = str(proposal.get("forge_artifact_id") or "")
        if not artifact_id:
            raise ValueError("candidate must originate from Skill Forge")
        acceptance = proposal.get("acceptance_contract")
        shadow_plan = proposal.get("shadow_eval_plan")
        if not isinstance(acceptance, dict) or not isinstance(shadow_plan, dict):
            raise ValueError("candidate lacks governed evaluation contracts")
        if not changes:
            raise ValueError("no concrete changes supplied")
        if len(changes) > self.policy.max_files:
            raise ValueError("patch exceeds max_files")

        allowed = set(authorized_target_files)
        if not allowed:
            raise ValueError("authorized_target_files are required")
        total_chars = 0
        seen: set[str] = set()
        normalized: list[ProposedFileChange] = []
        for change in changes:
            path = self._validate_path(change.path)
            if path not in allowed:
                raise ValueError(f"target file is not authorized: {path}")
            if path in seen:
                raise ValueError(f"duplicate target file: {path}")
            seen.add(path)
            total_chars += len(change.content)
            normalized.append(
                ProposedFileChange(
                    path=path,
                    operation=change.operation,
                    content=change.content,
                    expected_before_sha256=change.expected_before_sha256,
                )
            )
        if total_chars > self.policy.max_total_chars:
            raise ValueError("patch exceeds max_total_chars")

        return PatchProposal(
            proposal_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc).isoformat(),
            source_candidate_id=candidate.candidate_id,
            source_skill_artifact_id=artifact_id,
            rationale=candidate.rationale,
            baseline_sha=baseline_sha,
            changes=tuple(normalized),
            acceptance_contract=dict(acceptance),
            shadow_eval_plan=dict(shadow_plan),
            risk_classification=risk_classification,
            requires_human_approval=self.policy.require_human_approval,
        )

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


@dataclass(frozen=True)
class SandboxApplyResult:
    proposal_id: str
    sandbox_root: str
    changed_files: tuple[str, ...]
    after_sha256: Mapping[str, str]


class SandboxPatchApplicator:
    """Apply an already-governed proposal strictly below a sandbox root."""

    def apply(self, proposal: PatchProposal, sandbox_root: str | Path) -> SandboxApplyResult:
        root = Path(sandbox_root).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("sandbox root must be an existing directory")

        hashes: dict[str, str] = {}
        changed: list[str] = []
        for change in proposal.changes:
            target = (root / change.path).resolve()
            try:
                target.relative_to(root)
            except ValueError as exc:
                raise ValueError("sandbox path escape rejected") from exc

            exists = target.exists()
            if change.operation is PatchOperation.CREATE and exists:
                raise ValueError(f"create target already exists: {change.path}")
            if change.operation is PatchOperation.REPLACE and not exists:
                raise ValueError(f"replace target does not exist: {change.path}")
            if change.expected_before_sha256 is not None:
                before = hashlib.sha256(target.read_bytes()).hexdigest() if exists else None
                if before != change.expected_before_sha256:
                    raise ValueError(f"baseline content mismatch: {change.path}")

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change.content, encoding="utf-8")
            hashes[change.path] = hashlib.sha256(change.content.encode("utf-8")).hexdigest()
            changed.append(change.path)

        return SandboxApplyResult(
            proposal_id=proposal.proposal_id,
            sandbox_root=str(root),
            changed_files=tuple(changed),
            after_sha256=hashes,
        )


@dataclass(frozen=True)
class PatchValidationEvidence:
    targeted_tests_passed: bool
    full_regression_passed: bool
    acceptance_contract_passed: bool
    new_code_regressions: int = 0
    safety_regressions: int = 0
    wrong_skill_selections: int = 0
    hallucinated_entities: int = 0
    ungrounded_answers: int = 0
    provider_errors: int = 0
    improved_cases: int = 0
    regressed_cases: int = 0
    baseline_latency_ms: int = 0
    candidate_latency_ms: int = 0
    baseline_llm_calls: int = 0
    candidate_llm_calls: int = 0


@dataclass(frozen=True)
class PatchEvaluationReport:
    report_id: str
    proposal_id: str
    baseline_sha: str
    changed_files: tuple[str, ...]
    verdict: PatchVerdict
    reasons: tuple[str, ...]
    evidence: PatchValidationEvidence
    requires_human_approval: bool = True


class PatchEvaluationGate:
    """Deterministic gate over validation evidence supplied by external runners."""

    @staticmethod
    def evaluate(proposal: PatchProposal, evidence: PatchValidationEvidence) -> PatchEvaluationReport:
        blockers: list[str] = []
        if evidence.provider_errors:
            blockers.append("provider_errors")
        if evidence.safety_regressions:
            blockers.append("safety_regressions")
        if evidence.hallucinated_entities:
            blockers.append("hallucinated_entities")
        if evidence.ungrounded_answers:
            blockers.append("ungrounded_answers")
        if evidence.wrong_skill_selections:
            blockers.append("wrong_skill_selections")
        if blockers:
            verdict = PatchVerdict.BLOCKED
            reasons = tuple(blockers)
        else:
            regressions = (
                evidence.new_code_regressions
                or evidence.regressed_cases
                or not evidence.targeted_tests_passed
                or not evidence.full_regression_passed
                or not evidence.acceptance_contract_passed
            )
            if regressions:
                verdict = PatchVerdict.REJECTED
                reasons = ("correctness_or_regression_gate_failed",)
            else:
                verdict = PatchVerdict.APPROVAL_REQUIRED
                reasons = ("all_automated_gates_passed_human_approval_required",)

        return PatchEvaluationReport(
            report_id=str(uuid.uuid4()),
            proposal_id=proposal.proposal_id,
            baseline_sha=proposal.baseline_sha,
            changed_files=proposal.target_files,
            verdict=verdict,
            reasons=reasons,
            evidence=evidence,
        )
