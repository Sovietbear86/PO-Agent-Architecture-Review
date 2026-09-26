from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.task_catalog import build_task_search_release


class FakeAdapter:
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.calls = []

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        self.calls.append((release_id, space))
        return list(self.tasks)


def _task(key: str):
    return SimpleNamespace(
        key=key,
        title=key,
        status_raw="In progress",
        status=SimpleNamespace(value="In progress"),
        assignee_login="user",
        assignee_id="user",
        assignee="user",
        release_id="release-uuid",
        project_space="WMB",
    )


def test_task_search_release_skill_uses_directory_resolution_not_task_release_resolve():
    registry = discover_v4_plugins()
    skill = next(skill for skill in registry.skills() if skill.id == "task.search_release")

    assert skill.capabilities == ("space.resolve", "release.search", "task.search_release")
    procedure = "\n".join(skill.procedure)
    assert "release.search" in procedure
    assert "do NOT use task-based release.resolve" in procedure
    assert "SOURCE_CONDITIONAL" in procedure


def test_task_search_release_empty_membership_fails_source_conditional():
    adapter = FakeAdapter([])
    runtime = SimpleNamespace(adapter=adapter)

    with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
        asyncio.run(
            build_task_search_release(runtime)(
                {"release_id": "release-uuid", "space": "WMB"}
            )
        )

    assert adapter.calls == [("release-uuid", "WMB")]


def test_task_search_release_nonempty_membership_returns_exact_rows():
    adapter = FakeAdapter([_task("WMB-1"), _task("WMB-2")])
    runtime = SimpleNamespace(adapter=adapter)

    result = asyncio.run(
        build_task_search_release(runtime)(
            {"release_id": "release-uuid", "space": "WMB"}
        )
    )

    assert result.data["count"] == 2
    assert [row["key"] for row in result.data["tasks"]] == ["WMB-1", "WMB-2"]
    assert result.data["membership"] == "source_backed_release_task_query"
    assert adapter.calls == [("release-uuid", "WMB")]
