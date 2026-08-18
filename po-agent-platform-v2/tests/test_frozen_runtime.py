from __future__ import annotations

from datetime import datetime, timezone

import pytest

from po_agent.adapters import FrozenAS21Adapter
from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot
from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.runtime_factory import build_frozen_runtime_bundle


def _task(key: str = "WMB-29242") -> Task:
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    return Task(
        key=key,
        id=f"id-{key}",
        title="Improve frozen SWTR evaluation",
        description="Implement deterministic evaluation and document acceptance criteria.",
        status=TaskStatus.IN_PROGRESS,
        status_category=StatusCategory.ACTIVE_WORK,
        created_at=now,
        updated_at=now,
        labels=["real-pilot"],
        source="swtr",
    )


def _batch() -> SWTRShadowBatch:
    return SWTRShadowBatch.build([SWTRTaskSnapshot.from_task(_task())])


def test_frozen_runtime_factory_uses_frozen_adapter_and_no_live_source():
    bundle = build_frozen_runtime_bundle(_batch())

    assert bundle.mode == "frozen"
    assert isinstance(bundle.adapter, FrozenAS21Adapter)
    assert bundle.adapter.task_keys == ("WMB-29242",)

    # The selected adapter is the object exposed through the real production
    # runtime stack; a live TaskApi adapter is not constructed or retained.
    assert bundle.runtime.adapter is bundle.adapter
    graph = repr(bundle.adapter.__dict__)
    assert "TaskApiAS21Adapter" not in graph
    assert "localhost:8003" not in graph


@pytest.mark.asyncio
async def test_real_harness_executes_task_summary_on_frozen_task():
    bundle = build_frozen_runtime_bundle(_batch())

    response = await bundle.runtime.process(
        HarnessRequest(query="Суммаризируй WMB-29242: что нужно сделать?")
    )

    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-summary"
    assert response.answer
    assert response.evidence
    assert any(item.entity_id == "WMB-29242" for item in response.evidence)
    assert response.data["goal"]


@pytest.mark.asyncio
async def test_real_harness_executes_quality_and_missing_requirements_on_same_corpus():
    bundle = build_frozen_runtime_bundle(_batch())

    quality = await bundle.runtime.process(
        HarnessRequest(query="Оцени постановку задачи WMB-29242")
    )
    missing = await bundle.runtime.process(
        HarnessRequest(query="Чего не хватает в задаче WMB-29242?")
    )

    assert quality.status is ResponseStatus.COMPLETED
    assert quality.skill_id == "task-quality"
    assert 0 <= quality.data["score"] <= 100

    assert missing.status is ResponseStatus.COMPLETED
    assert missing.skill_id == "task-missing-requirements"
    assert "missing_elements" in missing.data

    # Multiple real Harness calls remain offline and operate on the exact same
    # immutable corpus rather than re-reading SWTR between capabilities.
    assert bundle.adapter.task_count == 1
    task = await bundle.adapter.get_task("WMB-29242")
    assert task is not None
    assert task.title == "Improve frozen SWTR evaluation"
