import httpx
import pytest
from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable, TaskApiAS21Adapter
from po_agent.domain.models import StatusCategory, TaskStatus

def task_payload(key="WMB-101"):
    return {"id":key,"source_id":key,"title":"Implement login","description":"Implement OAuth login","status":"In progress","assignee":"Ivanov.I.I","source":"swtr","source_data":{}}

def real_shaped_payload():
    p=task_payload("WMB-30000")
    p["assignee"]="Калачанов Виктор"
    p["source_data"]={"swtr_attributes":[{"code":"assigned_to","value":{"externalId":"Kalachanov.V.V","login":"kalachanov.v.v","firstName":"Виктор","lastName":"Калачанов","middleName":"Вячеславович"}}]}
    return p

@pytest.mark.asyncio
async def test_search_maps_task_api_response_to_canonical_task():
    async def handler(request):
        assert request.url.params["q"]=="login"; return httpx.Response(200,json=[task_payload()])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api"); tasks=await TaskApiAS21Adapter(client=client).search_tasks("login"); await client.aclose()
    assert tasks[0].key=="WMB-101" and tasks[0].assignee=="Ivanov.I.I" and tasks[0].source=="swtr"

@pytest.mark.asyncio
async def test_real_shaped_assignee_identity_is_canonicalized():
    async def handler(request): return httpx.Response(200,json=[real_shaped_payload()])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api"); task=(await TaskApiAS21Adapter(client=client).search_tasks("Калачанов"))[0]; await client.aclose()
    assert task.assignee_id=="Kalachanov.V.V"
    assert task.assignee_login=="kalachanov.v.v"
    assert task.source_data["swtr_attributes"][0]["code"]=="assigned_to"

@pytest.mark.asyncio
async def test_unknown_status_never_silently_becomes_open():
    payload=task_payload(); payload["status"]="Brand new AS21 state"
    async def handler(request): return httpx.Response(200,json=[payload])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api"); task=(await TaskApiAS21Adapter(client=client).search_tasks("x"))[0]; await client.aclose()
    assert task.status==TaskStatus.UNKNOWN and task.status_category==StatusCategory.UNKNOWN and task.status_raw=="Brand new AS21 state"

@pytest.mark.asyncio
async def test_get_task_requires_exact_key_not_first_search_hit():
    async def handler(request): return httpx.Response(200,json=[task_payload("WMB-100"),task_payload("WMB-101")])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api"); task=await TaskApiAS21Adapter(client=client).get_task("wmb-101"); await client.aclose(); assert task and task.key=="WMB-101"

@pytest.mark.asyncio
async def test_transport_failure_is_not_silently_converted_to_empty_scope():
    async def handler(request): raise httpx.ConnectError("down",request=request)
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api"); adapter=TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21SourceUnavailable): await adapter.search_tasks("")
    await client.aclose()

@pytest.mark.asyncio
async def test_malformed_protocol_fails_closed():
    async def handler(request): return httpx.Response(200,json={"items":[]})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    with pytest.raises(AS21SourceError): await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()

@pytest.mark.asyncio
async def test_invalid_json_is_protocol_error_not_transport_outage():
    async def handler(request): return httpx.Response(200,content=b"not-json",headers={"content-type":"application/json"})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    with pytest.raises(AS21SourceError,match="invalid JSON"): await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()

@pytest.mark.asyncio
async def test_unmappable_task_item_fails_closed_instead_of_disappearing():
    async def handler(request): return httpx.Response(200,json=[{"unexpected":"shape"}])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    with pytest.raises(AS21SourceError,match="canonical Task"): await TaskApiAS21Adapter(client=client).search_tasks("")
    await client.aclose()

@pytest.mark.asyncio
async def test_unproven_source_facts_are_explicitly_unsupported():
    client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[])),base_url="http://task-api"); adapter=TaskApiAS21Adapter(client=client)
    with pytest.raises(AS21CapabilityUnavailable): await adapter.get_task_history("WMB-101")
    with pytest.raises(AS21CapabilityUnavailable): await adapter.get_attachment_metadata("WMB-101")
    with pytest.raises(AS21CapabilityUnavailable): await adapter.get_sprint_tasks("SPRINT")
    with pytest.raises(AS21CapabilityUnavailable): await adapter.get_release_tasks("RELEASE")
    await client.aclose()
