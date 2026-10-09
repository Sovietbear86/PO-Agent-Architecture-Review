from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.v4_plugins._task_live_handlers import (
    build_task_hierarchy,
    build_task_type_analysis,
)


def _task(
    key: str,
    *,
    task_type_code: str,
    task_type_name: str,
    status: TaskStatus = TaskStatus.OPEN,
    created_at: datetime | None = None,
) -> Task:
    return Task(
        key=key,
        id=key,
        title=key,
        description="",
        status=status,
        status_raw=status.value,
        status_type="done" if status == TaskStatus.CLOSED else "progress" if status == TaskStatus.IN_PROGRESS else "open",
        status_category=(
            StatusCategory.COMPLETED
            if status == TaskStatus.CLOSED
            else StatusCategory.ACTIVE_WORK
            if status == TaskStatus.IN_PROGRESS
            else StatusCategory.BACKLOG
        ),
        assignee="Иванов Иван",
        assignee_id="Ivanov.I.I",
        assignee_login="ivanov.i.i",
        created_at=created_at or datetime(2026, 10, 1, tzinfo=timezone.utc),
        updated_at=created_at or datetime(2026, 10, 1, tzinfo=timezone.utc),
        project_space="DMS",
        task_type_code=task_type_code,
        task_type_name=task_type_name,
        source="swtr",
        source_data={
            "swtr_space": "DMS",
            "swtr_suit": {"code": task_type_code, "name": task_type_name},
            "_canonical_created_at_from_source": True,
        },
    )


class Runtime:
    def __init__(self, tasks, relations=None):
        self.tasks = list(tasks)
        self.adapter = self
        self.relations = relations or {}

    async def _member_resolve(self, args):
        class Result:
            data = {"external_id": "Ivanov.I.I", "member_login": "Ivanov.I.I"}
        return Result()

    async def _get_resilient(self, path, *, params):
        class Response:
            def __init__(self, payload):
                self.payload = payload

            def json(self):
                return self.payload

        rows = [
            {
                "source_id": task.key,
                "title": task.title,
                "description": task.description,
                "status": task.status_raw,
                "task_type_code": task.task_type_code,
                "task_type_name": task.task_type_name,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "source": "REAL_AS21",
                "source_data": task.source_data,
            }
            for task in self.tasks
        ]

        if "/sprints/" in path and path.endswith("/tasks"):
            assert params.get("complete") is True
            assert params.get("include_task_type") is True
            return Response({
                "complete": True,
                "membership_proven": True,
                "complete_tasks": rows,
                "source_path": "test_live_sprint",
            })

        assert path.endswith(("task-query", "assignee-tasks"))
        tasks = self.tasks
        if params.get("assignee"):
            tasks = [task for task in tasks if task.assignee_id == params["assignee"]]
        rows = [
            {
                "source_id": task.key,
                "title": task.title,
                "description": task.description,
                "status": task.status_raw,
                "task_type_code": task.task_type_code,
                "task_type_name": task.task_type_name,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "source": "REAL_AS21",
                "source_data": task.source_data,
            }
            for task in tasks
        ]
        return Response({
            "tasks": rows,
            "source_complete": True,
            "completed_spaces": ["DMS"],
            "incomplete_spaces": [],
        })

    @staticmethod
    def _map(row):
        status = TaskStatus.CLOSED if str(row["status"]).casefold() == "closed" else TaskStatus.OPEN
        created_raw = row.get("created_at")
        created = datetime.fromisoformat(created_raw) if created_raw else None
        return _task(
            row["source_id"],
            task_type_code=row.get("task_type_code") or "",
            task_type_name=row.get("task_type_name") or "",
            status=status,
            created_at=created,
        )

    @staticmethod
    def _safe_status(raw):
        value = str(raw or "").casefold()
        if value in {"open", "открытые", "not_completed"}:
            return "not_completed"
        if value in {"closed", "completed", "закрытые"}:
            return "completed"
        return value

    async def get_task_relations(self, key):
        return dict(self.relations[key])

    async def get_sprint_tasks(self, sprint_id, space=None):
        return list(self.tasks)


def test_task_type_analysis_composes_person_space_status_and_type():
    runtime = Runtime([
        _task("DMS-1", task_type_code="defect", task_type_name="Defect"),
        _task("DMS-2", task_type_code="story", task_type_name="Story"),
        _task("DMS-3", task_type_code="defect", task_type_name="Defect", status=TaskStatus.CLOSED),
    ])

    result = asyncio.run(build_task_type_analysis(runtime)({
        "reference": "Иванов",
        "space": "DMS",
        "status": "open",
        "task_type": "defect",
    }))

    assert result.data["task_keys"] == ["DMS-1"]
    assert result.data["count"] == 1
    assert result.data["scope_count"] == 2
    assert any(row["code"] == "defect" and row["count"] == 1 for row in result.data["type_breakdown"])


def test_task_type_analysis_composes_person_sprint_status_and_type():
    runtime = Runtime([
        _task("DMS-431", task_type_code="bug", task_type_name="Дефект"),
        _task("DMS-432", task_type_code="task", task_type_name="Задача"),
        _task("DMS-433", task_type_code="bug", task_type_name="Дефект", status=TaskStatus.CLOSED),
    ])

    result = asyncio.run(build_task_type_analysis(runtime)({
        "reference": "Иванов",
        "space": "DMS",
        "sprint_id": "DMS-SPRNT-9",
        "status": "open",
        "task_type": "defect",
    }))

    assert result.data["task_keys"] == ["DMS-431"]
    assert result.data["count"] == 1
    assert result.data["scope_count"] == 2
    assert result.data["sprint_id"] == "DMS-SPRNT-9"
    assert result.data["source"] == "REAL_AS21"


def test_task_type_analysis_composes_person_space_status_type_and_open_ended_period():
    runtime = Runtime([
        _task(
            "DMS-10",
            task_type_code="defect",
            task_type_name="Дефект",
            created_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        ),
        _task(
            "DMS-11",
            task_type_code="defect",
            task_type_name="Дефект",
            created_at=datetime(2026, 9, 20, tzinfo=timezone.utc),
        ),
        _task(
            "DMS-12",
            task_type_code="story",
            task_type_name="История",
            created_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        ),
        _task(
            "DMS-13",
            task_type_code="defect",
            task_type_name="Дефект",
            status=TaskStatus.CLOSED,
            created_at=datetime(2026, 10, 2, tzinfo=timezone.utc),
        ),
    ])

    result = asyncio.run(build_task_type_analysis(runtime)({
        "reference": "Иванов",
        "space": "DMS",
        "status": "open",
        "task_type": "defect",
        "created_period": "с 30.09.2026 по сегодняшний день",
    }))

    assert result.data["task_keys"] == ["DMS-10"]
    assert result.data["count"] == 1
    assert result.data["task_type"] == "defect"
    assert result.data["status"] == "open"
    assert result.data["period_kind"] == "explicit_start_to_now"
    assert result.data["created_period"] == "с 30.09.2026 по сегодняшний день"


def test_task_type_analysis_without_type_returns_distribution():
    runtime = Runtime([
        _task("DMS-1", task_type_code="defect", task_type_name="Defect"),
        _task("DMS-2", task_type_code="story", task_type_name="Story"),
        _task("DMS-3", task_type_code="defect", task_type_name="Defect"),
    ])

    result = asyncio.run(build_task_type_analysis(runtime)({"space": "DMS"}))

    breakdown = {row["code"]: row["count"] for row in result.data["type_breakdown"]}
    assert breakdown == {"defect": 2, "story": 1}
    assert result.data["count"] == 3


def test_task_hierarchy_follows_source_parents_and_detects_epic_type_without_assuming_depth_10():
    runtime = Runtime(
        [_task("DMS-3", task_type_code="story", task_type_name="Story")],
        relations={
            "DMS-3": {
                "schema_proven": True,
                "task_type_code": "story",
                "task_type_name": "Story",
                "parent_key": "DMS-2",
                "parent_ambiguous": False,
                "epic_key": None,
                "epic_ambiguous": False,
                "related_keys": ["DMS-4"],
                "source_fields_seen": ["attribute:parent", "unit:links"],
            },
            "DMS-2": {
                "schema_proven": True,
                "task_type_code": "story",
                "task_type_name": "Story",
                "parent_key": "DMS-1",
                "parent_ambiguous": False,
                "epic_key": None,
                "epic_ambiguous": False,
                "related_keys": [],
                "source_fields_seen": ["attribute:parent"],
            },
            "DMS-1": {
                "schema_proven": True,
                "task_type_code": "epic",
                "task_type_name": "Epic",
                "parent_key": None,
                "parent_ambiguous": False,
                "epic_key": None,
                "epic_ambiguous": False,
                "related_keys": [],
                "source_fields_seen": ["attribute:parent"],
            },
        },
    )

    result = asyncio.run(build_task_hierarchy(runtime)({"task_key": "DMS-3", "mode": "inspect"}))

    assert result.data["depth"] == 2
    assert [row["key"] for row in result.data["parent_chain"]] == ["DMS-2", "DMS-1"]
    assert result.data["epic_key"] == "DMS-1"
    assert result.data["related_keys"] == ["DMS-4"]
    assert result.data["max_depth_assumption"] is None
    assert result.data["safety_traversal_cap"] == 20


def test_task_hierarchy_fails_closed_on_source_cycle():
    runtime = Runtime(
        [_task("DMS-3", task_type_code="story", task_type_name="Story")],
        relations={
            "DMS-3": {
                "schema_proven": True,
                "task_type_code": "story",
                "task_type_name": "Story",
                "parent_key": "DMS-2",
                "parent_ambiguous": False,
                "epic_key": None,
                "epic_ambiguous": False,
                "related_keys": [],
                "source_fields_seen": ["attribute:parent"],
            },
            "DMS-2": {
                "schema_proven": True,
                "task_type_code": "story",
                "task_type_name": "Story",
                "parent_key": "DMS-3",
                "parent_ambiguous": False,
                "epic_key": None,
                "epic_ambiguous": False,
                "related_keys": [],
                "source_fields_seen": ["attribute:parent"],
            },
        },
    )

    with pytest.raises(AS21SourceUnavailable):
        asyncio.run(build_task_hierarchy(runtime)({"task_key": "DMS-3", "mode": "inspect"}))
