from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.time_accounting import (
    build_task_time_spent,
    build_task_worklogs,
)


class FakeAdapter:
    def __init__(self, *, complete: bool = True, total: float = 48.0, entry_total: float = 48.0):
        self.complete = complete
        self.total = total
        self.entry_total = entry_total
        self.calls = []

    async def get_task_worklogs(self, task_key: str):
        self.calls.append(task_key)
        return {
            "task_code": task_key,
            "source": "REAL_AS21",
            "total_hours": self.total,
            "entry_total_hours": self.entry_total,
            "complete": self.complete,
            "convention": {"worklog_day_hours": 8, "worklog_week_days": 5},
            "entries": [
                {
                    "id": "w1",
                    "date": "2026-09-01",
                    "user": {"external_id": "Semavin.M.M", "first_name": "Михаил", "last_name": "Семавин", "middle_name": "Михайлович"},
                    "type": {"code": 44, "name": "4Р_Тестирование компонента"},
                    "duration_hours": 8.0,
                    "comment": None,
                },
                {
                    "id": "w2",
                    "date": "2026-09-02",
                    "user": {"external_id": "Semavin.M.M", "first_name": "Михаил", "last_name": "Семавин", "middle_name": "Михайлович"},
                    "type": {"code": 44, "name": "4Р_Тестирование компонента"},
                    "duration_hours": 8.0,
                    "comment": None,
                },
                {
                    "id": "w3",
                    "date": "2026-09-04",
                    "user": {"external_id": "Garanin.R.V", "first_name": "Родион", "last_name": "Гаранин", "middle_name": "Владимирович"},
                    "type": {"code": 61, "name": "2Р_Кодирование"},
                    "duration_hours": 32.0,
                    "comment": None,
                },
            ],
        }


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_time_accounting_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.time_accounting.task" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {"task.time_spent", "task.worklogs"} <= ids


def test_task_time_spent_returns_authoritative_total():
    adapter = FakeAdapter()
    result = asyncio.run(build_task_time_spent(_runtime(adapter))({"task_key": "DMS-380"}))

    assert adapter.calls == ["DMS-380"]
    assert result.data["time_spent_hours"] == 48.0
    assert result.data["worklog_count"] == 3
    assert result.data["complete"] is True


def test_task_time_spent_fails_closed_on_incomplete_collection():
    adapter = FakeAdapter(complete=False)
    with pytest.raises(V4CapabilityUnavailable, match="complete bounded worklog collection"):
        asyncio.run(build_task_time_spent(_runtime(adapter))({"task_key": "DMS-380"}))


def test_task_time_spent_fails_closed_when_aggregate_mismatches_entries():
    adapter = FakeAdapter(total=48.0, entry_total=40.0)
    with pytest.raises(V4CapabilityUnavailable, match="does not match"):
        asyncio.run(build_task_time_spent(_runtime(adapter))({"task_key": "DMS-380"}))


def test_task_worklogs_preserve_user_date_type_and_duration():
    result = asyncio.run(build_task_worklogs(_runtime())({"task_key": "DMS-380"}))
    rows = result.data["worklogs"]

    assert result.data["count"] == 3
    assert result.data["time_spent_hours"] == 48.0
    assert rows[0]["date"] == "2026-09-01"
    assert rows[0]["user_external_id"] == "Semavin.M.M"
    assert rows[0]["work_type_name"] == "4Р_Тестирование компонента"
    assert rows[0]["duration_hours"] == 8.0
