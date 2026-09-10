from __future__ import annotations

import pytest

from po_agent.harness.agent_core_v3 import AcceptedTurnContract
from po_agent.harness.agent_core_v3_pilot import AgentCoreV3PilotProcessor


class _RecordingAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def search_tasks(self, jql: str, max_results: int = 50, fields=None):
        del fields
        self.calls.append((jql, max_results))
        return []


@pytest.mark.asyncio
async def test_h1b_search_executor_requests_full_certified_collection_window() -> None:
    adapter = _RecordingAdapter()
    processor = AgentCoreV3PilotProcessor(
        adapter,  # type: ignore[arg-type]
        interpreter=object(),  # type: ignore[arg-type]
        grounder=object(),  # type: ignore[arg-type]
    )
    contract = AcceptedTurnContract(
        turn_id="full-collection",
        intent="task_search",
        constraints={"assignee": "Example.User"},
        requested_constraints=frozenset({"assignee"}),
    )

    answer, data, evidence = await processor._execute_search(contract)

    assert adapter.calls == [("assignee = Example.User", 10000)]
    assert answer == "Найдено задач: 0."
    assert data["count"] == 0
    assert evidence == []
