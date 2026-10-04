from __future__ import annotations

import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.domain.models import StatusCategory, Task, TaskStatus
from po_agent.harness.v4_plugin_registry import V4PluginRegistry
from po_agent.harness.v4_plugins._task_live_handlers import (
    _parse_human_created_period,
    build_task_search_created,
)
from po_agent.harness.v4_plugins.task_catalog import BINDINGS


MOSCOW = ZoneInfo("Europe/Moscow")


def _task(
    key: str,
    created_at: datetime,
    *,
    source_created: bool = True,
    status: TaskStatus = TaskStatus.OPEN,
) -> Task:
    is_progress = status == TaskStatus.IN_PROGRESS
    is_completed = status in {TaskStatus.CLOSED, TaskStatus.CANCELLED, TaskStatus.RESOLVED}
    return Task(
        key=key,
        id=key,
        title=key,
        status=status,
        status_category=(
            StatusCategory.COMPLETED if is_completed
            else StatusCategory.ACTIVE_WORK if is_progress
            else StatusCategory.BACKLOG
        ),
        status_raw=(
            "In progress" if is_progress
            else "Closed" if is_completed
            else "Open"
        ),
        status_type=(
            "progress" if is_progress
            else "done" if is_completed
            else "new"
        ),
        assignee="Калачанов Виктор Вячеславович",
        assignee_id="Kalachanov.V.V",
        assignee_login="kalachanov.v.v",
        created_at=created_at,
        updated_at=created_at,
        project_space="STS",
        source="swtr",
        source_data={
            "_canonical_created_at_from_source": source_created,
            "swtr_space": "STS",
        },
    )


class Runtime:
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.resolve_calls = []
        self.adapter = self

    async def _member_resolve(self, args):
        self.resolve_calls.append(dict(args))

        class Result:
            data = {
                "external_id": "Kalachanov.V.V",
                "member_login": "Kalachanov.V.V",
            }

        return Result()

    async def _get_resilient(self, path, *, params):
        assert path == "/api/v1/swtr-read/task-query"
        assert params["space"] == "STS"
        assert params["assignee"] == "Kalachanov.V.V"

        class Response:
            def __init__(self, tasks):
                self._tasks = tasks

            def json(self):
                return {
                    "tasks": [
                        {
                            "source_id": task.key,
                            "title": task.title,
                            "status": task.status_raw,
                            "created_at": task.created_at.isoformat(),
                            "source": "REAL_AS21",
                            "source_data": task.source_data,
                        }
                        for task in self._tasks
                    ],
                    "source_complete": True,
                    "completed_spaces": ["STS"],
                    "incomplete_spaces": [],
                }

        return Response(self.tasks)

    @staticmethod
    def _map(row):
        created = datetime.fromisoformat(row["created_at"])
        raw_status = str(row.get("status") or "").casefold()
        status = (
            TaskStatus.IN_PROGRESS if "progress" in raw_status
            else TaskStatus.CLOSED if "closed" in raw_status
            else TaskStatus.OPEN
        )
        return _task(
            row["source_id"],
            created,
            source_created=bool(row["source_data"].get("_canonical_created_at_from_source")),
            status=status,
        )

    @staticmethod
    def _safe_status(raw: str) -> str:
        value = str(raw or "").strip().casefold()
        if value in {"open", "active", "открытые", "незавершенные", "незавершённые"}:
            return "not_completed"
        if value in {"completed", "done", "closed", "закрытые", "завершенные", "завершённые"}:
            return "completed"
        return str(raw or "").strip()


def test_created_period_parses_explicit_inclusive_dates() -> None:
    start, end, kind = _parse_human_created_period(
        "с 29.09.2026 по 01.10.2026",
        now=datetime(2026, 10, 1, 12, 0, tzinfo=MOSCOW),
    )
    assert start == datetime(2026, 9, 29, 0, 0, tzinfo=MOSCOW)
    assert end.date().isoformat() == "2026-10-01"
    assert kind == "explicit_inclusive_dates"


def test_created_period_parses_last_two_calendar_days() -> None:
    start, end, kind = _parse_human_created_period(
        "последние 2 дня",
        now=datetime(2026, 10, 1, 14, 0, tzinfo=MOSCOW),
    )
    assert start == datetime(2026, 9, 30, 0, 0, tzinfo=MOSCOW)
    assert end == datetime(2026, 10, 1, 14, 0, tzinfo=MOSCOW)
    assert kind == "last_2_calendar_days"


def test_created_period_search_filters_only_source_created_timestamps() -> None:
    runtime = Runtime([
        _task("STS-1", datetime(2026, 9, 28, 10, 0, tzinfo=MOSCOW)),
        _task("STS-2", datetime(2026, 9, 29, 10, 0, tzinfo=MOSCOW)),
        _task("STS-3", datetime(2026, 10, 1, 10, 0, tzinfo=MOSCOW)),
    ])

    result = asyncio.run(
        build_task_search_created(runtime)(
            {
                "reference": "Калачанов",
                "space": "STS",
                "created_period": "с 29.09.2026 по 01.10.2026",
            }
        )
    )

    assert result.data["task_keys"] == ["STS-2", "STS-3"]
    assert result.data["count"] == 2
    assert result.data["source"] == "REAL_AS21"


def test_created_period_search_fails_closed_if_created_at_is_not_source_backed() -> None:
    runtime = Runtime([
        _task(
            "STS-1",
            datetime(2026, 10, 1, 10, 0, tzinfo=MOSCOW),
            source_created=False,
        ),
    ])

    with pytest.raises(AS21SourceUnavailable):
        asyncio.run(
            build_task_search_created(runtime)(
                {
                    "reference": "Калачанов",
                    "space": "STS",
                    "created_period": "с 29.09.2026 по 01.10.2026",
                }
            )
        )


def test_created_period_search_preserves_open_status_constraint() -> None:
    runtime = Runtime([
        _task("STS-1", datetime(2026, 10, 1, 10, 0, tzinfo=MOSCOW), status=TaskStatus.OPEN),
        _task("STS-2", datetime(2026, 10, 1, 11, 0, tzinfo=MOSCOW), status=TaskStatus.IN_PROGRESS),
        _task("STS-3", datetime(2026, 10, 1, 12, 0, tzinfo=MOSCOW), status=TaskStatus.CLOSED),
        _task("STS-4", datetime(2026, 9, 28, 10, 0, tzinfo=MOSCOW), status=TaskStatus.OPEN),
    ])

    result = asyncio.run(
        build_task_search_created(runtime)(
            {
                "reference": "Калачанов",
                "space": "STS",
                "created_period": "с 29.09.2026 по 01.10.2026",
                "status": "открытые",
            }
        )
    )

    assert result.data["task_keys"] == ["STS-1", "STS-2"]
    assert result.data["count"] == 2
    assert result.data["status"] == "открытые"
    assert all(task["status"] != TaskStatus.CLOSED.value for task in result.data["tasks"])


def test_created_period_search_preserves_in_progress_status_constraint() -> None:
    runtime = Runtime([
        _task("STS-1", datetime(2026, 10, 1, 10, 0, tzinfo=MOSCOW), status=TaskStatus.OPEN),
        _task("STS-2", datetime(2026, 10, 1, 11, 0, tzinfo=MOSCOW), status=TaskStatus.IN_PROGRESS),
    ])

    result = asyncio.run(
        build_task_search_created(runtime)(
            {
                "reference": "Калачанов",
                "space": "STS",
                "created_period": "с 29.09.2026 по 01.10.2026",
                "status": "В работе",
            }
        )
    )

    assert result.data["task_keys"] == ["STS-2"]
    assert result.data["count"] == 1


def test_created_in_progress_binding_fixes_status_at_plugin_seam() -> None:
    binding = next(
        item for item in BINDINGS
        if item.capability_id == "task.search_created_in_progress"
    )
    assert dict(binding.fixed_arguments) == {"status": "in_progress"}


def test_created_in_progress_fixed_binding_overrides_planner_status() -> None:
    runtime = Runtime([
        _task("STS-1", datetime(2026, 10, 1, 10, 0, tzinfo=MOSCOW), status=TaskStatus.OPEN),
        _task("STS-2", datetime(2026, 10, 1, 11, 0, tzinfo=MOSCOW), status=TaskStatus.IN_PROGRESS),
        _task("STS-3", datetime(2026, 10, 1, 12, 0, tzinfo=MOSCOW), status=TaskStatus.CLOSED),
    ])

    handler = V4PluginRegistry._apply_fixed_arguments(
        build_task_search_created(runtime),
        {"status": "in_progress"},
    )
    result = asyncio.run(
        handler(
            {
                "reference": "Калачанов",
                "space": "STS",
                "created_period": "с 29.09.2026 по 01.10.2026",
                # Deliberately conflicting planner value: plugin contract wins.
                "status": "completed",
            }
        )
    )

    assert result.data["task_keys"] == ["STS-2"]
    assert result.data["count"] == 1
    assert result.data["status"] == "in_progress"
