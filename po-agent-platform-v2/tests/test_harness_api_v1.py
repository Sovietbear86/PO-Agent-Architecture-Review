"""API acceptance coverage for the recovered Harness Core."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from po_agent.api.v1 import router, set_runtime


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def setup_function():
    set_runtime(None)


def teardown_function():
    set_runtime(None)


def test_query_endpoint_exposes_typed_harness_contract():
    client = build_client()
    response = client.post(
        "/api/v1/query",
        json={"query": "Покажи WMB-102", "session_id": "ui-session-1"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "COMPLETED"
    assert payload["session_id"] == "ui-session-1"
    assert payload["intent"] == "task_lookup"
    assert payload["skill"] == {"id": "task-lookup", "version": "1.0.0"}
    assert payload["data"]["task"]["key"] == "WMB-102"
    assert payload["evidence"]
    assert payload["trace_id"]
    assert payload["correlation_id"]


def test_health_endpoint_declares_runtime_source_and_readiness():
    client = build_client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["runtime"] == "harness-recovery"
    assert payload["adapter"] == "fake"
    assert payload["source_status"] == "healthy"
    assert "history" in payload["source_facts"]
    assert payload["skill_readiness"]["ready"] > 0


def test_empty_query_is_a_typed_failure_not_an_unstructured_exception():
    client = build_client()
    response = client.post("/api/v1/query", json={"query": ""})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "FAILED"
    assert payload["warnings"] == ["query_empty"]
    assert payload["trace_id"]
