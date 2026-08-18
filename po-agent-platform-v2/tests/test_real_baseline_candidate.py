from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256

import pytest

from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot
from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.contracts import Evidence, HarnessResponse, ResponseStatus
from po_agent.harness.real_baseline_candidate import (
    CallableRuntimeVariant,
    CaseVerdict,
    ExperimentVerdict,
    RealBaselineCandidateEvaluator,
    VariantIdentity,
)


def _task(key: str = "WMB-29242") -> Task:
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    return Task(
        key=key,
        id=f"id-{key}",
        title="Сделать restart-safe evaluation harness",
        description="Нужно сравнивать baseline и candidate на одинаковом frozen corpus",
        status=TaskStatus.IN_PROGRESS,
        status_category=StatusCategory.ACTIVE_WORK,
        created_at=now,
        updated_at=now,
        sprint_id=None,
        release_id=None,
        source="swtr",
    )


def _batch() -> SWTRShadowBatch:
    return SWTRShadowBatch.build([SWTRTaskSnapshot.from_task(_task())])


def _identity(name: str, config: str) -> VariantIdentity:
    return VariantIdentity(
        variant_id=name,
        code_ref=f"sha-{name}",
        config_sha256=sha256(config.encode()).hexdigest(),
    )


def _response(key: str, *, quality: str = "good", foreign: bool = False) -> HarnessResponse:
    entity_id = "WMB-99999" if foreign else key
    if quality == "good":
        answer = (
            f"Задача {key}: Сделать restart-safe evaluation harness.\n"
            "- Нужно сравнивать baseline и candidate на одинаковом frozen corpus.\n"
            "- Не указан исполнитель; нужно уточнить исполнителя.\n"
            "- Не указан приоритет; следует согласовать приоритет.\n"
            "- Не указан спринт и релиз; нужно уточнить план поставки.\n"
            "Какие критерии приемки должны быть зафиксированы?"
        )
    elif quality == "weak":
        answer = f"Задача {key} находится в работе."
    else:
        answer = ""
    return HarnessResponse(
        status=ResponseStatus.COMPLETED if answer else ResponseStatus.FAILED,
        trace_id=f"trace-{key}-{quality}",
        session_id="s",
        answer=answer,
        evidence=[
            Evidence(
                type="task",
                source="swtr",
                label="task",
                entity_id=entity_id,
                value=key,
            )
        ],
        warnings=[],
    )


def _variant(name: str, config: str, quality: str, calls: list[tuple[str, str]]) -> CallableRuntimeVariant:
    async def execute(query: str, session_id: str) -> HarnessResponse:
        calls.append((query, session_id))
        key = "WMB-29242"
        return _response(key, quality=quality)

    return CallableRuntimeVariant(identity=_identity(name, config), executor=execute)


@pytest.mark.asyncio
async def test_same_frozen_corpus_and_query_matrix_are_used_for_both_variants():
    baseline_calls: list[tuple[str, str]] = []
    candidate_calls: list[tuple[str, str]] = []
    baseline = _variant("baseline", "cfg-a", "weak", baseline_calls)
    candidate = _variant("candidate", "cfg-b", "good", candidate_calls)
    evaluator = RealBaselineCandidateEvaluator(min_improved_cases=1)

    report = await evaluator.run(
        experiment_id="real-1",
        batch=_batch(),
        baseline=baseline,
        candidate=candidate,
        query_templates=("Суммаризируй задачу {task_key}", "Чего не хватает в задаче {task_key}?"),
    )

    assert [item[0] for item in baseline_calls] == [item[0] for item in candidate_calls]
    assert all("WMB-29242" in query for query, _ in baseline_calls)
    assert report.manifest.frozen_batch_sha256 == _batch().batch_sha256
    assert report.manifest.task_keys == ("WMB-29242",)
    assert report.verdict is ExperimentVerdict.APPROVAL_REQUIRED
    assert report.candidate_aggregate_score > report.baseline_aggregate_score


@pytest.mark.asyncio
async def test_identical_variant_identity_fails_closed_before_execution():
    calls: list[tuple[str, str]] = []
    same_identity = _identity("same", "same")

    async def execute(query: str, session_id: str) -> HarnessResponse:
        calls.append((query, session_id))
        return _response("WMB-29242")

    baseline = CallableRuntimeVariant(identity=same_identity, executor=execute)
    candidate = CallableRuntimeVariant(identity=same_identity, executor=execute)

    with pytest.raises(ValueError, match="variant_id must differ"):
        await RealBaselineCandidateEvaluator().run(
            experiment_id="real-2",
            batch=_batch(),
            baseline=baseline,
            candidate=candidate,
            query_templates=("Суммаризируй задачу {task_key}",),
        )
    assert calls == []


@pytest.mark.asyncio
async def test_same_code_and_config_under_different_labels_is_rejected():
    calls: list[tuple[str, str]] = []

    async def execute(query: str, session_id: str) -> HarnessResponse:
        calls.append((query, session_id))
        return _response("WMB-29242")

    config = sha256(b"same-config").hexdigest()
    baseline = CallableRuntimeVariant(
        identity=VariantIdentity("baseline", "same-sha", config), executor=execute
    )
    candidate = CallableRuntimeVariant(
        identity=VariantIdentity("candidate", "same-sha", config), executor=execute
    )

    with pytest.raises(ValueError, match="genuinely distinct"):
        await RealBaselineCandidateEvaluator().run(
            experiment_id="real-3",
            batch=_batch(),
            baseline=baseline,
            candidate=candidate,
            query_templates=("Суммаризируй задачу {task_key}",),
        )
    assert calls == []


@pytest.mark.asyncio
async def test_candidate_regression_is_rejected_not_promoted():
    baseline_calls: list[tuple[str, str]] = []
    candidate_calls: list[tuple[str, str]] = []
    baseline = _variant("baseline", "cfg-a", "good", baseline_calls)
    candidate = _variant("candidate", "cfg-b", "weak", candidate_calls)

    report = await RealBaselineCandidateEvaluator().run(
        experiment_id="real-4",
        batch=_batch(),
        baseline=baseline,
        candidate=candidate,
        query_templates=("Чего не хватает в задаче {task_key}?",),
    )

    assert report.regressed_cases == 1
    assert report.cases[0].verdict is CaseVerdict.REGRESSED
    assert report.verdict is ExperimentVerdict.REJECTED


@pytest.mark.asyncio
async def test_foreign_evidence_blocks_case_and_fails_closed():
    baseline_calls: list[tuple[str, str]] = []
    baseline = _variant("baseline", "cfg-a", "good", baseline_calls)
    candidate_calls: list[tuple[str, str]] = []

    async def candidate_execute(query: str, session_id: str) -> HarnessResponse:
        candidate_calls.append((query, session_id))
        return _response("WMB-29242", quality="good", foreign=True)

    candidate = CallableRuntimeVariant(
        identity=_identity("candidate", "cfg-b"),
        executor=candidate_execute,
    )

    report = await RealBaselineCandidateEvaluator().run(
        experiment_id="real-5",
        batch=_batch(),
        baseline=baseline,
        candidate=candidate,
        query_templates=("Суммаризируй задачу {task_key}",),
    )

    assert report.blocked_cases == 1
    assert report.cases[0].candidate.blocked is True
    assert report.cases[0].candidate.block_reason == "foreign evidence entity"
    assert report.verdict is ExperimentVerdict.REJECTED


@pytest.mark.asyncio
async def test_no_improvement_returns_insufficient_evidence():
    baseline_calls: list[tuple[str, str]] = []
    candidate_calls: list[tuple[str, str]] = []
    baseline = _variant("baseline", "cfg-a", "good", baseline_calls)
    candidate = _variant("candidate", "cfg-b", "good", candidate_calls)

    report = await RealBaselineCandidateEvaluator().run(
        experiment_id="real-6",
        batch=_batch(),
        baseline=baseline,
        candidate=candidate,
        query_templates=("Суммаризируй задачу {task_key}",),
    )

    assert report.equivalent_cases == 1
    assert report.verdict is ExperimentVerdict.INSUFFICIENT_EVIDENCE
    assert report.report_sha256
