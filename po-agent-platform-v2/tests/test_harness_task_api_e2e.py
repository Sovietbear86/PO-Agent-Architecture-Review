import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from po_agent.adapters.task_api import TaskApiAS21Adapter
from po_agent.api.v1 import router, set_runtime
from po_agent.harness.source_aware_runtime import SourceAwareHarnessRuntime


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


def api_client(runtime) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    set_runtime(runtime)
    return TestClient(app)


def teardown_function():
    set_runtime(None)


def test_task_api_end_to_end_query_maps_source_to_harness_contract():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/tasks"
        assert request.url.params["q"] == "WMB-101"
        return httpx.Response(200, json=[task_payload()])

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=http)
    client = api_client(SourceAwareHarnessRuntime(adapter))

    response = client.post("/api/v1/query", json={"query": "Покажи WMB-101", "session_id": "e2e-1"})
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "COMPLETED"
    assert payload["skill"]["id"] == "task-lookup"
    assert payload["data"]["task"]["key"] == "WMB-101"
    assert payload["evidence"]
    assert payload["trace_id"]


def test_task_api_outage_is_failed_not_zero_work():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=http)
    client = api_client(SourceAwareHarnessRuntime(adapter))

    response = client.post("/api/v1/query", json={"query": "Обзор"})
    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["warnings"] == ["source_unavailable"]
    assert "0 задач" not in payload["answer"]
    assert "пуст" in payload["answer"].casefold()


def test_unsupported_history_is_explicit_capability_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[task_payload()])

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=http)
    client = api_client(SourceAwareHarnessRuntime(adapter))

    response = client.post("/api/v1/query", json={"query": "История WMB-101"})
    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["warnings"] == ["source_capability_unavailable"]


def test_malformed_task_api_protocol_is_typed_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"items": []})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(client=http)
    client = api_client(SourceAwareHarnessRuntime(adapter))

    response = client.post("/api/v1/query", json={"query": "Обзор"})
    payload = response.json()

    assert payload["status"] == "FAILED"
    assert payload["warnings"] == ["source_protocol_error"]
