import httpx
import pytest

from po_agent.adapters.task_api import (
    AS21CapabilityUnavailable,
    AS21SourceError,
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
)


def task_payload(key: str = "WMB-101") -> dict:
    return {
        "id": key,
        "source_id": key,
        "title": "Implement login",
        "description": "Implement OAuth login",
        "status": "In progress",
        "assignee": "Ivanov.I.I",
        "source": "swtr",
        "source_data": {},
    }


@pytest.mark.asyncio
async def test_search_maps_task_api_response_to_canonical_task():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["q"] == "login"
        return httpx.Response(200, json=[task_payload()])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    tasks = await adapter.search_tasks("login")
    await client.aclose()

    assert len(tasks) == 1
    assert tasks[0].key == "WMB-101"
    assert tasks[0].assignee == "Ivanov.I.I"
    assert tasks[0].source == "swtr"


@pytest.mark.asyncio
async def test_get_task_requires_exact_key_not_first_search_hit():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[task_payload("WMB-100"), task_payload("WMB-101")])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    task = await adapter.get_task("wmb-101")
    await client.aclose()

    assert task is not None
    assert task.key == "WMB-101"


@pytest.mark.asyncio
async def test_transport_failure_is_not_silently_converted_to_empty_scope():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceUnavailable):
        await adapter.search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_malformed_protocol_fails_closed():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceError):
        await adapter.search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_invalid_json_is_protocol_error_not_transport_outage():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json", headers={"content-type": "application/json"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceError, match="invalid JSON"):
        await adapter.search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_unmappable_task_item_fails_closed_instead_of_disappearing():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"unexpected": "shape"}])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceError, match="canonical Task"):
        await adapter.search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_missing_history_and_attachments_are_explicitly_unsupported():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[])), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21CapabilityUnavailable):
        await adapter.get_task_history("WMB-101")
    with pytest.raises(AS21CapabilityUnavailable):
        await adapter.get_attachment_metadata("WMB-101")
    await client.aclose()
