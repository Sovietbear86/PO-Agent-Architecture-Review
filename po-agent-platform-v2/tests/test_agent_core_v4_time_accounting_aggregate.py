from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.time_accounting_aggregate import (
    build_release_time_spent,
    build_sprint_time_spent,
    build_team_time_spent,
    build_team_utilization_actual,
)


def _task(key: str):
    return SimpleNamespace(key=key)


class FakeAdapter:
    def __init__(self):
        self.calls = []
        self.tasks = [_task("DMS-1"), _task("DMS-2")]
        self.worklogs = {
            "DMS-1": [
                {
                    "id": "w1", "date": "2026-09-02",
                    "user": {"external_id": "alice"},
                    "type": {"name": "Кодирование"},
                    "duration_hours": 8.0,
                },
                {
                    "id": "w2", "date": "2026-08-30",
                    "user": {"external_id": "alice"},
                    "type": {"name": "Кодирование"},
                    "duration_hours": 4.0,
                },
            ],
            "DMS-2": [
                {
                    "id": "w3", "date": "2026-09-03",
                    "user": {"external_id": "bob"},
                    "type": {"name": "Тестирование"},
                    "duration_hours": 6.0,
                }
            ],
        }
        self.release_tasks = []

    async def get_current_sprint_id(self, space: str):
        self.calls.append(("current", space))
        return "DMS-SPRNT-3"

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        self.calls.append(("sprint", sprint_id, space))
        return list(self.tasks)

    async def list_sprints(self, space: str):
        self.calls.append(("list_sprints", space))
        return [{
            "code": "DMS-SPRNT-3",
            "start_at": "2026-09-01T00:00:00+03:00",
            "finish_at": "2026-09-14T23:59:59+03:00",
            "deleted": False,
        }]

    async def get_task_worklogs(self, task_key: str):
        self.calls.append(("worklogs", task_key))
        entries = list(self.worklogs.get(task_key, []))
        return {
            "task_code": task_key,
            "complete": True,
            "entries": entries,
            "total_hours": sum(float(row["duration_hours"]) for row in entries),
        }

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        self.calls.append(("release", release_id, space))
        return list(self.release_tasks)


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_aggregate_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.time_accounting.aggregate" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "sprint.time_spent",
        "team.time_spent",
        "team.utilization_actual",
        "release.time_spent",
    } <= ids


def test_sprint_time_spent_filters_worklogs_to_sprint_period():
    result = asyncio.run(
        build_sprint_time_spent(_runtime())(
            {"space": "DMS", "sprint_id": "DMS-SPRNT-3"}
        )
    )
    assert result.data["total_hours"] == 14.0
    assert result.data["worklog_count"] == 2
    assert result.data["period_start"] == "2026-09-01"
    assert result.data["period_finish"] == "2026-09-14"
    by_member = {row["member"]: row["hours"] for row in result.data["by_member"]}
    assert by_member == {"alice": 8.0, "bob": 6.0}


def test_team_time_spent_uses_authoritative_current_sprint():
    adapter = FakeAdapter()
    result = asyncio.run(build_team_time_spent(_runtime(adapter))({"space": "DMS"}))
    assert result.data["sprint_id"] == "DMS-SPRNT-3"
    assert result.data["total_hours"] == 14.0
    assert adapter.calls[0] == ("current", "DMS")


def test_actual_utilization_scales_owner_policy_to_sprint_period():
    result = asyncio.run(build_team_utilization_actual(_runtime())({"space": "DMS"}))
    assert result.data["calendar_days"] == 14
    # 247 * 8 * .87 / 365 * 14 = 65.94h after policy rounding.
    assert result.data["capacity_hours_per_member"] == 65.94
    rows = {row["member"]: row for row in result.data["members"]}
    assert rows["alice"]["actual_hours"] == 8.0
    assert rows["alice"]["utilization_percent"] == 12.1
    assert rows["bob"]["actual_hours"] == 6.0
    assert rows["bob"]["utilization_percent"] == 9.1
    assert result.data["numerator_source"] == "REAL_AS21_WORKLOGS"
    assert result.data["denominator_source"] == "OWNER_POLICY"


def test_release_time_spent_fails_closed_without_release_membership():
    with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
        asyncio.run(
            build_release_time_spent(_runtime())(
                {"space": "WMB", "release_id": "release-uuid"}
            )
        )
