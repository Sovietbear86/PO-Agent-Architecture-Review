from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.agent_core_v4 import AgentCoreV4Runtime


def _task(key: str, *, status: TaskStatus, status_raw: str, status_type: str, category: StatusCategory):
    now = datetime.now(timezone.utc)
    return Task(
        key=key,
        id=key,
        title=key,
        status=status,
        status_raw=status_raw,
        status_type=status_type,
        status_category=category,
        created_at=now,
        updated_at=now,
        project_space="DMS",
        sprint_id="DMS-SPRNT-3",
        source="swtr",
    )


class Adapter:
    def __init__(self):
        self.tasks = [
            _task("DMS-1", status=TaskStatus.NEED_INFO, status_raw="Need info", status_type="pause", category=StatusCategory.WAITING),
            _task("DMS-2", status=TaskStatus.UNKNOWN, status_raw="На исправлении", status_type="progress", category=StatusCategory.ACTIVE_WORK),
            _task("DMS-3", status=TaskStatus.CLOSED, status_raw="Закрыт", status_type="done", category=StatusCategory.COMPLETED),
        ]

    async def get_sprint_tasks(self, sprint_id: str, space=None):
        return list(self.tasks)

    async def search_tasks(self, query: str, max_results=10000):
        return list(self.tasks)


def _runtime():
    return AgentCoreV4Runtime(
        Adapter(),
        llm=object(),
        model=None,
        team=None,
        legacy_capabilities=None,
    )


def test_task_search_blocked_uses_canonical_blocked_predicate():
    result = asyncio.run(
        _runtime()._task_search({"sprint_id": "DMS-SPRNT-3", "space": "DMS", "status": "blocked"})
    )
    assert result.data["task_keys"] == ["DMS-1"]


def test_task_search_matches_authoritative_source_status_label():
    result = asyncio.run(
        _runtime()._task_search({"sprint_id": "DMS-SPRNT-3", "space": "DMS", "status": "На исправлении"})
    )
    assert result.data["task_keys"] == ["DMS-2"]


def test_task_search_space_only_is_bounded_and_source_backed():
    runtime = _runtime()
    result = asyncio.run(runtime._task_search({"space": "DMS"}))

    assert result.data["count"] == 3
    assert result.data["task_keys"] == ["DMS-1", "DMS-2", "DMS-3"]


def test_task_search_still_rejects_truly_unscoped_query():
    runtime = _runtime()
    try:
        asyncio.run(runtime._task_search({}))
    except Exception as exc:
        assert "исполнитель, спринт или подтверждённое продуктовое пространство" in str(exc)
    else:
        raise AssertionError("unscoped task.search must fail closed")
