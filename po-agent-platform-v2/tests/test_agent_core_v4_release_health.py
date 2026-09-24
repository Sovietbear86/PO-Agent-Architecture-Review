from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugins.core import build_release_health


class FakeReleaseAdapter:
    def __init__(self, tasks):
        self.tasks = list(tasks)
        self.calls = []

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        self.calls.append((release_id, space))
        return list(self.tasks)


def _task(key: str, *, completed: bool, blocked: bool = False):
    return SimpleNamespace(
        key=key,
        title=key,
        is_completed=completed,
        is_open=not completed,
        is_blocked=blocked,
        status_raw="Closed" if completed else ("Blocked" if blocked else "In progress"),
        status=SimpleNamespace(value="Closed" if completed else "In progress"),
    )


def test_release_health_uses_bounded_space_scoped_membership():
    adapter = FakeReleaseAdapter([
        _task("WMB-1", completed=True),
        _task("WMB-2", completed=False, blocked=True),
    ])
    runtime = SimpleNamespace(adapter=adapter)

    result = asyncio.run(
        build_release_health(runtime)({"release_id": "release-uuid", "space": "WMB"})
    )

    assert adapter.calls == [("release-uuid", "WMB")]
    assert result.data["total"] == 2
    assert result.data["completed"] == 1
    assert result.data["blocked"] == 1
    assert result.data["completion_percent"] == 50.0
    assert result.data["membership"] == "source_backed_release_task_query"


def test_release_health_fails_closed_when_membership_is_not_exposed():
    adapter = FakeReleaseAdapter([])
    runtime = SimpleNamespace(adapter=adapter)

    with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
        asyncio.run(
            build_release_health(runtime)({"release_id": "release-uuid", "space": "WMB"})
        )

    assert adapter.calls == [("release-uuid", "WMB")]
