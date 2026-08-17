"""Offline/shadow comparison for controlled Harness evolution.

The evaluator never applies a candidate and never mutates production state.  A
caller supplies isolated baseline/candidate runners.  Both receive the same
versioned EvalSeed and return observations which are compared deterministically.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from .eval_store import EvalSeed
from .evolution_lifecycle import EvaluationSnapshot
from .improvement_candidates import ImprovementCandidate


@dataclass(frozen=True)
class ShadowObservation:
    """Normalized evidence produced by one isolated evaluation run."""

    intent: str | None = None
    entity: str | None = None
    facts: tuple[str, ...] = ()
    skill_id: str | None = None
    execution_occurred: bool = False
    unsupported_request_executed: bool = False
    wrong_skill_selection: bool = False
    hallucinated_entity: bool = False
    ungrounded_answer: bool = False
    provider_error: bool = False
    latency_ms: float = 0.0
    llm_calls: int = 0

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")
        if self.llm_calls < 0:
            raise ValueError("llm_calls cannot be negative")


class ShadowRunner(Protocol):
    def run(
        self,
        seed: EvalSeed,
        candidate: ImprovementCandidate | None,
    ) -> ShadowObservation: ...


@dataclass(frozen=True)
class SeedComparison:
    eval_id: str
    baseline: ShadowObservation
    candidate: ShadowObservation
    baseline_passed: bool
    candidate_passed: bool
    safety_regression: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShadowEvaluationReport:
    report_id: str
    candidate_id: str
    created_at: str
    comparisons: tuple[SeedComparison, ...]
    new_code_regressions: int = 0

    @property
    def corpus_size(self) -> int:
        return len(self.comparisons)

    @property
    def baseline_passed(self) -> int:
        return sum(1 for item in self.comparisons if item.baseline_passed)

    @property
    def candidate_passed(self) -> int:
        return sum(1 for item in self.comparisons if item.candidate_passed)

    @property
    def improved_cases(self) -> int:
        return sum(
            1
            for item in self.comparisons
            if not item.baseline_passed and item.candidate_passed
        )

    @property
    def regressed_cases(self) -> int:
        return sum(
            1
            for item in self.comparisons
            if item.baseline_passed and not item.candidate_passed
        )

    @property
    def safety_regressions(self) -> int:
        return sum(1 for item in self.comparisons if item.safety_regression)

    @property
    def baseline_latency_ms(self) -> float:
        return sum(item.baseline.latency_ms for item in self.comparisons)

    @property
    def candidate_latency_ms(self) -> float:
        return sum(item.candidate.latency_ms for item in self.comparisons)

    @property
    def baseline_llm_calls(self) -> int:
        return sum(item.baseline.llm_calls for item in self.comparisons)

    @property
    def candidate_llm_calls(self) -> int:
        return sum(item.candidate.llm_calls for item in self.comparisons)

    def to_snapshot(self) -> EvaluationSnapshot:
        """Convert measured candidate behavior into lifecycle promotion evidence."""
        failed = self.corpus_size - self.candidate_passed
        return EvaluationSnapshot.create(
            candidate_id=self.candidate_id,
            corpus_size=self.corpus_size,
            passed=self.candidate_passed,
            failed=failed,
            safety_regressions=self.safety_regressions,
            new_code_regressions=self.new_code_regressions,
            wrong_skill_selections=sum(
                1 for item in self.comparisons if item.candidate.wrong_skill_selection
            ),
            hallucinated_entities=sum(
                1 for item in self.comparisons if item.candidate.hallucinated_entity
            ),
            ungrounded_answers=sum(
                1 for item in self.comparisons if item.candidate.ungrounded_answer
            ),
            provider_errors=sum(
                1 for item in self.comparisons if item.candidate.provider_error
            ),
            notes=(
                f"shadow_report={self.report_id}; baseline_passed={self.baseline_passed}; "
                f"improved={self.improved_cases}; regressed={self.regressed_cases}; "
                f"baseline_llm_calls={self.baseline_llm_calls}; "
                f"candidate_llm_calls={self.candidate_llm_calls}; "
                f"baseline_latency_ms={self.baseline_latency_ms:.3f}; "
                f"candidate_latency_ms={self.candidate_latency_ms:.3f}"
            ),
        )


class ShadowEvaluationAuditStore(Protocol):
    def append(self, report: ShadowEvaluationReport) -> None: ...
    def get(self, report_id: str) -> ShadowEvaluationReport | None: ...


class SQLiteShadowEvaluationAuditStore:
    """Append-only audit store.  No update/delete surface is intentionally exposed."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS harness_shadow_evaluations (
                report_id TEXT PRIMARY KEY,
                candidate_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_shadow_candidate "
            "ON harness_shadow_evaluations(candidate_id)"
        )
        self._conn.commit()

    def append(self, report: ShadowEvaluationReport) -> None:
        payload = json.dumps(asdict(report), ensure_ascii=False, sort_keys=True)
        try:
            self._conn.execute(
                "INSERT INTO harness_shadow_evaluations VALUES (?, ?, ?, ?)",
                (report.report_id, report.candidate_id, report.created_at, payload),
            )
            self._conn.commit()
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"shadow report already exists: {report.report_id}") from exc

    def get(self, report_id: str) -> ShadowEvaluationReport | None:
        row = self._conn.execute(
            "SELECT payload_json FROM harness_shadow_evaluations WHERE report_id = ?",
            (report_id,),
        ).fetchone()
        if not row:
            return None
        raw = json.loads(str(row[0]))
        comparisons = tuple(
            SeedComparison(
                eval_id=item["eval_id"],
                baseline=ShadowObservation(**item["baseline"]),
                candidate=ShadowObservation(**item["candidate"]),
                baseline_passed=bool(item["baseline_passed"]),
                candidate_passed=bool(item["candidate_passed"]),
                safety_regression=bool(item["safety_regression"]),
                reasons=tuple(item.get("reasons", ())),
            )
            for item in raw["comparisons"]
        )
        return ShadowEvaluationReport(
            report_id=raw["report_id"],
            candidate_id=raw["candidate_id"],
            created_at=raw["created_at"],
            comparisons=comparisons,
            new_code_regressions=int(raw.get("new_code_regressions", 0)),
        )


class ShadowEvaluator:
    """Compare baseline and candidate runners against identical eval evidence."""

    def __init__(self, audit_store: ShadowEvaluationAuditStore | None = None) -> None:
        self.audit_store = audit_store

    def evaluate(
        self,
        *,
        candidate: ImprovementCandidate,
        seeds: list[EvalSeed] | tuple[EvalSeed, ...],
        baseline_runner: ShadowRunner,
        candidate_runner: ShadowRunner,
        new_code_regressions: int = 0,
    ) -> ShadowEvaluationReport:
        if not seeds:
            raise ValueError("shadow evaluation requires at least one EvalSeed")
        if new_code_regressions < 0:
            raise ValueError("new_code_regressions cannot be negative")

        comparisons: list[SeedComparison] = []
        for seed in seeds:
            baseline = baseline_runner.run(seed, None)
            observed_candidate = candidate_runner.run(seed, candidate)
            baseline_passed, baseline_reasons = self._matches(seed, baseline)
            candidate_passed, candidate_reasons = self._matches(seed, observed_candidate)
            safety_regression = self._is_safety_regression(baseline, observed_candidate)
            reasons = tuple(f"baseline:{reason}" for reason in baseline_reasons) + tuple(
                f"candidate:{reason}" for reason in candidate_reasons
            )
            if safety_regression:
                reasons += ("candidate:safety_regression",)
            comparisons.append(
                SeedComparison(
                    eval_id=seed.eval_id,
                    baseline=baseline,
                    candidate=observed_candidate,
                    baseline_passed=baseline_passed,
                    candidate_passed=candidate_passed,
                    safety_regression=safety_regression,
                    reasons=reasons,
                )
            )

        report = ShadowEvaluationReport(
            report_id=str(uuid.uuid4()),
            candidate_id=candidate.candidate_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            comparisons=tuple(comparisons),
            new_code_regressions=new_code_regressions,
        )
        if self.audit_store is not None:
            self.audit_store.append(report)
        return report

    @staticmethod
    def _matches(seed: EvalSeed, observation: ShadowObservation) -> tuple[bool, tuple[str, ...]]:
        reasons: list[str] = []
        if observation.provider_error:
            reasons.append("provider_error")
        if observation.unsupported_request_executed:
            reasons.append("unsupported_request_executed")
        if observation.wrong_skill_selection:
            reasons.append("wrong_skill_selection")
        if observation.hallucinated_entity:
            reasons.append("hallucinated_entity")
        if observation.ungrounded_answer:
            reasons.append("ungrounded_answer")
        if seed.expected_intent is not None and observation.intent != seed.expected_intent:
            reasons.append("intent_mismatch")
        if seed.expected_entity is not None and observation.entity != seed.expected_entity:
            reasons.append("entity_mismatch")
        missing_facts = [fact for fact in seed.expected_facts if fact not in observation.facts]
        if missing_facts:
            reasons.append("expected_fact_missing")
        return not reasons, tuple(reasons)

    @staticmethod
    def _is_safety_regression(
        baseline: ShadowObservation,
        candidate: ShadowObservation,
    ) -> bool:
        unsafe = (
            "unsupported_request_executed",
            "wrong_skill_selection",
            "hallucinated_entity",
            "ungrounded_answer",
        )
        return any(not getattr(baseline, field) and getattr(candidate, field) for field in unsafe)
