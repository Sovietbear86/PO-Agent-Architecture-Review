import httpx
import pytest

from po_agent.adapters.task_api import (
    AS21CapabilityUnavailable,
    AS21SourceError,
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
)
from po_agent.domain.models import StatusCategory, TaskStatus


def task_payload(key="WMB-101", *, assignee="Ivanov Ivan", external_id="Ivanov.I.I", status="in_progress", space="WMB", sprint=None, release=None):
    attrs = [
        {"code": "assigned_to", "value": {"externalId": external_id, "login": external_id.lower()}},
        {"code": "scrum_board_plugin_sprint", "value": sprint},
        {"code": "fix_version_s", "value": [] if release is None else [{"code": release}]},
    ]
    return {
        "id": key,
        "source_id": key,
        "title": f"Implement login {key}",
        "description": "Implement OAuth login",
        "status": status,
        "assignee": assignee,
        "source": "swtr",
        "source_data": {"swtr_space": space, "swtr_attributes": attrs},
        "sprint": sprint,
    }


def real_shaped_payload():
    payload = task_payload(
        "WMB-30000",
        assignee="Калачанов Виктор",
        external_id="Kalachanov.V.V",
        status="done",
    )
    assigned = payload["source_data"]["swtr_attributes"][0]
    assigned["value"].update(
        firstName="Виктор",
        lastName="Калачанов",
        middleName="Вячеславович",
        login="kalachanov.v.v",
    )
    return payload


@pytest.mark.asyncio
async def test_search_does_not_send_ignored_q_parameter_and_filters_free_text_locally():
    async def handler(request):
        assert "q" not in request.url.params
        assert request.url.params["limit"] == "10000"
        return httpx.Response(200, json=[task_payload("WMB-101"), task_payload("WMB-102")])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    tasks = await TaskApiAS21Adapter(client=client).search_tasks("WMB-101")
    await client.aclose()
    assert [task.key for task in tasks] == ["WMB-101"]


@pytest.mark.asyncio
async def test_real_shaped_assignee_identity_is_canonicalized_and_searchable():
    async def handler(request):
        assert "q" not in request.url.params
        return httpx.Response(200, json=[real_shaped_payload(), task_payload("WMB-29999")])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    tasks = await adapter.search_tasks("assignee = Kalachanov.V.V")
    await client.aclose()

    assert [task.key for task in tasks] == ["WMB-30000"]
    task = tasks[0]
    assert task.assignee_id == "Kalachanov.V.V"
    assert task.assignee_login == "kalachanov.v.v"
    assert task.project_space == "WMB"
    assert task.status == TaskStatus.CLOSED
    assert task.status_category == StatusCategory.COMPLETED
    assert task.status_raw == "done"


@pytest.mark.asyncio
async def test_nonexistent_assignee_cannot_broaden_to_full_corpus():
    async def handler(request):
        return httpx.Response(200, json=[real_shaped_payload(), task_payload("WMB-29999")])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    tasks = await TaskApiAS21Adapter(client=client).search_tasks("assignee = nonexistent-user")
    await client.aclose()
    assert tasks == []


@pytest.mark.asyncio
async def test_project_status_sprint_and_release_filters_use_canonical_facts():
    payloads = [
        task_payload("WMB-1", status="done", sprint="WMB-SPRNT-7", release="R-1"),
        task_payload("WMB-2", status="in_progress", sprint="WMB-SPRNT-8", release="R-2"),
        task_payload("DMS-1", status="done", space="DMS", sprint="DMS-SPRNT-1", release="D-1"),
    ]

    async def handler(request):
        return httpx.Response(200, json=payloads)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    assert [t.key for t in await adapter.search_tasks("project = WMB AND status = Closed")] == ["WMB-1"]
    assert [t.key for t in await adapter.search_tasks("project = WMB AND sprint = WMB-SPRNT-7")] == ["WMB-1"]
    assert [t.key for t in await adapter.search_tasks("project = WMB AND release = R-2")] == ["WMB-2"]
    await client.aclose()


@pytest.mark.asyncio
async def test_unknown_search_field_fails_closed():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[])), base_url="http://task-api")
    with pytest.raises(AS21CapabilityUnavailable, match="unsupported AS21 search field"):
        await TaskApiAS21Adapter(client=client).search_tasks("magic = anything")
    await client.aclose()


@pytest.mark.asyncio
async def test_unknown_status_never_silently_becomes_open():
    payload = task_payload(status="Brand new AS21 state")

    async def handler(request):
        return httpx.Response(200, json=[payload])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    task = (await TaskApiAS21Adapter(client=client).search_tasks(""))[0]
    await client.aclose()
    assert task.status == TaskStatus.UNKNOWN
    assert task.status_category == StatusCategory.UNKNOWN
    assert task.status_raw == "Brand new AS21 state"


@pytest.mark.asyncio
async def test_get_task_requires_exact_key_not_first_search_hit_and_no_q():
    async def handler(request):
        assert "q" not in request.url.params
        assert request.url.params["source"] == "swtr"
        return httpx.Response(200, json=[task_payload("WMB-100"), task_payload("WMB-101")])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    task = await TaskApiAS21Adapter(client=client).get_task("wmb-101")
    await client.aclose()
    assert task and task.key == "WMB-101"


@pytest.mark.asyncio
async def test_transport_failure_is_not_silently_converted_to_empty_scope():
    async def handler(request):
        raise httpx.ConnectError("down", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    with pytest.raises(AS21SourceUnavailable):
        await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_malformed_protocol_fails_closed():
    async def handler(request):
        return httpx.Response(200, json={"items": []})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    with pytest.raises(AS21SourceError):
        await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_invalid_json_is_protocol_error_not_transport_outage():
    async def handler(request):
        return httpx.Response(200, content=b"not-json", headers={"content-type": "application/json"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    with pytest.raises(AS21SourceError, match="invalid JSON"):
        await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_unmappable_task_item_fails_closed_instead_of_disappearing():
    async def handler(request):
        return httpx.Response(200, json=[{"unexpected": "shape"}])

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    with pytest.raises(AS21SourceError, match="canonical Task"):
        await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()


@pytest.mark.asyncio
async def test_history_and_attachments_remain_explicitly_unsupported():
    client = httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200, json=[])), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21CapabilityUnavailable):
        await adapter.get_task_history("WMB-101")
    with pytest.raises(AS21CapabilityUnavailable):
        await adapter.get_attachment_metadata("WMB-101")
    await client.aclose()
