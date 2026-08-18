"""Adapters for evaluating real PO Agent runtimes on frozen SWTR snapshots.

This module deliberately does not know how to read or mutate AS21/SWTR. It receives
one detached task snapshot at a time and invokes an injected *real* PO Agent case
runner. The wrapper normalizes production CapabilityResult/HarnessResponse output
into AgentObservation for the existing SWTR shadow evaluator.

The important boundary is that baseline and candidate must be actual runtime
callables supplied by the caller; this module contains no mock baseline/candidate
logic and no synthetic score constants.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
import time
from typing import Any, Callable, Mapping, Protocol

from .contracts import CapabilityResult, HarnessResponse, ResponseStatus
from .swtr_real_evaluation import AgentObservation


class RealPOAgentCaseRunner(Protocol):
    """Synchronous case runner executed against a detached frozen snapshot."""

    def __call__(self, snapshot: Mapping[str, object]) -> CapabilityResult | HarnessResponse | Mapping[str, object]:
        ...


@dataclass(frozen=True, slots=True)
class RealPOAgentScoringPolicy:
    """Deterministic scoring of a real PO Agent response.

    The score is intentionally based only on source-grounded response properties,
    not on agent identity. Baseline and candidate therefore cross the same gate.
    """

    answer_weight: float = 0.20
    identity_weight: float = 0.20
    source_fact_weight: float = 0.35
    evidence_weight: float = 0.25

    def __post_init__(self) -> None:
        weights = (
            self.answer_weight,
            self.identity_weight,
            self.source_fact_weight,
            self.evidence_weight,
        )
        if any(weight < 0 for weight in weights):
            raise ValueError("scoring weights must be non-negative")
        if not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("scoring weights must sum to 1.0")


@dataclass(frozen=True, slots=True)
class _NormalizedResult:
    answer: str
    data: object
    evidence: tuple[Mapping[str, object], ...]
    warnings: tuple[str, ...]
    provider_error: bool
    llm_calls: int


def _json_text(value: object) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except (TypeError, ValueError):
        return str(value)


def _normalize_evidence(items: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(items, (list, tuple)):
        return ()
    normalized: list[Mapping[str, object]] = []
    for item in items:
        if hasattr(item, "to_dict"):
            value = item.to_dict()
        elif isinstance(item, Mapping):
            value = dict(item)
        else:
            continue
        normalized.append(value)
    return tuple(normalized)


def _normalize_result(raw: object) -> _NormalizedResult:
    if isinstance(raw, CapabilityResult):
        return _NormalizedResult(
            answer=raw.answer or "",
            data=raw.data,
            evidence=_normalize_evidence(raw.evidence),
            warnings=tuple(str(item) for item in raw.warnings),
            provider_error=False,
            llm_calls=0,
        )
    if isinstance(raw, HarnessResponse):
        failed = raw.status is ResponseStatus.FAILED
        return _NormalizedResult(
            answer=raw.answer or raw.question or "",
            data=raw.data,
            evidence=_normalize_evidence(raw.evidence),
            warnings=tuple(str(item) for item in raw.warnings),
            provider_error=failed,
            llm_calls=0,
        )
    if isinstance(raw, Mapping):
        answer = str(raw.get("answer") or raw.get("question") or "")
        warnings = raw.get("warnings") or ()
        llm_calls = raw.get("llm_calls", 0)
        return _NormalizedResult(
            answer=answer,
            data=raw.get("data"),
            evidence=_normalize_evidence(raw.get("evidence")),
            warnings=tuple(str(item) for item in warnings) if isinstance(warnings, (list, tuple)) else (str(warnings),),
            provider_error=bool(raw.get("provider_error", False)),
            llm_calls=int(llm_calls) if isinstance(llm_calls, int) and not isinstance(llm_calls, bool) else 0,
        )
    raise TypeError("real PO Agent runner must return CapabilityResult, HarnessResponse, or Mapping")


class RealPOAgentSnapshotAgent:
    """Turn an injected real PO Agent case runner into a SnapshotAgent.

    No AS21 adapter is exposed to the runner. It receives only the detached task
    snapshot that was frozen by SWTRReadOnlyShadowSource. Grounding and score are
    calculated by deterministic rules shared by baseline and candidate.
    """

    _TOKEN_RE = re.compile(r"[A-Za-zА-Яа-яЁё0-9_-]+", re.UNICODE)

    def __init__(
        self,
        runner: RealPOAgentCaseRunner,
        *,
        scoring: RealPOAgentScoringPolicy | None = None,
        runner_id: str,
    ) -> None:
        if not callable(runner):
            raise TypeError("runner must be callable")
        if not runner_id.strip():
            raise ValueError("runner_id must not be empty")
        self._runner = runner
        self._scoring = scoring or RealPOAgentScoringPolicy()
        self._runner_id = runner_id.strip()

    @property
    def runner_id(self) -> str:
        return self._runner_id

    @staticmethod
    def _task_key(snapshot: Mapping[str, object]) -> str:
        key = str(snapshot.get("key") or "").strip().upper()
        if not key:
            raise ValueError("snapshot must contain task key")
        return key

    @classmethod
    def _tokens(cls, value: object) -> set[str]:
        return {token.casefold() for token in cls._TOKEN_RE.findall(str(value)) if len(token) >= 3}

    def _source_fact_coverage(self, snapshot: Mapping[str, object], result: _NormalizedResult) -> float:
        response_text = " ".join((result.answer, _json_text(result.data), _json_text(result.evidence))).casefold()
        facts = [
            snapshot.get("key"),
            snapshot.get("title"),
            snapshot.get("status"),
            snapshot.get("assignee"),
            snapshot.get("priority"),
        ]
        available = [fact for fact in facts if fact not in (None, "")]
        if not available:
            return 0.0
        matched = 0
        for fact in available:
            tokens = self._tokens(fact)
            if tokens and any(token in response_text for token in tokens):
                matched += 1
        return matched / len(available)

    @staticmethod
    def _evidence_grounded(task_key: str, result: _NormalizedResult) -> tuple[bool, float]:
        if not result.evidence:
            return False, 0.0
        valid = 0
        foreign = 0
        for item in result.evidence:
            source = str(item.get("source") or "").casefold()
            entity_id = str(item.get("entity_id") or "").strip().upper()
            if source in {"as21", "swtr", "deterministic", "as21_history"}:
                valid += 1
            if entity_id and entity_id != task_key:
                foreign += 1
        if foreign:
            return False, valid / len(result.evidence)
        return valid > 0, valid / len(result.evidence)

    def __call__(self, snapshot: Mapping[str, object]) -> AgentObservation:
        detached = json.loads(json.dumps(dict(snapshot), ensure_ascii=False, default=str))
        task_key = self._task_key(detached)
        started = time.monotonic()
        try:
            normalized = _normalize_result(self._runner(detached))
        except Exception as exc:  # evaluator must fail closed on real runtime failure
            return AgentObservation(
                answer=f"provider_error:{type(exc).__name__}",
                score=0.0,
                grounded=False,
                provider_error=True,
                latency_ms=(time.monotonic() - started) * 1000.0,
            )

        latency_ms = (time.monotonic() - started) * 1000.0
        answer_ok = bool(normalized.answer.strip())
        identity_ok = task_key.casefold() in normalized.answer.casefold() or task_key.casefold() in _json_text(normalized.data).casefold()
        evidence_grounded, evidence_quality = self._evidence_grounded(task_key, normalized)
        source_coverage = self._source_fact_coverage(detached, normalized)

        score = (
            self._scoring.answer_weight * float(answer_ok)
            + self._scoring.identity_weight * float(identity_ok)
            + self._scoring.source_fact_weight * source_coverage
            + self._scoring.evidence_weight * evidence_quality
        )
        score = round(min(1.0, max(0.0, score)), 6)

        warning_text = " ".join(normalized.warnings).casefold()
        hallucination = "halluc" in warning_text or "ungrounded" in warning_text
        wrong_skill = "wrong_skill" in warning_text or "wrong skill" in warning_text
        provider_error = normalized.provider_error or "provider_error" in warning_text
        grounded = answer_ok and identity_ok and evidence_grounded and not (hallucination or provider_error or wrong_skill)

        return AgentObservation(
            answer=normalized.answer,
            score=score,
            grounded=grounded,
            hallucination=hallucination,
            wrong_skill=wrong_skill,
            provider_error=provider_error,
            latency_ms=latency_ms,
            llm_calls=normalized.llm_calls,
        )
