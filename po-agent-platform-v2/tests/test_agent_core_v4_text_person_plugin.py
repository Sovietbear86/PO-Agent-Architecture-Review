from __future__ import annotations

import asyncio

from po_agent.harness.contracts import CapabilityResult
from po_agent.harness.v4_plugins._task_live_handlers import build_task_search_text
from po_agent.harness.v4_plugins.task_catalog import SKILLS


class Response:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class Adapter:
    def __init__(self):
        self.calls = []

    async def _get_resilient(self, path, *, params):
        self.calls.append((path, dict(params)))
        return Response({
            "tasks": [],
            "source_complete": True,
            "completed_spaces": ["DMS"],
            "incomplete_spaces": [],
        })

    def _map(self, row):
        raise AssertionError("empty source result must not map rows")


class Runtime:
    def __init__(self):
        self.adapter = Adapter()
        self.resolve_calls = []

    async def _member_resolve(self, args):
        self.resolve_calls.append(dict(args))
        return CapabilityResult(
            answer="resolved",
            data={
                "external_id": "Semavin.M.M",
                "member_login": "Semavin.M.M",
                "reference": args["reference"],
            },
            evidence=[],
        )


def test_text_person_skill_is_single_capability() -> None:
    skill = next(item for item in SKILLS if item.id == "task.search_text")
    assert skill.capabilities == ("task.search_text",)


def test_text_person_handler_resolves_reference_inside_capability() -> None:
    runtime = Runtime()
    result = asyncio.run(
        build_task_search_text(runtime)(
            {"phrase": "риски", "reference": "Семавин", "space": "DMS"}
        )
    )

    assert runtime.resolve_calls == [{"reference": "Семавин", "space": "DMS"}]
    assert runtime.adapter.calls == [
        (
            "/api/v1/swtr-read/task-query",
            {
                "limit": 100,
                "max_pages": 100,
                "phrase": "риски",
                "space": "DMS",
                "assignee": "Semavin.M.M",
            },
        )
    ]
    assert result.data["count"] == 0
    assert result.data["source_assignee"] == "Semavin.M.M"
    assert result.data["source"] == "REAL_AS21"
