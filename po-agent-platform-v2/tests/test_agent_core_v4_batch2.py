from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch2 import (
    build_sprint_scope_change,
    build_team_blocked,
    build_team_capacity,
    build_team_wip,
    build_team_workload,
)


def _task(
    key: str,
    *,
    assignee: str | None,
    completed: bool = False,
    blocked: bool = False,
    status_type: str = "progress",
    status_category: str = "active_work",
    estimate_hours: float | None = None,
):
    return SimpleNamespace(
        key=key,
        title=key,
        assignee=assignee,
        assignee_login=assignee,
        assignee_id=assignee,
        is_completed=completed,
        is_open=not completed,
        is_blocked=blocked,
        status_type=status_type,
        status_category=SimpleNamespace(value=status_category),
        status_raw="Closed" if completed else ("Blocked" if blocked else "In progress"),
        status=SimpleNamespace(value="Closed" if completed else "In progress"),
        estimate_hours=estimate_hours,
    )


class FakeAdapter:
    def __init__(self):
        self.calls = []
        self.tasks = [
            _task("DMS-1", assignee="alice", estimate_hours=8),
            _task("DMS-2", assignee="alice", blocked=True, estimate_hours=4),
            _task("DMS-3", assignee="bob", status_type="open", status_category="backlog", estimate_hours=3),
            _task("DMS-4", assignee="bob", completed=True, estimate_hours=5),
            _task("DMS-5", assignee=None, estimate_hours=None),
        ]

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


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_batch2_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.batch2.team_current_sprint" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "sprint.scope_change",
        "team.workload",
        "team.wip",
        "team.blocked",
        "team.capacity",
    } <= ids


def test_team_workload_is_current_sprint_scoped_and_task_count_based():
    adapter = FakeAdapter()
    result = asyncio.run(build_team_workload(_runtime(adapter))({"space": "DMS"}))

    assert adapter.calls == [("current", "DMS"), ("sprint", "DMS-SPRNT-3", "DMS")]
    assert result.data["scope"] == "current_sprint"
    assert result.data["active_tasks"] == 4
    assert result.data["completed_tasks"] == 1
    assert result.data["unassigned_active_tasks"] == 1
    rows = {row["member"]: row for row in result.data["workload"]}
    assert rows["alice"]["active_tasks"] == 2
    assert rows["alice"]["wip"] == 2
    assert rows["alice"]["blocked"] == 1
    assert rows["bob"]["wip"] == 0
    assert "task_count_workload_not_capacity" in result.warnings


def test_team_wip_and_blocked_use_current_sprint_predicates():
    runtime = _runtime()

    wip = asyncio.run(build_team_wip(runtime)({"space": "DMS"}))
    assert wip.data["task_keys"] == ["DMS-1", "DMS-2", "DMS-5"]
    assert wip.data["total_wip"] == 3

    blocked = asyncio.run(build_team_blocked(runtime)({"space": "DMS"}))
    assert blocked.data["task_keys"] == ["DMS-2"]
    assert blocked.data["total_blocked"] == 1


def test_team_capacity_fails_on_source_estimates_before_using_any_baseline():
    adapter = FakeAdapter()
    adapter.tasks.append(_task("DMS-6", assignee="alice", estimate_hours=None))
    runtime = _runtime(adapter)

    with pytest.raises(V4CapabilityUnavailable, match="do not expose source-backed estimates"):
        asyncio.run(build_team_capacity(runtime)({"space": "DMS"}))

    with pytest.raises(V4CapabilityUnavailable, match="explicit capacity baseline alone is insufficient"):
        asyncio.run(build_team_capacity(runtime)({"space": "DMS", "capacity_hours": "40"}))


def test_team_capacity_uses_owner_policy_default_when_estimates_are_complete():
    adapter = FakeAdapter()
    adapter.tasks = [task for task in adapter.tasks if task.assignee is not None]
    runtime = _runtime(adapter)

    result = asyncio.run(build_team_capacity(runtime)({"space": "DMS"}))
    rows = {row["member"]: row for row in result.data["members"]}

    assert result.data["capacity_source"] == "owner_policy_default"
    assert result.data["capacity_hours_per_member"] == 65.94
    assert result.data["capacity_policy"]["working_days_2026"] == 247
    assert result.data["capacity_policy"]["calendar_days"] == 14
    assert result.data["capacity_policy"]["normalization"] == "2026_annual_average_workday_density"
    assert result.data["capacity_policy"]["availability_factor"] == 0.87
    assert result.data["capacity_policy"]["weekly_hours"] == 40.0
    assert rows["alice"]["estimated_hours"] == 12.0
    assert rows["alice"]["utilization_percent"] == 18.2


def test_team_capacity_explicit_baseline_overrides_owner_policy():
    adapter = FakeAdapter()
    adapter.tasks = [task for task in adapter.tasks if task.assignee is not None]
    runtime = _runtime(adapter)

    result = asyncio.run(build_team_capacity(runtime)({"space": "DMS", "capacity_hours": "40"}))
    rows = {row["member"]: row for row in result.data["members"]}

    assert result.data["capacity_source"] == "explicit_user_baseline"
    assert result.data["capacity_policy"] is None
    assert rows["alice"]["estimated_hours"] == 12.0
    assert rows["alice"]["utilization_percent"] == 30.0
    assert rows["bob"]["estimated_hours"] == 3.0
    assert rows["bob"]["utilization_percent"] == 7.5


def test_scope_change_validates_sprint_then_fails_closed_without_baseline():
    adapter = FakeAdapter()
    runtime = _runtime(adapter)

    with pytest.raises(V4CapabilityUnavailable, match="sprint-start commitment baseline"):
        asyncio.run(
            build_sprint_scope_change(runtime)({"sprint_id": "DMS-SPRNT-3", "space": "DMS"})
        )

    assert adapter.calls == [("sprint", "DMS-SPRNT-3", "DMS")]
