from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.time_accounting_member import (
    build_member_time_spent,
    build_member_utilization_actual,
    build_member_worklogs,
)


def _task(key: str):
    return SimpleNamespace(key=key)


class FakeAdapter:
    def __init__(self):
        self.tasks = [_task("DMS-1"), _task("DMS-2")]
        self.worklogs = {
            "DMS-1": [
                {
                    "id": "w1",
                    "date": "2026-09-14",
                    "user": {"external_id": "Semavin.M.M"},
                    "type": {"code": 44, "name": "Тестирование"},
                    "duration_hours": 8.0,
                    "comment": None,
                },
                {
                    "id": "w2",
                    "date": "2026-09-15",
                    "user": {"external_id": "Other.User"},
                    "type": {"code": 61, "name": "Кодирование"},
                    "duration_hours": 4.0,
                    "comment": None,
                },
            ],
            "DMS-2": [
                {
                    "id": "w3",
                    "date": "2026-09-20",
                    "user": {"external_id": "Semavin.M.M"},
                    "type": {"code": 61, "name": "Кодирование"},
                    "duration_hours": 6.0,
                    "comment": "done",
                },
                {
                    "id": "w4",
                    "date": "2026-09-30",
                    "user": {"external_id": "Semavin.M.M"},
                    "type": {"code": 61, "name": "Кодирование"},
                    "duration_hours": 10.0,
                    "comment": None,
                },
            ],
        }

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        return list(self.tasks)

    async def list_sprints(self, space: str):
        return [{
            "code": "DMS-SPRNT-3",
            "start_at": "2026-09-13T00:00:00+03:00",
            "finish_at": "2026-09-27T23:59:59+03:00",
        }]

    async def get_task_worklogs(self, task_key: str):
        entries = list(self.worklogs.get(task_key, []))
        return {"complete": True, "entries": entries}


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_member_time_accounting_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.time_accounting.member" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "member.time_spent",
        "member.worklogs",
        "member.utilization_actual",
    } <= ids


def test_member_time_spent_filters_by_worklog_author_and_sprint_period():
    result = asyncio.run(
        build_member_time_spent(_runtime())({
            "member_login": "Semavin.M.M",
            "space": "DMS",
            "sprint_id": "DMS-SPRNT-3",
        })
    )

    assert result.data["total_hours"] == 14.0
    assert result.data["worklog_count"] == 2
    assert result.data["attribution"] == "worklog_author_external_id"
    assert result.data["by_task"] == [
        {"task_key": "DMS-1", "hours": 8.0},
        {"task_key": "DMS-2", "hours": 6.0},
    ]


def test_member_worklogs_returns_exact_member_entries_only():
    result = asyncio.run(
        build_member_worklogs(_runtime())({
            "member_login": "Semavin.M.M",
            "space": "DMS",
            "sprint_id": "DMS-SPRNT-3",
        })
    )

    assert result.data["worklog_count"] == 2
    assert result.data["total_hours"] == 14.0
    assert [row["id"] for row in result.data["worklogs"]] == ["w1", "w3"]
    assert [row["task_key"] for row in result.data["worklogs"]] == ["DMS-1", "DMS-2"]


def test_member_actual_utilization_uses_period_normalized_owner_policy():
    result = asyncio.run(
        build_member_utilization_actual(_runtime())({
            "member_login": "Semavin.M.M",
            "space": "DMS",
            "sprint_id": "DMS-SPRNT-3",
        })
    )

    assert result.data["calendar_days"] == 15
    assert result.data["available_capacity_hours"] == 70.65
    assert result.data["actual_hours"] == 14.0
    assert result.data["utilization_percent"] == 19.8
    assert result.data["numerator_source"] == "REAL_AS21_WORKLOGS"
    assert result.data["denominator_source"] == "OWNER_POLICY"


def test_member_zero_worklogs_is_legitimate_completion_shape():
    adapter = FakeAdapter()
    adapter.worklogs = {"DMS-1": [], "DMS-2": []}
    result = asyncio.run(
        build_member_time_spent(_runtime(adapter))({
            "member_login": "Semavin.M.M",
            "space": "DMS",
            "sprint_id": "DMS-SPRNT-3",
        })
    )
    assert result.data["total_hours"] == 0.0
    assert result.data["worklog_count"] == 0
    assert result.data["by_task"] == []


def test_member_completion_contracts_are_zero_safe_and_cover_context():
    registry = discover_v4_plugins()
    skills = {skill.id: skill for skill in registry.skills()}
    for skill_id in ("member.time_spent", "member.worklogs"):
        req = skills[skill_id].completion[0]
        assert "worklog_count" in req.data_keys
        assert req.covers_resolved_constraints is True
    req = skills["member.utilization_actual"].completion[0]
    assert req.data_keys == ("member_login", "sprint_id", "worklog_count", "capacity_policy")
    assert req.covers_resolved_constraints is True
