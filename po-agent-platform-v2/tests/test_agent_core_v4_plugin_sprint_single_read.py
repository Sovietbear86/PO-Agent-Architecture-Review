from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.domain.models import StatusCategory, TaskStatus
from po_agent.harness.v4_plugins.core import build_task_search


def _task(key: str, *, status: TaskStatus) -> SimpleNamespace:
    return SimpleNamespace(
        key=key,
        title=key,
        status=status,
        status_raw=status.value,
        status_type="progress" if status == TaskStatus.IN_PROGRESS else "done",
        status_category=StatusCategory.ACTIVE_WORK if status == TaskStatus.IN_PROGRESS else StatusCategory.COMPLETED,
        is_open=status == TaskStatus.IN_PROGRESS,
        is_completed=status != TaskStatus.IN_PROGRESS,
        is_blocked=False,
        assignee="user",
        assignee_login="user",
        assignee_id="user",
        project_space="DMS",
        sprint_id="DMS-SPRNT-3",
        release_id=None,
        source="swtr",
    )


class Adapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str | None]] = []
        self.tasks = [
            _task("DMS-1", status=TaskStatus.IN_PROGRESS),
            _task("DMS-2", status=TaskStatus.CLOSED),
        ]

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        self.calls.append((sprint_id, space))
        return list(self.tasks)


class Runtime:
    def __init__(self) -> None:
        self.adapter = Adapter()

    @staticmethod
    def _safe_status(raw: str) -> str:
        value = str(raw or "").strip().casefold()
        if value in {"not_completed", "open"}:
            return "not_completed"
        if value in {"completed", "closed"}:
            return "completed"
        return str(raw or "").strip()

    @staticmethod
    def _task_to_dict(task):
        return {
            "key": task.key,
            "title": task.title,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "assignee_login": task.assignee_login,
            "assignee_id": task.assignee_id,
            "project_space": task.project_space,
            "sprint_id": task.sprint_id,
            "release_id": task.release_id,
            "source": task.source,
        }

    async def _task_search(self, args):
        raise AssertionError("sprint-only plugin path must not delegate to duplicate-reading core handler")


def test_sprint_only_task_search_reads_source_once_and_preserves_status_filter() -> None:
    runtime = Runtime()
    result = asyncio.run(
        build_task_search(runtime)(
            {
                "space": "DMS",
                "sprint_id": "DMS-SPRNT-3",
                "status": "not_completed",
            }
        )
    )

    assert runtime.adapter.calls == [("DMS-SPRNT-3", "DMS")]
    assert result.data["count"] == 1
    assert result.data["task_keys"] == ["DMS-1"]
    assert result.data["filters"] == {
        "space": "DMS",
        "sprint_id": "DMS-SPRNT-3",
        "status": "not_completed",
    }
