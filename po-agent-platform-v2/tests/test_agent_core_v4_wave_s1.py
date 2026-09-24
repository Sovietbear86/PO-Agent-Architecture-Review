from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import AgentCoreV4Runtime, V4NeedsClarification
from po_agent.harness.agent_core_v4_completion import SkillCompletionContract, is_skill_satisfied
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_s1 import (
    build_release_search,
    build_sprint_scope,
    build_sprint_throughput,
    build_sprint_velocity,
    build_sprint_wip,
)


def _task(
    key: str,
    *,
    completed: bool = False,
    open_: bool = True,
    status_type: str = "progress",
    status_category: str = "active_work",
    assignee: str | None = "User",
):
    status = SimpleNamespace(value="Closed" if completed else "In progress")
    category = SimpleNamespace(value=status_category)
    return SimpleNamespace(
        key=key,
        status=status,
        status_raw=status.value,
        status_type=status_type,
        status_category=category,
        assignee=assignee,
        assignee_login=assignee,
        assignee_id=assignee,
        is_completed=completed,
        is_open=open_,
    )


class FakeAdapter:
    def __init__(self):
        self.tasks = [
            _task("DMS-1", completed=True, open_=False, status_type="done", status_category="completed"),
            _task("DMS-2", completed=False, open_=True, status_type="progress"),
            _task("DMS-3", completed=False, open_=True, status_type="open", status_category="backlog", assignee=None),
        ]
        self.versions = [{"id": "DMS-R1", "name": "Release 1"}]

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None):
        assert sprint_id == "DMS-SPRNT-3"
        return list(self.tasks)

    async def list_sprints(self, space: str):
        assert space == "DMS"
        return [{
            "code": "DMS-SPRNT-3",
            "space": "DMS",
            "start_at": "2026-09-13T00:00:00Z",
            "finish_at": "2026-09-27T00:00:00Z",
            "status": "IN_PROGRESS",
        }]

    async def search_versions_bounded(self, *, query=None, space=None):
        return list(self.versions)


def _runtime(adapter=None):
    return SimpleNamespace(adapter=adapter or FakeAdapter())


def test_wave_s1_plugin_is_auto_discovered():
    registry = discover_v4_plugins()
    assert "builtin.wave_s1.sprint_flow_release_search" in registry.plugin_ids
    skill_ids = {skill.id for skill in registry.skills()}
    assert {
        "sprint.scope",
        "sprint.velocity",
        "sprint.throughput",
        "sprint.wip",
        "release.search",
    } <= skill_ids


def test_scope_velocity_and_wip_have_explicit_source_backed_semantics():
    runtime = _runtime()

    scope = asyncio.run(build_sprint_scope(runtime)({"sprint_id": "DMS-SPRNT-3"}))
    assert scope.data["total"] == 3
    assert scope.data["completed"] == 1
    assert scope.data["open"] == 2
    assert scope.data["unassigned"] == 1

    velocity = asyncio.run(build_sprint_velocity(runtime)({"sprint_id": "DMS-SPRNT-3"}))
    assert velocity.data["velocity"] == 1
    assert velocity.data["unit"] == "tasks/sprint"
    assert velocity.data["story_points_available"] is False

    wip = asyncio.run(build_sprint_wip(runtime)({"sprint_id": "DMS-SPRNT-3"}))
    assert wip.data["wip"] == 1
    assert wip.data["task_keys"] == ["DMS-2"]


def test_throughput_declares_snapshot_formula_and_source_dates():
    result = asyncio.run(
        build_sprint_throughput(_runtime())({"sprint_id": "DMS-SPRNT-3", "space": "DMS"})
    )
    assert result.data["unit"] == "completed_tasks/calendar_day"
    assert result.data["completed"] == 1
    assert result.data["elapsed_days"] >= 1
    assert "current_snapshot" in result.data["formula"]


def test_release_search_returns_bounded_source_results():
    result = asyncio.run(
        build_release_search(_runtime())({"space": "DMS", "query": "Release"})
    )
    assert result.data["count"] == 1
    assert result.data["release_id"] == "DMS-R1"
    assert result.data["bounded"] is True


def test_release_search_requires_typed_choice_when_single_release_is_required():
    adapter = FakeAdapter()
    adapter.versions = [
        {"id": "DMS-R1", "name": "Release 1"},
        {"id": "DMS-R2", "name": "Release 2"},
    ]
    handler = build_release_search(_runtime(adapter))
    with pytest.raises(V4NeedsClarification) as exc:
        asyncio.run(handler({"space": "DMS", "require_single": "true"}))
    assert exc.value.options == ("DMS-R1", "DMS-R2")


def test_release_health_contract_can_use_release_search_helper():
    registry = discover_v4_plugins()
    by_id = {skill.id: skill for skill in registry.skills()}
    release_health = by_id["release.health"]
    assert set(release_health.capabilities) == {"space.resolve", "release.search", "release.health"}


def test_wave_s1_metric_skills_can_resolve_explicit_period_or_current_sprint():
    registry = discover_v4_plugins()
    by_id = {skill.id: skill for skill in registry.skills()}
    expected_resolvers = {"space.resolve", "sprint.resolve", "sprint.search", "sprint.current"}
    for skill_id in ("sprint.scope", "sprint.velocity", "sprint.throughput", "sprint.wip"):
        capabilities = set(by_id[skill_id].capabilities)
        assert expected_resolvers <= capabilities
        assert skill_id in capabilities


def test_scope_and_wip_contracts_match_compacted_observation_shape():
    registry = discover_v4_plugins()
    by_id = {skill.id: skill for skill in registry.skills()}

    raw = {
        "sprint_id": "DMS-SPRNT-3",
        "total": 3,
        "wip": 1,
        "task_keys": ["DMS-1", "DMS-2", "DMS-3"],
        "source": "REAL_AS21",
    }

    compacted = AgentCoreV4Runtime._compact_data("sprint.wip", raw)
    assert "task_keys" not in compacted
    assert compacted["task_key_count"] == 3
    assert compacted["task_keys_sample"] == ["DMS-1", "DMS-2", "DMS-3"]

    for skill_id in ("sprint.scope", "sprint.wip"):
        requirement = by_id[skill_id].completion[0]
        assert "task_key_count" in requirement.data_keys
        observation = SimpleNamespace(
            capability_id=requirement.capability_id,
            data=dict(compacted),
            arguments={},
            step=1,
        )
        contract = SkillCompletionContract(skill_id=skill_id, requirements=(requirement,))
        assert is_skill_satisfied(contract, [observation])
