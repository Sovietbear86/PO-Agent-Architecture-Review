from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.domain.models import AttachmentType
from po_agent.harness.v4_plugins._task_live_handlers import build_task_search_attachments


def _attachment(name: str):
    return SimpleNamespace(
        id=name,
        name=name,
        type=AttachmentType.OTHER,
        size_bytes=123,
    )


def _task(key: str, *, sprint_id: str, with_file: bool):
    return SimpleNamespace(
        key=key,
        id=key,
        title=key,
        description="",
        status=SimpleNamespace(value="In progress"),
        status_category=SimpleNamespace(value="active_work"),
        assignee="user",
        assignee_id="user",
        assignee_login="user",
        priority=None,
        project_space="DMS",
        sprint_id=sprint_id,
        release_id=None,
        source="swtr",
        source_data={},
        attachments=[_attachment(f"{key}.txt")] if with_file else [],
    )


class Adapter:
    def __init__(self):
        self.sprint_calls = []
        self.metadata_calls = []
        self.tasks = [
            _task("DMS-1", sprint_id="DMS-SPRNT-3", with_file=True),
            _task("DMS-2", sprint_id="DMS-SPRNT-3", with_file=False),
        ]

    async def get_sprint_tasks(self, sprint_id: str, space=None):
        self.sprint_calls.append((sprint_id, space))
        return list(self.tasks)

    async def get_attachment_metadata(self, task_key: str):
        self.metadata_calls.append(task_key)
        return []

    async def _get_resilient(self, *args, **kwargs):
        raise AssertionError("sprint-scoped attachment search must not broaden to task-query")


def test_attachment_search_preserves_source_backed_sprint_scope():
    adapter = Adapter()
    runtime = SimpleNamespace(adapter=adapter)

    result = asyncio.run(
        build_task_search_attachments(runtime)(
            {"space": "DMS", "sprint_id": "DMS-SPRNT-3"}
        )
    )

    assert adapter.sprint_calls == [("DMS-SPRNT-3", "DMS")]
    assert adapter.metadata_calls == ["DMS-2"]
    assert result.data["sprint_id"] == "DMS-SPRNT-3"
    assert result.data["space"] == "DMS"
    assert result.data["count"] == 1
    assert result.data["results"][0]["task"]["key"] == "DMS-1"
