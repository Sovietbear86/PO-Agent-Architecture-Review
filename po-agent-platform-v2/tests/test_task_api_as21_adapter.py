import httpx
import pytest
from po_agent.adapters.task_api import AS21CapabilityUnavailable, AS21SourceError, AS21SourceUnavailable, TaskApiAS21Adapter
from po_agent.domain.models import AttachmentType, StatusCategory, TaskStatus


def task_payload(key="WMB-101", **overrides):
    payload={"id":key,"source_id":key,"title":"Implement login","description":"Implement OAuth login","status":"In progress","assignee":"Ivanov.I.I","source":"swtr","source_data":{}}
    payload.update(overrides)
    return payload


def real_shaped_payload():
    return task_payload(
        "WMB-30000",
        assignee="Калачанов Виктор",
        status="done",
        source_data={
            "swtr_space":"WMB",
            "swtr_attributes":[
                {"code":"assigned_to","value":{"externalId":"Kalachanov.V.V","login":"kalachanov.v.v","firstName":"Виктор","lastName":"Калачанов","middleName":"Вячеславович"}}
            ],
        },
    )


@pytest.mark.asyncio
async def test_search_does_not_send_ignored_q_parameter_and_filters_free_text_locally():
    async def handler(request):
        assert "q" not in request.url.params
        assert request.url.params["limit"] == "10000"
        return httpx.Response(200,json=[task_payload(),task_payload("WMB-102",title="Other",description="No match")])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    tasks=await TaskApiAS21Adapter(client=client).search_tasks("OAuth")
    await client.aclose()
    assert [t.key for t in tasks]==["WMB-101"]


@pytest.mark.asyncio
async def test_real_shaped_assignee_identity_is_canonicalized_and_searchable():
    async def handler(request): return httpx.Response(200,json=[real_shaped_payload(),task_payload("WMB-200")])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    tasks=await TaskApiAS21Adapter(client=client).search_tasks("assignee = Kalachanov.V.V")
    await client.aclose()
    assert [t.key for t in tasks]==["WMB-30000"]
    task=tasks[0]
    assert task.assignee_id=="Kalachanov.V.V"
    assert task.assignee_login=="kalachanov.v.v"
    assert task.project_space=="WMB"
    assert task.status==TaskStatus.CLOSED


@pytest.mark.asyncio
async def test_nonexistent_assignee_cannot_broaden_to_full_corpus():
    async def handler(request): return httpx.Response(200,json=[real_shaped_payload(),task_payload("WMB-200")])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    tasks=await TaskApiAS21Adapter(client=client).search_tasks("assignee = nonexistent-user")
    await client.aclose()
    assert tasks==[]


@pytest.mark.asyncio
async def test_project_status_sprint_and_release_filters_use_canonical_facts():
    payload=real_shaped_payload()
    payload["sprint"]="SPRINT-42"
    payload["source_data"]["swtr_attributes"].append({"code":"fix_version_s","value":[{"code":"REL-1"}]})
    async def handler(request): return httpx.Response(200,json=[payload])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    adapter=TaskApiAS21Adapter(client=client)
    tasks=await adapter.search_tasks("project = WMB AND status = Closed AND sprint = SPRINT-42 AND release = REL-1")
    await client.aclose()
    assert [t.key for t in tasks]==["WMB-30000"]


@pytest.mark.asyncio
async def test_long_as21_description_is_preserved_not_truncated_or_dropped():
    long_description="A"*25000
    payload=real_shaped_payload(); payload["description"]=long_description
    async def handler(request): return httpx.Response(200,json=[payload])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    tasks=await TaskApiAS21Adapter(client=client).search_tasks("key = WMB-30000")
    await client.aclose()
    assert len(tasks)==1
    assert tasks[0].description==long_description
    assert len(tasks[0].description)==25000


@pytest.mark.asyncio
async def test_unknown_search_field_fails_closed():
    client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json=[])),base_url="http://task-api")
    with pytest.raises(AS21CapabilityUnavailable): await TaskApiAS21Adapter(client=client).search_tasks("magic = anything")
    await client.aclose()


@pytest.mark.asyncio
async def test_unknown_status_never_silently_becomes_open():
    payload=task_payload(status="Brand new AS21 state")
    async def handler(request): return httpx.Response(200,json=[payload])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    task=(await TaskApiAS21Adapter(client=client).search_tasks("key = WMB-101"))[0]
    await client.aclose()
    assert task.status==TaskStatus.UNKNOWN and task.status_category==StatusCategory.UNKNOWN and task.status_raw=="Brand new AS21 state"


@pytest.mark.asyncio
async def test_get_task_requires_exact_key_not_first_search_hit_and_no_q():
    async def handler(request):
        assert "q" not in request.url.params
        if request.url.path == "/api/v1/swtr-read/tasks/WMB-101/files":
            return httpx.Response(200,json={"task_code":"WMB-101","files":[]})
        return httpx.Response(200,json=[task_payload("WMB-100"),task_payload("WMB-101")])
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    task=await TaskApiAS21Adapter(client=client).get_task("wmb-101")
    await client.aclose()
    assert task and task.key=="WMB-101"


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
async def test_attachment_metadata_maps_rich_read_payload_without_downloading_content():
    async def handler(request):
        assert request.url.path == "/api/v1/swtr-read/tasks/WMB-30000/files"
        return httpx.Response(200,json={"task_code":"WMB-30000","files":[{
            "id":"file-1","name":"requirements.pdf","size":12345,
            "contentType":"application/pdf","created":"2026-07-10T10:00:00Z",
            "createdBy":"Author","version":1,"hash":"abc","storageType":"s3"
        }]})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler),base_url="http://task-api")
    items=await TaskApiAS21Adapter(client=client).get_attachment_metadata("WMB-30000")
    await client.aclose()
    assert len(items)==1
    assert items[0].id=="file-1" and items[0].name=="requirements.pdf"
    assert items[0].size_bytes==12345 and items[0].type==AttachmentType.PDF
    assert items[0].url is None


@pytest.mark.asyncio
async def test_attachment_metadata_can_select_one_file_and_malformed_metadata_fails_closed():
    payload={"task_code":"WMB-30000","files":[
        {"id":"a","name":"one.xlsx","size":10,"contentType":"application/vnd.ms-excel","created":"2026-07-10T10:00:00Z"},
        {"id":"b","name":"two.txt","size":20,"contentType":"text/plain","created":"2026-07-10T11:00:00Z"},
    ]}
    async def good_handler(request): return httpx.Response(200,json=payload)
    client=httpx.AsyncClient(transport=httpx.MockTransport(good_handler),base_url="http://task-api")
    items=await TaskApiAS21Adapter(client=client).get_attachment_metadata("WMB-30000","b")
    await client.aclose()
    assert [item.id for item in items]==["b"] and items[0].type==AttachmentType.TEXT

    async def bad_handler(request): return httpx.Response(200,json={"task_code":"WMB-30000","files":[{"id":"x","name":"broken.pdf"}]})
    client=httpx.AsyncClient(transport=httpx.MockTransport(bad_handler),base_url="http://task-api")
    with pytest.raises(AS21SourceError): await TaskApiAS21Adapter(client=client).get_attachment_metadata("WMB-30000")
    await client.aclose()


@pytest.mark.asyncio
async def test_get_task_history_maps_workflow_status_changes():
    history_payload = {
        "task_code": "WMB-101",
        "events": [
            {
                "task_code": "WMB-101",
                "field_code": "workflow_status",
                "old_value": "Open",
                "new_value": "In progress",
                "changed_at": "2026-07-10T10:00:00Z",
                "actor": "User1"
            },
            {
                "task_code": "WMB-101",
                "field_code": "workflow_status",
                "old_value": "In progress",
                "new_value": "Resolved",
                "changed_at": "2026-07-11T14:30:00Z",
                "actor": "User2"
            }
        ],
        "page_info": {"has_next": False, "page": 0, "page_size": 100, "total": 2}
    }
    
    async def handler(request):
        return httpx.Response(200, json=history_payload)
    
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=client)
    transitions = await adapter.get_task_history("WMB-101")
    await client.aclose()
    
    assert len(transitions) == 2
    assert transitions[0].from_status == TaskStatus.OPEN
    assert transitions[0].to_status == TaskStatus.IN_PROGRESS
    assert transitions[0].author == "User1"
    assert transitions[1].from_status == TaskStatus.IN_PROGRESS
    assert transitions[1].to_status == TaskStatus.RESOLVED
    assert transitions[1].author == "User2"
