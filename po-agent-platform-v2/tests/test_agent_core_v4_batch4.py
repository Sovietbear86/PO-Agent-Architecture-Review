from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.domain.models import TaskPriority
from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch4 import (
    build_portfolio_overview,
    build_release_blockers,
    build_release_dependencies,
    build_release_progress,
    build_release_risk_queue,
)


def _task(
    key: str,
    *,
    completed: bool = False,
    blocked: bool = False,
    assignee: str | None = "alice",
    priority: TaskPriority | None = None,
    estimate_hours: float | None = None,
    depends_on=(),
    age_days: int = 1,
    status_type: str = "progress",
    status_category: str = "active_work",
):
    return SimpleNamespace(
        key=key,
        title=key,
        is_completed=completed,
        is_open=not completed,
        is_blocked=blocked,
        assignee=assignee,
        assignee_login=assignee,
        assignee_id=assignee,
        priority=priority,
        estimate_hours=estimate_hours,
        depends_on=tuple(depends_on),
        age_days=age_days,
        status_raw="Closed" if completed else ("Need info" if blocked else "In progress"),
        status=SimpleNamespace(value="Closed" if completed else "In progress"),
        status_type=status_type,
        status_category=SimpleNamespace(value=status_category),
    )


class FakeAdapter:
    def __init__(self):
        self.release_tasks = []
        self.current = {
            "DMS": "DMS-SPRNT-3",
            "OLP": "OLP-SPRNT-8",
            "WMB": None,
            "STS": None,
            "CRPV": None,
        }
        self.sprints = {
            "DMS-SPRNT-3": [
                _task("DMS-1"),
                _task("DMS-2", blocked=True),
                _task("DMS-3", completed=True, status_type="done", status_category="completed"),
            ],
            "OLP-SPRNT-8": [
                _task("OLP-1"),
                _task("OLP-2", status_type="open", status_category="backlog"),
            ],
        }

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        return list(self.release_tasks)

    async def get_current_sprint_id(self, space: str):
        return self.current.get(space)

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        return list(self.sprints.get(sprint_id, []))


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_batch4_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.batch4.release_portfolio" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "release.progress",
        "release.blockers",
        "release.dependencies",
        "release.risk_queue",
        "portfolio.overview",
    } <= ids


def test_release_analytics_fail_closed_without_membership():
    runtime = _runtime()
    for builder in (
        build_release_progress,
        build_release_blockers,
        build_release_dependencies,
        build_release_risk_queue,
    ):
        with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
            asyncio.run(builder(runtime)({"space": "WMB", "release_id": "release-uuid"}))


def test_release_progress_does_not_zero_fill_missing_estimates():
    adapter = FakeAdapter()
    adapter.release_tasks = [
        _task("WMB-1", completed=True, estimate_hours=8),
        _task("WMB-2", completed=False, estimate_hours=None),
    ]
    result = asyncio.run(build_release_progress(_runtime(adapter))({"space": "WMB", "release_id": "r1"}))
    assert result.data["total"] == 2
    assert result.data["completed"] == 1
    assert result.data["task_completion_percent"] == 50.0
    assert result.data["estimate_coverage_percent"] == 50.0
    assert result.data["effort_progress"] is None
    assert "effort_progress_unavailable_incomplete_estimates" in result.warnings


def test_release_dependencies_and_risk_queue_are_deterministic():
    adapter = FakeAdapter()
    adapter.release_tasks = [
        _task(
            "WMB-1",
            blocked=True,
            assignee=None,
            priority=TaskPriority.CRITICAL,
            depends_on=("WMB-2", "EXT-1"),
            age_days=20,
        ),
        _task("WMB-2", priority=TaskPriority.HIGH),
    ]
    runtime = _runtime(adapter)

    deps = asyncio.run(build_release_dependencies(runtime)({"space": "WMB", "release_id": "r1"}))
    assert deps.data["internal"] == [{"task_key": "WMB-1", "depends_on": "WMB-2"}]
    assert deps.data["external"] == [{"task_key": "WMB-1", "depends_on": "EXT-1"}]

    risks = asyncio.run(build_release_risk_queue(runtime)({"space": "WMB", "release_id": "r1"}))
    assert risks.data["risk_queue"][0]["task"]["key"] == "WMB-1"
    assert risks.data["risk_queue"][0]["risk_score"] == 100
    assert risks.data["risk_queue"][0]["reasons"] == [
        "blocked", "high_priority", "unassigned", "aging_14d"
    ]


def test_portfolio_overview_uses_bounded_per_space_current_sprints():
    result = asyncio.run(build_portfolio_overview(_runtime())({}))

    rows = {row["space"]: row for row in result.data["spaces"]}
    assert result.data["space_count"] == 5
    assert result.data["source_backed_space_count"] == 2
    assert rows["DMS"]["sprint_id"] == "DMS-SPRNT-3"
    assert rows["DMS"]["total"] == 3
    assert rows["DMS"]["blocked"] == 1
    assert rows["OLP"]["total"] == 2
    assert rows["WMB"]["state"] == "NO_CURRENT_SPRINT"
    assert result.data["total_current_sprint_tasks"] == 5
    assert result.data["total_blocked"] == 1
