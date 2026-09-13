"""Assignment 185 — B1 regression: production adapter fails closed on an
incomplete sprint collection and maps a proven-complete one.

The route now distinguishes a proven-complete collection from a bounded
partial view (the source could not paginate and no fallback produced a
complete set). The adapter must fail closed on ``complete=false`` — a partial
view must never masquerade as an empty or complete sprint — and map the
canonical ``complete_tasks`` rows (with sprint membership) when complete.
"""

import httpx
import pytest

from po_agent.adapters.production_task_api import ProductionTaskApiAS21Adapter
from po_agent.adapters.task_api import AS21SourceError


def _canonical_row(code: str, sprint: str = "DMS-SPRNT-1", space: str = "DMS") -> dict:
    """Same shape the fixed swtr_read route returns in ``complete_tasks``."""
    return {
        "source_id": code,
        "title": f"Task {code}",
        "status": "In progress",
        "source": "swtr",
        "source_data": {
            "swtr_space": space,
            "workflow_status": "In progress",
            "swtr_attributes": [
                {"code": "workflow_status", "value": {"name": "In progress", "statusType": "progress"}},
                {"code": "scrum_board_plugin_sprint", "value": {"code": sprint}},
            ],
            "live_sprint_route": True,
        },
    }


@pytest.mark.asyncio
async def test_incomplete_collection_fails_closed_not_empty_or_complete():
    payload = {
        "sprint_id": "DMS-SPRNT-1",
        "complete": False,
        "source_path": "get_sprint_tasks",
        "complete_tasks": [_canonical_row("DMS-1")],
    }

    async def handler(request):
        assert request.url.path == "/api/v1/swtr-read/sprints/DMS-SPRNT-1/tasks"
        assert request.url.params.get("complete") == "true"
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = ProductionTaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceError, match="incomplete"):
        await adapter.get_sprint_tasks("DMS-SPRNT-1")
    await client.aclose()


@pytest.mark.asyncio
async def test_complete_collection_maps_canonical_rows_with_sprint():
    rows = [_canonical_row(f"DMS-{i}") for i in range(1, 6)]
    payload = {"sprint_id": "DMS-SPRNT-1", "complete": True, "source_path": "get_sprint_tasks",
               "complete_tasks": rows}

    async def handler(request):
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = ProductionTaskApiAS21Adapter(client=client)
    tasks = await adapter.get_sprint_tasks("DMS-SPRNT-1", space="DMS")
    await client.aclose()

    assert [t.key for t in tasks] == [f"DMS-{i}" for i in range(1, 6)]
    assert all(t.sprint_id == "DMS-SPRNT-1" for t in tasks)
    assert all(t.project_space == "DMS" for t in tasks)


@pytest.mark.asyncio
async def test_space_filter_still_applies_to_complete_collection():
    rows = [_canonical_row("DMS-1", space="DMS"), _canonical_row("OLP-1", space="OLP", sprint="DMS-SPRNT-1")]
    payload = {"sprint_id": "DMS-SPRNT-1", "complete": True, "complete_tasks": rows}

    async def handler(request):
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = ProductionTaskApiAS21Adapter(client=client)
    tasks = await adapter.get_sprint_tasks("DMS-SPRNT-1", space="DMS")
    await client.aclose()

    assert [t.key for t in tasks] == ["DMS-1"]