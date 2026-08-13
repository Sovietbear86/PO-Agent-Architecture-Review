"""API acceptance coverage for the dialogue-first Harness Core."""

import os
from contextlib import contextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from po_agent.api.v1 import router, set_runtime
from po_agent.config.settings import reset_settings


@contextmanager
def hermetic_env(**env_vars):
    """Context manager to set hermetic environment for tests."""
    # Save original environment
    original = {k: os.environ.get(k) for k in env_vars}
    
    # Set new environment
    for k, v in env_vars.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    
    # Reset cached settings
    reset_settings()
    
    try:
        yield
    finally:
        # Restore original environment
        for k, v in original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        
        # Reset cached settings
        reset_settings()


def build_client() -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    return TestClient(app)


def setup_function():
    set_runtime(None)


def teardown_function():
    set_runtime(None)


def test_query_endpoint_exposes_typed_harness_contract():
    """Test harness query endpoint with conservative-fallback mode (no LLM)."""
    with hermetic_env(
        AS21_MODE="fake",
        SEMANTIC_LLM_ENABLED="false",
        OPENAI_API_KEY=None,
    ):
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
        assert payload["data"]["_harness"]["dialogue_state"] == "answered"
        assert "Ответ помог" in payload["data"]["_harness"]["feedback_prompt"]
        assert payload["evidence"]
        assert payload["trace_id"]
        assert payload["correlation_id"]


def test_health_endpoint_declares_runtime_source_semantics_and_readiness():
    """Test health endpoint with conservative-fallback mode (no LLM)."""
    with hermetic_env(
        AS21_MODE="fake",
        SEMANTIC_LLM_ENABLED="false",
        OPENAI_API_KEY=None,
    ):
        client = build_client()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["runtime"] == "harness-dialogue-v2"
        assert payload["semantic_mode"] == "conservative-fallback"
        assert payload["adapter"] == "fake"
        assert payload["source_status"] == "healthy"
        assert "history" in payload["source_facts"]
        assert payload["skill_readiness"]["ready"] > 0


def test_empty_query_is_a_typed_failure_not_an_unstructured_exception():
    """Test empty query returns typed FAILED with query_empty warning."""
    with hermetic_env(
        AS21_MODE="fake",
        SEMANTIC_LLM_ENABLED="false",
        OPENAI_API_KEY=None,
    ):
        client = build_client()
        response = client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "FAILED"
        assert payload["warnings"] == ["query_empty"]
        assert payload["trace_id"]


def test_health_endpoint_qwen_llm_mode():
    """Test health endpoint with Qwen LLM enabled (conservative-fallback for hermetic)."""
    with hermetic_env(
        AS21_MODE="fake",
        SEMANTIC_LLM_ENABLED="true",
        OPENAI_API_KEY="test-dummy-key",  # Dummy key, no actual network call
    ):
        client = build_client()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "healthy"
        assert payload["runtime"] == "harness-dialogue-v2"
        assert payload["semantic_mode"] == "qwen-llm"
        assert payload["adapter"] == "fake"
        assert payload["source_status"] == "healthy"
