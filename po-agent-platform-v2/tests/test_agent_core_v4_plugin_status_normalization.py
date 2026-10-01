from __future__ import annotations

import asyncio
from types import SimpleNamespace

from po_agent.domain.models import TaskStatus
from po_agent.harness.contracts import CapabilityResult
from po_agent.harness.v4_plugins.core import build_task_search


class Runtime:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def _task_search(self, args: dict[str, str]) -> CapabilityResult:
        self.calls.append(dict(args))
        return CapabilityResult(
            answer="ok",
            data={"count": 11, "tasks": [], "source": "REAL_AS21"},
            evidence=[],
        )


def test_plugin_task_search_normalizes_russian_in_progress_without_core_change() -> None:
    runtime = Runtime()
    result = asyncio.run(
        build_task_search(runtime)(
            {
                "assignee": "Semavin.M.M",
                "status": "В работе",
            }
        )
    )

    assert result.data["count"] == 11
    assert runtime.calls == [
        {
            "assignee": "Semavin.M.M",
            "status": TaskStatus.IN_PROGRESS.value,
        }
    ]


def test_plugin_task_search_preserves_unknown_source_status_literal() -> None:
    runtime = Runtime()
    asyncio.run(
        build_task_search(runtime)(
            {
                "assignee": "Semavin.M.M",
                "status": "Custom Workflow State",
            }
        )
    )

    assert runtime.calls[0]["status"] == "Custom Workflow State"
