from __future__ import annotations

from datetime import datetime, timezone

import pytest

from po_agent.adapters import FrozenAS21Adapter
from po_agent.adapters.swtr_shadow import SWTRShadowBatch, SWTRTaskSnapshot
from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    StatusCategory,
    StatusTransition,
    Task,
    TaskStatus,
)


def _task(key: str = "WMB-29242") -> Task:
    now = datetime(2026, 8, 18, 12, 0, tzinfo=timezone.utc)
    return Task(
        key=key,
        id=f"id-{key}",
        title="Real SWTR task",
        description="Frozen real-case corpus",
        status=TaskStatus.IN_PROGRESS,
        status_category=StatusCategory.ACTIVE_WORK,
        status_transitions=[
            StatusTransition(
                from_status=TaskStatus.OPEN,
                to_status=TaskStatus.IN_PROGRESS,
                timestamp=now,
                author="tester",
            )
        ],
        created_at=now,
        updated_at=now,
        sprint_id="SPRINT-42",
        release_id="REL-1",
        depends_on=["WMB-10000"],
        labels=["real", "pilot"],
        components=["harness"],
        attachments=[
            Attachment(
                id="att-1",
                name="requirements.pdf",
                type=AttachmentType.PDF,
                size_bytes=123,
                created_at=now,
            )
        ],
        source="swtr",
    )


def _batch(*tasks: Task) -> SWTRShadowBatch:
    return SWTRShadowBatch.build(SWTRTaskSnapshot.from_task(task) for task in tasks)


def test_from_shadow_batch_builds_frozen_corpus():
    adapter = FrozenAS21Adapter.from_shadow_batch(_batch(_task()))
    assert adapter.task_count == 1
    assert adapter.task_keys == ("WMB-29242",)


@pytest.mark.asyncio
async def test_get_task_returns_detached_copy_including_nested_state():
    adapter = FrozenAS21Adapter([_task()])

    first = await adapter.get_task("wmb-29242")
    assert first is not None
    first.title = "mutated"
    first.labels.append("evil")
    first.depends_on.clear()
    first.components[0] = "changed"
    first.status_transitions[0].author = "attacker"
    first.attachments[0].name = "changed.pdf"

    second = await adapter.get_task("WMB-29242")
    assert second is not None
    assert second.title == "Real SWTR task"
    assert second.labels == ["real", "pilot"]
    assert second.depends_on == ["WMB-10000"]
    assert second.components == ["harness"]
    assert second.status_transitions[0].author == "tester"
    assert second.attachments[0].name == "requirements.pdf"


@pytest.mark.asyncio
async def test_search_is_bounded_and_supports_key_and_text():
    adapter = FrozenAS21Adapter([_task("WMB-29242"), _task("WMB-29830")])

    exact = await adapter.search_tasks("key = WMB-29242", max_results=1)
    assert [task.key for task in exact] == ["WMB-29242"]

    text = await adapter.search_tasks("real swtr", max_results=1)
    assert len(text) == 1

    all_tasks = await adapter.search_tasks("", max_results=1)
    assert len(all_tasks) == 1

    with pytest.raises(ValueError, match="positive"):
        await adapter.search_tasks("", max_results=0)
    with pytest.raises(ValueError, match="complex JQL"):
        await adapter.search_tasks("project = WMB AND status = Open")


@pytest.mark.asyncio
async def test_history_sprint_release_and_attachments_use_frozen_data_only():
    adapter = FrozenAS21Adapter([_task()])

    history = await adapter.get_task_history("WMB-29242")
    assert len(history) == 1
    assert history[0].to_status == TaskStatus.IN_PROGRESS

    sprint = await adapter.get_sprint_tasks("SPRINT-42")
    assert [task.key for task in sprint] == ["WMB-29242"]

    release = await adapter.get_release_tasks("REL-1")
    assert [task.key for task in release] == ["WMB-29242"]

    attachments = await adapter.get_attachment_metadata("WMB-29242", "att-1")
    assert [item.id for item in attachments] == ["att-1"]

    history[0].author = "mutated"
    attachments[0].name = "mutated.pdf"
    assert (await adapter.get_task_history("WMB-29242"))[0].author == "tester"
    assert (await adapter.get_attachment_metadata("WMB-29242"))[0].name == "requirements.pdf"


def test_duplicate_keys_fail_closed():
    with pytest.raises(ValueError, match="duplicate frozen task key"):
        FrozenAS21Adapter([_task(), _task()])


@pytest.mark.asyncio
async def test_close_is_idempotent_and_never_creates_live_fallback():
    adapter = FrozenAS21Adapter([_task()])
    await adapter.close()
    await adapter.close()

    # The corpus is still purely local; close cannot reconnect or substitute a
    # TaskApi adapter.  A post-close read therefore remains deterministic.
    task = await adapter.get_task("WMB-29242")
    assert task is not None
    assert task.key == "WMB-29242"

    graph = repr(adapter.__dict__)
    assert "TaskApiAS21Adapter" not in graph
    assert "SWTRReadOnlyShadowSource" not in graph
    assert "http://" not in graph
    assert "https://" not in graph
