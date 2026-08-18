"""Reproducible orchestration for real SWTR/AS21 shadow experiments.

The runner freezes a bounded read-only SWTR corpus before any baseline/candidate
execution, binds agent identities and evaluation policy into an immutable
manifest, and delegates comparison to :mod:`swtr_real_evaluation`.

It deliberately has no AS21 mutation API and no production promotion/rollback
authority. A positive result can only be ``APPROVAL_REQUIRED``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Iterable, Optional

from po_agent.adapters.swtr_shadow import SWTRReadOnlyShadowSource, SWTRShadowBatch
from .swtr_real_evaluation import (
    RealShadowPolicy,
    RealShadowRunEvidence,
    SWTRRealShadowEvaluator,
    ShadowRunVerdict,
    SnapshotAgent,
)


class ExperimentStatus(str, Enum):
    """Terminal orchestration status for a frozen real-case experiment."""

    NO_ACTION = "no_action"
    REJECTED = "rejected"
    APPROVAL_REQUIRED = "approval_required"


@dataclass(frozen=True, slots=True)
class SWTRExperimentManifest:
    """Immutable identity of one frozen baseline-vs-candidate experiment."""

    experiment_id: str
    batch_sha256: str
    task_keys: tuple[str, ...]
    baseline_id: str
    candidate_id: str
    policy_sha256: str
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class SWTRExperimentResult:
    """Evidence package emitted by one reproducible real-case experiment."""

    manifest: SWTRExperimentManifest
    evidence: RealShadowRunEvidence
    status: ExperimentStatus
    report_sha256: str


class SWTRRealExperimentRunner:
    """Run baseline and candidate on exactly one frozen SWTR corpus.

    Capture happens exactly once per public run method. After capture, evaluation
    operates exclusively on the immutable :class:`SWTRShadowBatch`; the source
    is never consulted again during baseline/candidate execution.
    """

    def __init__(
        self,
        source: SWTRReadOnlyShadowSource,
        *,
        policy: RealShadowPolicy | None = None,
    ) -> None:
        self._source = source
        self._policy = policy or RealShadowPolicy()
        self._evaluator = SWTRRealShadowEvaluator(self._policy)

    @property
    def policy(self) -> RealShadowPolicy:
        return self._policy

    @staticmethod
    def _identity(value: str, field: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{field} must not be empty")
        return normalized

    @staticmethod
    def _policy_sha256(policy: RealShadowPolicy) -> str:
        canonical = json.dumps(
            asdict(policy),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return sha256(canonical.encode("utf-8")).hexdigest()

    @classmethod
    def _build_manifest(
        cls,
        batch: SWTRShadowBatch,
        *,
        experiment_id: str,
        baseline_id: str,
        candidate_id: str,
        policy: RealShadowPolicy,
    ) -> SWTRExperimentManifest:
        experiment_id = cls._identity(experiment_id, "experiment_id")
        baseline_id = cls._identity(baseline_id, "baseline_id")
        candidate_id = cls._identity(candidate_id, "candidate_id")
        if baseline_id == candidate_id:
            raise ValueError("baseline_id and candidate_id must differ")
        if not batch.cases:
            raise ValueError("frozen SWTR corpus must not be empty")

        task_keys = tuple(case.task_key for case in batch.cases)
        policy_sha256 = cls._policy_sha256(policy)
        material = {
            "experiment_id": experiment_id,
            "batch_sha256": batch.batch_sha256,
            "task_keys": task_keys,
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
            "policy_sha256": policy_sha256,
        }
        canonical = json.dumps(
            material,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        manifest_sha256 = sha256(canonical.encode("utf-8")).hexdigest()
        return SWTRExperimentManifest(
            experiment_id=experiment_id,
            batch_sha256=batch.batch_sha256,
            task_keys=task_keys,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            policy_sha256=policy_sha256,
            manifest_sha256=manifest_sha256,
        )

    @staticmethod
    def _status(verdict: ShadowRunVerdict) -> ExperimentStatus:
        if verdict is ShadowRunVerdict.APPROVAL_REQUIRED:
            return ExperimentStatus.APPROVAL_REQUIRED
        if verdict is ShadowRunVerdict.REJECTED:
            return ExperimentStatus.REJECTED
        return ExperimentStatus.NO_ACTION

    @staticmethod
    def _report_sha256(
        manifest: SWTRExperimentManifest,
        evidence: RealShadowRunEvidence,
        status: ExperimentStatus,
    ) -> str:
        material = {
            "manifest_sha256": manifest.manifest_sha256,
            "run_sha256": evidence.run_sha256,
            "status": status.value,
        }
        canonical = json.dumps(material, sort_keys=True, separators=(",", ":"))
        return sha256(canonical.encode("utf-8")).hexdigest()

    def run_frozen_batch(
        self,
        batch: SWTRShadowBatch,
        *,
        experiment_id: str,
        baseline_id: str,
        candidate_id: str,
        baseline_agent: SnapshotAgent,
        candidate_agent: SnapshotAgent,
    ) -> SWTRExperimentResult:
        """Evaluate an already-frozen corpus without any source access."""
        manifest = self._build_manifest(
            batch,
            experiment_id=experiment_id,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            policy=self._policy,
        )
        evidence = self._evaluator.evaluate(
            batch,
            baseline_id=manifest.baseline_id,
            candidate_id=manifest.candidate_id,
            baseline_agent=baseline_agent,
            candidate_agent=candidate_agent,
        )
        if evidence.batch_sha256 != manifest.batch_sha256:
            raise RuntimeError("evaluation batch identity does not match frozen manifest")
        status = self._status(evidence.verdict)
        return SWTRExperimentResult(
            manifest=manifest,
            evidence=evidence,
            status=status,
            report_sha256=self._report_sha256(manifest, evidence, status),
        )

    async def run_keys(
        self,
        task_keys: Iterable[str],
        *,
        experiment_id: str,
        baseline_id: str,
        candidate_id: str,
        baseline_agent: SnapshotAgent,
        candidate_agent: SnapshotAgent,
    ) -> SWTRExperimentResult:
        """Capture explicit real SWTR keys once, freeze them, then evaluate."""
        batch = await self._source.capture_keys(task_keys)
        return self.run_frozen_batch(
            batch,
            experiment_id=experiment_id,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            baseline_agent=baseline_agent,
            candidate_agent=candidate_agent,
        )

    async def run_query(
        self,
        query: str,
        *,
        experiment_id: str,
        baseline_id: str,
        candidate_id: str,
        baseline_agent: SnapshotAgent,
        candidate_agent: SnapshotAgent,
        limit: Optional[int] = None,
    ) -> SWTRExperimentResult:
        """Capture one bounded SWTR query result once, freeze it, then evaluate."""
        batch = await self._source.capture_query(query, limit=limit)
        return self.run_frozen_batch(
            batch,
            experiment_id=experiment_id,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            baseline_agent=baseline_agent,
            candidate_agent=candidate_agent,
        )
