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
    """Exact lookup uses the proven canonical scan + rich attachment boundary.

    The old test asserted a legacy `q=WMB-101` transport detail. Production QA
    proved that exact-key correctness must not trust a first search hit, so the
    adapter now scans canonical SWTR tasks and verifies the exact key locally,
    then performs the canonical rich-read attachment metadata request.
    """
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/v1/tasks":
            assert request.url.params["limit"] == "10000"
            assert request.url.params["source"] == "swtr"
            return httpx.Response(200, json=[task_payload()])
        if request.url.path == "/api/v1/swtr-read/tasks/WMB-101/files":
            return httpx.Response(200, json={"files": []})
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

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
