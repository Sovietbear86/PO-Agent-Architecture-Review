from __future__ import annotations

from datetime import datetime, timezone

import pytest

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.swtr_shadow import (
    SWTRReadOnlyShadowSource,
    SWTRShadowBudgetExceeded,
    SWTRShadowError,
    SWTRTaskSnapshot,
)
from po_agent.domain.models import StatusCategory, Task, TaskStatus


class StubAS21Adapter(AS21Adapter):
    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = {task.key: task for task in tasks}
        self.closed = False

    async def get_task(self, task_key: str):
        return self.tasks.get(task_key)

    async def search_tasks(self, jql: str, max_results: int = 50, fields=None):
        del jql, fields
        return list(self.tasks.values())[:max_results]

    async def get_task_history(self, task_key: str):
        raise AssertionError("history must not be used by SWTR shadow capture")

    async def get_sprint_tasks(self, sprint_id: str, space=None):
        raise AssertionError("sprint mutation/capability path not required")

    async def get_release_tasks(self, release_id: str, space=None):
        raise AssertionError("release mutation/capability path not required")

    async def get_attachment_metadata(self, task_key: str, attachment_id=None):
        raise AssertionError("attachment download path not required")

    async def close(self):
        self.closed = True


def _task(key: str, *, source: str = "swtr", title: str = "Real case") -> Task:
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    return Task(
        key=key,
        id=f"id-{key}",
        title=title,
        description="Observed from AS21/SWTR",
        status=TaskStatus.IN_PROGRESS,
        status_category=StatusCategory.ACTIVE_WORK,
        created_at=now,
        updated_at=now,
        source=source,
    )


def test_snapshot_is_deterministic_and_content_addressed():
    task = _task("DMS-101")
    first = SWTRTaskSnapshot.from_task(task)
    second = SWTRTaskSnapshot.from_task(task)

    assert first == second
    assert len(first.content_sha256) == 64
    assert first.as_dict()["key"] == "DMS-101"


@pytest.mark.asyncio
async def test_capture_keys_is_bounded_deduplicated_and_read_only():
    adapter = StubAS21Adapter([_task("DMS-101"), _task("DMS-102")])
    source = SWTRReadOnlyShadowSource(adapter, max_cases=2)

    batch = await source.capture_keys([" dms-101 ", "DMS-101", "DMS-102"])

    assert [case.task_key for case in batch.cases] == ["DMS-101", "DMS-102"]
    assert len(batch.batch_sha256) == 64
    assert not hasattr(source, "update_task")
    assert not hasattr(source, "transition_task")
    assert not hasattr(source, "comment")


@pytest.mark.asyncio
async def test_capture_keys_fails_closed_when_task_missing():
    source = SWTRReadOnlyShadowSource(StubAS21Adapter([_task("DMS-101")]))

    with pytest.raises(SWTRShadowError, match="was not found"):
        await source.capture_keys(["DMS-999"])


@pytest.mark.asyncio
async def test_capture_rejects_non_swtr_source():
    source = SWTRReadOnlyShadowSource(
        StubAS21Adapter([_task("DMS-101", source="fixture")])
    )

    with pytest.raises(SWTRShadowError, match="unexpected task source"):
        await source.capture_keys(["DMS-101"])


@pytest.mark.asyncio
async def test_capture_budget_is_enforced_before_source_access():
    source = SWTRReadOnlyShadowSource(
        StubAS21Adapter([_task("DMS-101"), _task("DMS-102")]),
        max_cases=1,
    )

    with pytest.raises(SWTRShadowBudgetExceeded):
        await source.capture_keys(["DMS-101", "DMS-102"])


@pytest.mark.asyncio
async def test_query_limit_is_bounded_and_duplicates_fail_closed():
    source = SWTRReadOnlyShadowSource(StubAS21Adapter([_task("DMS-101")]), max_cases=3)

    with pytest.raises(SWTRShadowBudgetExceeded):
        await source.capture_query("project = DMS", limit=4)

    batch = await source.capture_query("project = DMS", limit=1)
    assert len(batch.cases) == 1


@pytest.mark.asyncio
async def test_close_delegates_to_adapter():
    adapter = StubAS21Adapter([_task("DMS-101")])
    source = SWTRReadOnlyShadowSource(adapter)
    await source.close()
    assert adapter.closed is True
