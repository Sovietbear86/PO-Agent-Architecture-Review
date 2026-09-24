from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch3 import (
    build_release_scope,
    build_team_assignee_recommendation,
    build_team_bottlenecks,
    build_team_competency_match,
    build_team_distribution,
)


def _task(
    key: str,
    *,
    assignee: str | None,
    completed: bool = False,
    blocked: bool = False,
    status_raw: str = "In progress",
    status_type: str = "progress",
    status_category: str = "active_work",
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
        status_raw=status_raw,
        status=SimpleNamespace(value=status_raw),
    )


class FakeAdapter:
    def __init__(self):
        self.calls = []
        self.current = "DMS-SPRNT-3"
        self.tasks = [
            _task("DMS-1", assignee="alice"),
            _task("DMS-2", assignee="alice", blocked=True, status_raw="Need info"),
            _task("DMS-3", assignee="alice", status_raw="Open", status_type="open", status_category="backlog"),
            _task("DMS-4", assignee="bob"),
            _task("DMS-5", assignee="bob", completed=True, status_raw="Closed", status_type="done", status_category="completed"),
            _task("DMS-6", assignee=None),
        ]
        self.release_tasks = []

    async def get_current_sprint_id(self, space: str):
        self.calls.append(("current", space))
        return self.current

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        self.calls.append(("sprint", sprint_id, space))
        return list(self.tasks)

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        self.calls.append(("release", release_id, space))
        return list(self.release_tasks)


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_batch3_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.batch3.team_release" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert {
        "team.competency_match",
        "team.assignee_recommendation",
        "team.bottlenecks",
        "team.distribution",
        "release.scope",
    } <= ids


def test_competency_and_assignee_recommendation_fail_closed_without_source():
    runtime = _runtime()

    with pytest.raises(V4CapabilityUnavailable, match="competency/skill source"):
        asyncio.run(build_team_competency_match(runtime)({"space": "DMS"}))

    with pytest.raises(V4CapabilityUnavailable, match="competencies and availability"):
        asyncio.run(build_team_assignee_recommendation(runtime)({"space": "DMS"}))


def test_team_bottlenecks_is_current_sprint_scoped_and_descriptive():
    adapter = FakeAdapter()
    result = asyncio.run(build_team_bottlenecks(_runtime(adapter))({"space": "DMS"}))

    assert adapter.calls == [("current", "DMS"), ("sprint", "DMS-SPRNT-3", "DMS")]
    rows = {row["member"]: row for row in result.data["bottlenecks"]}
    assert rows["alice"]["active_tasks"] == 3
    assert rows["alice"]["blocked"] == 1
    assert "descriptive_operational_metric_not_employee_score" in result.warnings


def test_team_distribution_is_exact_current_sprint_distribution():
    result = asyncio.run(build_team_distribution(_runtime())({"space": "DMS"}))
    rows = {row["member"]: row for row in result.data["members"]}

    assert result.data["total_tasks"] == 6
    assert rows["alice"]["tasks"] == 3
    assert rows["alice"]["blocked"] == 1
    assert rows["bob"]["tasks"] == 2
    assert rows["unassigned"]["tasks"] == 1


def test_release_scope_fails_closed_on_unproven_empty_membership():
    adapter = FakeAdapter()
    with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
        asyncio.run(
            build_release_scope(_runtime(adapter))(
                {"space": "WMB", "release_id": "release-uuid"}
            )
        )
    assert adapter.calls == [("release", "release-uuid", "WMB")]


def test_release_scope_returns_only_source_backed_membership():
    adapter = FakeAdapter()
    adapter.release_tasks = [
        _task("WMB-1", assignee="alice"),
        _task("WMB-2", assignee="bob"),
    ]
    result = asyncio.run(
        build_release_scope(_runtime(adapter))(
            {"space": "WMB", "release_id": "release-uuid"}
        )
    )

    assert result.data["count"] == 2
    assert result.data["task_keys"] == ["WMB-1", "WMB-2"]
    assert result.data["membership"] == "source_backed_release_task_query"
