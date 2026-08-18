"""Human-reviewable reporting for the first bounded real SWTR pilot.

The pilot layer is deliberately read-only. It delegates capture/evaluation to
SWTRRealExperimentRunner and turns immutable evidence into a deterministic,
human-reviewable report. It has no AS21 mutation or promotion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable

from .swtr_real_evaluation import ShadowDecision, SnapshotAgent
from .swtr_real_experiment import ExperimentStatus, SWTRExperimentResult, SWTRRealExperimentRunner


@dataclass(frozen=True, slots=True)
class PilotCaseReport:
    task_key: str
    content_sha256: str
    decision: ShadowDecision
    baseline_score: float
    candidate_score: float
    score_delta: float
    baseline_grounded: bool
    candidate_grounded: bool
    candidate_hallucination: bool
    candidate_wrong_skill: bool
    candidate_provider_error: bool
    evidence_sha256: str


@dataclass(frozen=True, slots=True)
class SWTRPilotReport:
    experiment: SWTRExperimentResult
    cases: tuple[PilotCaseReport, ...]
    summary: str
    pilot_sha256: str


class SWTRFirstRealPilot:
    """Run an explicit small SWTR corpus and emit review-only evidence."""

    def __init__(self, runner: SWTRRealExperimentRunner, *, max_pilot_cases: int = 10) -> None:
        if max_pilot_cases <= 0 or max_pilot_cases > 10:
            raise ValueError("max_pilot_cases must be between 1 and 10")
        self._runner = runner
        self._max_pilot_cases = max_pilot_cases

    @property
    def max_pilot_cases(self) -> int:
        return self._max_pilot_cases

    @staticmethod
    def _normalize_keys(task_keys: Iterable[str], limit: int) -> tuple[str, ...]:
        keys = tuple(key.strip() for key in task_keys)
        if not keys:
            raise ValueError("pilot requires at least one explicit SWTR task key")
        if any(not key for key in keys):
            raise ValueError("pilot task keys must not be empty")
        if len(keys) != len(set(keys)):
            raise ValueError("pilot task keys must be unique")
        if len(keys) > limit:
            raise ValueError(f"pilot is limited to {limit} tasks")
        return keys

    @staticmethod
    def _report(result: SWTRExperimentResult) -> SWTRPilotReport:
        cases = tuple(
            PilotCaseReport(
                task_key=item.task_key,
                content_sha256=item.content_sha256,
                decision=item.decision,
                baseline_score=float(item.baseline.score),
                candidate_score=float(item.candidate.score),
                score_delta=float(item.score_delta),
                baseline_grounded=item.baseline.grounded,
                candidate_grounded=item.candidate.grounded,
                candidate_hallucination=item.candidate.hallucination,
                candidate_wrong_skill=item.candidate.wrong_skill,
                candidate_provider_error=item.candidate.provider_error,
                evidence_sha256=item.evidence_sha256,
            )
            for item in result.evidence.cases
        )
        summary = (
            f"status={result.status.value}; cases={len(cases)}; "
            f"improved={result.evidence.improved_cases}; "
            f"equivalent={result.evidence.equivalent_cases}; "
            f"regressed={result.evidence.regressed_cases}; "
            f"blocked={result.evidence.blocked_cases}"
        )
        material = {
            "manifest_sha256": result.manifest.manifest_sha256,
            "report_sha256": result.report_sha256,
            "status": result.status.value,
            "case_evidence": [case.evidence_sha256 for case in cases],
            "summary": summary,
        }
        canonical = json.dumps(material, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return SWTRPilotReport(
            experiment=result,
            cases=cases,
            summary=summary,
            pilot_sha256=sha256(canonical.encode("utf-8")).hexdigest(),
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
    ) -> SWTRPilotReport:
        """Capture one explicit bounded corpus, compare, and return evidence only."""
        keys = self._normalize_keys(task_keys, self._max_pilot_cases)
        result = await self._runner.run_keys(
            keys,
            experiment_id=experiment_id,
            baseline_id=baseline_id,
            candidate_id=candidate_id,
            baseline_agent=baseline_agent,
            candidate_agent=candidate_agent,
        )
        if tuple(result.manifest.task_keys) != tuple(sorted(keys)):
            # SWTRShadowBatch canonicalizes case order. Equality as sets is the
            # safety property; the exact canonical order belongs to the batch.
            if set(result.manifest.task_keys) != set(keys):
                raise RuntimeError("pilot manifest corpus differs from requested task keys")
        return self._report(result)

    @staticmethod
    def requires_human_review(report: SWTRPilotReport) -> bool:
        """True only for a positive result; this does not grant approval."""
        return report.experiment.status is ExperimentStatus.APPROVAL_REQUIRED
