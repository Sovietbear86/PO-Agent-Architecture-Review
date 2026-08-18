"""Production-safe baseline vs candidate evaluation on one frozen AS21/SWTR corpus.

The module compares two *real* PO Agent runtime variants against exactly the same
immutable :class:`SWTRShadowBatch`.  It never reads SWTR itself, never mutates AS21,
and never promotes a candidate automatically.  A positive result ends at
``APPROVAL_REQUIRED`` so a human remains the production authority.

The built-in judge is intentionally conservative and deterministic.  It scores only
properties that can be derived from the frozen task snapshot and runtime response.
Teams may inject a stronger judge later, but the experiment runner still enforces
corpus/query/budget identity and fail-closed behavior.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from hashlib import sha256
import json
import math
from typing import Awaitable, Callable, Mapping, Protocol, Sequence

from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot

from .contracts import HarnessRequest, HarnessResponse, ResponseStatus


DEFAULT_QUERY_TEMPLATES: tuple[str, ...] = (
    "Суммаризируй задачу {task_key}",
    "Оцени качество постановки задачи {task_key}",
    "Чего не хватает в задаче {task_key}?",
    "Какие риски ты видишь в задаче {task_key}?",
    "Какие вопросы PO должен задать перед передачей задачи {task_key} в разработку?",
)


class ExperimentVerdict(str, Enum):
    REJECTED = "REJECTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CaseVerdict(str, Enum):
    IMPROVED = "IMPROVED"
    EQUIVALENT = "EQUIVALENT"
    REGRESSED = "REGRESSED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True, slots=True)
class POScoreWeights:
    grounding: float = 0.24
    correctness: float = 0.18
    completeness: float = 0.14
    missing_requirements: float = 0.10
    hallucination_safety: float = 0.16
    actionability: float = 0.10
    intent_adherence: float = 0.08

    def __post_init__(self) -> None:
        values = tuple(asdict(self).values())
        if any((not isinstance(v, (int, float))) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("all scoring weights must be finite non-negative numbers")
        if not math.isclose(sum(values), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("scoring weights must sum to 1.0")


@dataclass(frozen=True, slots=True)
class VariantIdentity:
    variant_id: str
    code_ref: str
    config_sha256: str

    def __post_init__(self) -> None:
        if not self.variant_id.strip():
            raise ValueError("variant_id must not be empty")
        if not self.code_ref.strip():
            raise ValueError("code_ref must not be empty")
        if not self.config_sha256.strip():
            raise ValueError("config_sha256 must not be empty")


class RuntimeVariant(Protocol):
    @property
    def identity(self) -> VariantIdentity: ...

    async def execute(self, query: str, *, session_id: str) -> HarnessResponse: ...


@dataclass(frozen=True, slots=True)
class CallableRuntimeVariant:
    """Adapter around a real async runtime callable.

    ``executor`` must invoke a real PO Agent/Harness implementation.  The class
    contains no canned responses and no synthetic improvement scores.
    """

    identity: VariantIdentity
    executor: Callable[[str, str], Awaitable[HarnessResponse]]

    async def execute(self, query: str, *, session_id: str) -> HarnessResponse:
        response = await self.executor(query, session_id)
        if not isinstance(response, HarnessResponse):
            raise TypeError("runtime variant must return HarnessResponse")
        return response


@dataclass(frozen=True, slots=True)
class DimensionScores:
    grounding: float
    correctness: float
    completeness: float
    missing_requirements: float
    hallucination_safety: float
    actionability: float
    intent_adherence: float
    total: float
    blocked: bool = False
    block_reason: str | None = None


@dataclass(frozen=True, slots=True)
class CaseResult:
    task_key: str
    query: str
    baseline_response: str
    candidate_response: str
    baseline: DimensionScores
    candidate: DimensionScores
    delta: float
    verdict: CaseVerdict


@dataclass(frozen=True, slots=True)
class ExperimentManifest:
    experiment_id: str
    frozen_batch_sha256: str
    task_keys: tuple[str, ...]
    queries: tuple[str, ...]
    baseline: VariantIdentity
    candidate: VariantIdentity
    scoring_sha256: str
    manifest_sha256: str


@dataclass(frozen=True, slots=True)
class ExperimentReport:
    manifest: ExperimentManifest
    cases: tuple[CaseResult, ...]
    baseline_aggregate_score: float
    candidate_aggregate_score: float
    absolute_delta: float
    relative_delta: float
    improved_cases: int
    equivalent_cases: int
    regressed_cases: int
    blocked_cases: int
    baseline_hallucination_rate: float
    candidate_hallucination_rate: float
    verdict: ExperimentVerdict
    report_sha256: str


class POQualityJudge(Protocol):
    def score(
        self,
        *,
        snapshot: Mapping[str, object],
        query: str,
        response: HarnessResponse,
    ) -> DimensionScores: ...


class DeterministicPOQualityJudge:
    """Conservative judge using only frozen source facts and response evidence.

    The judge intentionally avoids pretending to understand business truth that is
    absent from the source.  ``correctness`` is therefore a structural/source-bound
    proxy rather than an LLM opinion.  Any runtime failure or foreign evidence is
    fail-closed.
    """

    _FIELD_LABELS: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("description", ("описан", "описание", "description")),
        ("assignee", ("исполнитель", "assignee", "назначен")),
        ("priority", ("приоритет", "priority")),
        ("sprint_id", ("спринт", "sprint")),
        ("release_id", ("релиз", "release")),
    )

    def __init__(self, weights: POScoreWeights | None = None) -> None:
        self.weights = weights or POScoreWeights()

    @staticmethod
    def _clamp(value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("score must be finite")
        return min(1.0, max(0.0, value))

    @staticmethod
    def _response_text(response: HarnessResponse) -> str:
        data = json.dumps(response.data, ensure_ascii=False, sort_keys=True, default=str) if response.data is not None else ""
        return " ".join((response.answer or "", response.question or "", data)).strip()

    @staticmethod
    def _evidence(response: HarnessResponse) -> tuple[dict[str, object], ...]:
        return tuple(item.to_dict() for item in response.evidence)

    @staticmethod
    def _task_key(snapshot: Mapping[str, object]) -> str:
        key = str(snapshot.get("key") or "").strip().upper()
        if not key:
            raise ValueError("frozen snapshot must contain task key")
        return key

    def _grounding(self, task_key: str, response: HarnessResponse) -> tuple[float, bool]:
        evidence = self._evidence(response)
        if not evidence:
            return 0.0, False
        good = 0
        foreign = False
        for item in evidence:
            source = str(item.get("source") or "").casefold()
            entity_id = str(item.get("entity_id") or "").strip().upper()
            if entity_id and entity_id != task_key:
                foreign = True
            if source in {"as21", "swtr", "as21_history", "deterministic"} and (not entity_id or entity_id == task_key):
                good += 1
        return good / len(evidence), foreign

    @staticmethod
    def _fact_coverage(snapshot: Mapping[str, object], text: str) -> float:
        lowered = text.casefold()
        facts = (
            snapshot.get("key"),
            snapshot.get("title"),
            snapshot.get("status"),
            snapshot.get("priority"),
            snapshot.get("assignee"),
        )
        available = [str(value).strip() for value in facts if value not in (None, "") and str(value).strip()]
        if not available:
            return 0.0
        matched = sum(1 for fact in available if fact.casefold() in lowered)
        return matched / len(available)

    def _missing_requirements(self, snapshot: Mapping[str, object], query: str, text: str) -> float:
        q = query.casefold()
        if not any(token in q for token in ("не хватает", "качество", "вопрос")):
            return 1.0 if text else 0.0
        missing: list[tuple[str, ...]] = []
        for field, labels in self._FIELD_LABELS:
            value = snapshot.get(field)
            if value in (None, "", [], ()):
                missing.append(labels)
        if not missing:
            return 1.0 if text else 0.0
        lowered = text.casefold()
        hits = sum(1 for labels in missing if any(label in lowered for label in labels))
        return hits / len(missing)

    @staticmethod
    def _actionability(query: str, text: str) -> float:
        if not text.strip():
            return 0.0
        lowered = text.casefold()
        structure = any(marker in text for marker in ("\n-", "\n•", "\n1.", "\n2."))
        action_words = any(word in lowered for word in ("уточ", "добав", "провер", "соглас", "нужно", "следует", "рекомен"))
        question_focus = "вопрос" in query.casefold() and "?" in text
        return min(1.0, 0.45 + 0.25 * structure + 0.20 * action_words + 0.10 * question_focus)

    @staticmethod
    def _intent_adherence(query: str, text: str, response: HarnessResponse) -> float:
        if response.status is ResponseStatus.FAILED or not text.strip():
            return 0.0
        q = query.casefold()
        lowered = text.casefold()
        if "суммар" in q:
            return 1.0 if len(text) >= 20 else 0.5
        if "не хватает" in q or "качество" in q:
            return 1.0 if any(word in lowered for word in ("не", "отсутств", "недостат", "уточ", "качест")) else 0.6
        if "рис" in q:
            return 1.0 if "рис" in lowered else 0.6
        if "вопрос" in q:
            return 1.0 if "?" in text else 0.6
        return 0.8

    def score(self, *, snapshot: Mapping[str, object], query: str, response: HarnessResponse) -> DimensionScores:
        task_key = self._task_key(snapshot)
        text = self._response_text(response)
        warning_text = " ".join(response.warnings).casefold()
        grounding, foreign = self._grounding(task_key, response)
        provider_failure = response.status is ResponseStatus.FAILED or "provider_error" in warning_text
        explicit_false_green = any(token in warning_text for token in ("halluc", "ungrounded", "wrong_skill", "wrong skill"))
        blocked = provider_failure or foreign or explicit_false_green or not text.strip()
        reason = None
        if provider_failure:
            reason = "runtime/provider failure"
        elif foreign:
            reason = "foreign evidence entity"
        elif explicit_false_green:
            reason = "false-green signal"
        elif not text.strip():
            reason = "empty response"

        correctness = 0.0 if blocked else min(1.0, 0.45 + 0.55 * grounding)
        completeness = 0.0 if blocked else self._fact_coverage(snapshot, text)
        missing = 0.0 if blocked else self._missing_requirements(snapshot, query, text)
        hallucination_safety = 0.0 if (foreign or explicit_false_green) else (0.25 if provider_failure else 1.0)
        actionability = 0.0 if blocked else self._actionability(query, text)
        adherence = 0.0 if blocked else self._intent_adherence(query, text, response)

        values = {
            "grounding": 0.0 if blocked else grounding,
            "correctness": correctness,
            "completeness": completeness,
            "missing_requirements": missing,
            "hallucination_safety": hallucination_safety,
            "actionability": actionability,
            "intent_adherence": adherence,
        }
        values = {name: self._clamp(value) for name, value in values.items()}
        weighted = sum(values[name] * getattr(self.weights, name) for name in values)
        total = 0.0 if blocked else round(self._clamp(weighted), 6)
        return DimensionScores(**values, total=total, blocked=blocked, block_reason=reason)


class RealBaselineCandidateEvaluator:
    """Compare two real runtime variants on one immutable batch and query matrix."""

    def __init__(
        self,
        *,
        judge: POQualityJudge | None = None,
        equivalent_delta: float = 0.02,
        min_improved_cases: int = 1,
        max_regressed_cases: int = 0,
    ) -> None:
        if equivalent_delta < 0 or not math.isfinite(equivalent_delta):
            raise ValueError("equivalent_delta must be finite and non-negative")
        if min_improved_cases <= 0:
            raise ValueError("min_improved_cases must be positive")
        if max_regressed_cases < 0:
            raise ValueError("max_regressed_cases must be non-negative")
        self._judge = judge or DeterministicPOQualityJudge()
        self._equivalent_delta = equivalent_delta
        self._min_improved_cases = min_improved_cases
        self._max_regressed_cases = max_regressed_cases

    @staticmethod
    def _canonical_sha(value: object) -> str:
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        return sha256(payload.encode("utf-8")).hexdigest()

    def _manifest(
        self,
        *,
        experiment_id: str,
        batch: SWTRShadowBatch,
        queries: tuple[str, ...],
        baseline: VariantIdentity,
        candidate: VariantIdentity,
    ) -> ExperimentManifest:
        if not experiment_id.strip():
            raise ValueError("experiment_id must not be empty")
        if not batch.cases:
            raise ValueError("frozen batch must not be empty")
        if baseline.variant_id == candidate.variant_id:
            raise ValueError("baseline and candidate variant_id must differ")
        if (baseline.code_ref, baseline.config_sha256) == (candidate.code_ref, candidate.config_sha256):
            raise ValueError("baseline and candidate must be genuinely distinct implementations/configurations")
        if not queries or any(not query.strip() for query in queries):
            raise ValueError("query set must contain non-empty queries")

        weights = getattr(self._judge, "weights", None)
        scoring_sha = self._canonical_sha(asdict(weights) if weights is not None else type(self._judge).__qualname__)
        material = {
            "experiment_id": experiment_id,
            "frozen_batch_sha256": batch.batch_sha256,
            "task_keys": tuple(case.task_key for case in batch.cases),
            "queries": queries,
            "baseline": asdict(baseline),
            "candidate": asdict(candidate),
            "scoring_sha256": scoring_sha,
        }
        manifest_sha = self._canonical_sha(material)
        return ExperimentManifest(
            experiment_id=experiment_id,
            frozen_batch_sha256=batch.batch_sha256,
            task_keys=tuple(case.task_key for case in batch.cases),
            queries=queries,
            baseline=baseline,
            candidate=candidate,
            scoring_sha256=scoring_sha,
            manifest_sha256=manifest_sha,
        )

    @staticmethod
    def _render(template: str, snapshot: SWTRTaskSnapshot) -> str:
        return template.format(task_key=snapshot.task_key)

    @staticmethod
    def _answer(response: HarnessResponse) -> str:
        return (response.answer or response.question or "").strip()

    def _case_verdict(self, baseline: DimensionScores, candidate: DimensionScores) -> CaseVerdict:
        if baseline.blocked or candidate.blocked:
            return CaseVerdict.BLOCKED
        delta = candidate.total - baseline.total
        if abs(delta) <= self._equivalent_delta:
            return CaseVerdict.EQUIVALENT
        return CaseVerdict.IMPROVED if delta > 0 else CaseVerdict.REGRESSED

    async def run(
        self,
        *,
        experiment_id: str,
        batch: SWTRShadowBatch,
        baseline: RuntimeVariant,
        candidate: RuntimeVariant,
        query_templates: Sequence[str] = DEFAULT_QUERY_TEMPLATES,
    ) -> ExperimentReport:
        queries = tuple(str(item).strip() for item in query_templates)
        manifest = self._manifest(
            experiment_id=experiment_id,
            batch=batch,
            queries=queries,
            baseline=baseline.identity,
            candidate=candidate.identity,
        )

        results: list[CaseResult] = []
        for snapshot in batch.cases:
            detached = snapshot.as_dict()
            for index, template in enumerate(queries):
                query = self._render(template, snapshot)
                case_material = f"{manifest.manifest_sha256}:{snapshot.task_key}:{index}"
                # Alternate execution order deterministically to reduce systematic
                # first-run/cache bias without revealing one answer to the other.
                candidate_first = int(sha256(case_material.encode("utf-8")).hexdigest(), 16) % 2 == 0
                baseline_session = f"{experiment_id}:baseline:{snapshot.task_key}:{index}"
                candidate_session = f"{experiment_id}:candidate:{snapshot.task_key}:{index}"
                if candidate_first:
                    candidate_response = await candidate.execute(query, session_id=candidate_session)
                    baseline_response = await baseline.execute(query, session_id=baseline_session)
                else:
                    baseline_response = await baseline.execute(query, session_id=baseline_session)
                    candidate_response = await candidate.execute(query, session_id=candidate_session)

                baseline_score = self._judge.score(snapshot=detached, query=query, response=baseline_response)
                candidate_score = self._judge.score(snapshot=detached, query=query, response=candidate_response)
                verdict = self._case_verdict(baseline_score, candidate_score)
                results.append(
                    CaseResult(
                        task_key=snapshot.task_key,
                        query=query,
                        baseline_response=self._answer(baseline_response),
                        candidate_response=self._answer(candidate_response),
                        baseline=baseline_score,
                        candidate=candidate_score,
                        delta=round(candidate_score.total - baseline_score.total, 6),
                        verdict=verdict,
                    )
                )

        if not results:
            raise RuntimeError("experiment produced no cases")
        baseline_aggregate = round(sum(item.baseline.total for item in results) / len(results), 6)
        candidate_aggregate = round(sum(item.candidate.total for item in results) / len(results), 6)
        absolute_delta = round(candidate_aggregate - baseline_aggregate, 6)
        relative_delta = 0.0 if baseline_aggregate == 0 else round(absolute_delta / baseline_aggregate, 6)
        improved = sum(item.verdict is CaseVerdict.IMPROVED for item in results)
        equivalent = sum(item.verdict is CaseVerdict.EQUIVALENT for item in results)
        regressed = sum(item.verdict is CaseVerdict.REGRESSED for item in results)
        blocked = sum(item.verdict is CaseVerdict.BLOCKED for item in results)
        baseline_hallucination_rate = round(sum(item.baseline.hallucination_safety < 1.0 for item in results) / len(results), 6)
        candidate_hallucination_rate = round(sum(item.candidate.hallucination_safety < 1.0 for item in results) / len(results), 6)

        if blocked or regressed > self._max_regressed_cases:
            verdict = ExperimentVerdict.REJECTED
        elif improved >= self._min_improved_cases and candidate_aggregate > baseline_aggregate:
            verdict = ExperimentVerdict.APPROVAL_REQUIRED
        else:
            verdict = ExperimentVerdict.INSUFFICIENT_EVIDENCE

        report_material = {
            "manifest": manifest.manifest_sha256,
            "cases": [
                {
                    "task_key": item.task_key,
                    "query": item.query,
                    "baseline_total": item.baseline.total,
                    "candidate_total": item.candidate.total,
                    "delta": item.delta,
                    "verdict": item.verdict.value,
                }
                for item in results
            ],
            "verdict": verdict.value,
        }
        return ExperimentReport(
            manifest=manifest,
            cases=tuple(results),
            baseline_aggregate_score=baseline_aggregate,
            candidate_aggregate_score=candidate_aggregate,
            absolute_delta=absolute_delta,
            relative_delta=relative_delta,
            improved_cases=improved,
            equivalent_cases=equivalent,
            regressed_cases=regressed,
            blocked_cases=blocked,
            baseline_hallucination_rate=baseline_hallucination_rate,
            candidate_hallucination_rate=candidate_hallucination_rate,
            verdict=verdict,
            report_sha256=self._canonical_sha(report_material),
        )


def runtime_variant_from_bundle(
    *,
    variant_id: str,
    code_ref: str,
    config: Mapping[str, object],
    runtime: object,
) -> CallableRuntimeVariant:
    """Create a runtime variant from an object exposing async ``process``.

    This small adapter keeps the evaluation layer independent from a particular
    runtime bundle implementation while still executing the real Harness API.
    """
    process = getattr(runtime, "process", None)
    if process is None or not callable(process):
        raise TypeError("runtime must expose callable async process(request)")
    config_sha = RealBaselineCandidateEvaluator._canonical_sha(dict(config))

    async def execute(query: str, session_id: str) -> HarnessResponse:
        response = await process(HarnessRequest(query=query, session_id=session_id))
        if not isinstance(response, HarnessResponse):
            raise TypeError("runtime.process() must return HarnessResponse")
        return response

    return CallableRuntimeVariant(
        identity=VariantIdentity(
            variant_id=variant_id,
            code_ref=code_ref,
            config_sha256=config_sha,
        ),
        executor=execute,
    )
