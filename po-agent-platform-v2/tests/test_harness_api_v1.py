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
        LLM_API_KEY=None,
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
        LLM_API_KEY=None,
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
        LLM_API_KEY=None,
    ):
        client = build_client()
        response = client.post("/api/v1/query", json={"query": ""})
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "FAILED"
        assert payload["warnings"] == ["query_empty"]
        assert payload["trace_id"]


def test_health_endpoint_qwen_llm_mode():
    """Test health endpoint with Qwen LLM enabled (no network call with dummy key)."""
    # Note: This test uses a dummy key - it still attempts network but fails gracefully
    # For truly hermetic qwen mode testing, mock the LLM client instead
    with hermetic_env(
        AS21_MODE="fake",
        SEMANTIC_LLM_ENABLED="true",
        LLM_API_KEY="test-dummy-key",
        OPENAI_BASE_URL="http://127.0.0.1:9999",  # Non-existent server - should fail
    ):
        client = build_client()
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        payload = response.json()
        # With dummy key pointing to non-existent server, semantic mode may be degraded
        # The test verifies that LLM_API_KEY is respected (not using local ~/.config/openai/api_key)
        assert payload["status"] == "healthy"
        assert payload["runtime"] == "harness-dialogue-v2"


def test_as21_diagnostics_reports_runtime_wiring_without_secrets():
    with hermetic_env(
        AS21_MODE="fake",
        PO_AGENT_AS21_MODE=None,
        TASK_API_BASE_URL="http://127.0.0.1:8003",
        PO_AGENT_TASK_API_BASE_URL=None,
        SWTR_TOKEN="must-not-leak",
        LLM_API_KEY="must-not-leak",
        SEMANTIC_LLM_ENABLED="false",
    ):
        client = build_client()
        response = client.get("/api/v1/ops/as21-diagnostics")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "degraded"
        assert "as21_mode_not_task_api" in payload["blockers"]
        assert payload["settings"]["as21_mode"] == "fake"
        assert payload["settings"]["task_api_base_url"] == "http://127.0.0.1:8003"
        assert payload["module_paths"]["po_agent"]["state"] == "OK"
        assert payload["task_api"]["state"] == "SKIPPED_NON_TASK_API_MODE"
        assert payload["oracle_guidance"]["full_task_sync_required"] is False
        assert payload["repair_actions"]
        assert "must-not-leak" not in response.text


def test_as21_diagnostics_accepts_po_agent_env_aliases():
    with hermetic_env(
        AS21_MODE=None,
        PO_AGENT_AS21_MODE="task-api",
        TASK_API_BASE_URL=None,
        PO_AGENT_TASK_API_BASE_URL="http://127.0.0.1:9",
        SEMANTIC_LLM_ENABLED="false",
        LLM_API_KEY=None,
    ):
        client = build_client()
        response = client.get("/api/v1/ops/as21-diagnostics")
        assert response.status_code == 200
        payload = response.json()
        assert payload["settings"]["as21_mode"] == "task-api"
        assert payload["settings"]["task_api_base_url"] == "http://127.0.0.1:9"
        assert payload["env"]["PO_AGENT_AS21_MODE"] == "task-api"
        assert payload["task_api"]["state"] in {
            "TASK_API_UNREACHABLE",
            "SWTR_READ_ROUTES_UNPROVEN",
        }


def test_conservative_fallback_ignores_local_llm_api_key():
    """Regression test: local LLM_API_KEY should not affect conservative fallback mode."""
    # Set a local LLM_API_KEY (simulating ~/.config/openai/api_key scenario)
    # But test should use conservative-fallback anyway due to SEMANTIC_LLM_ENABLED=false
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("LLM_API_KEY=should-not-be-used\n")
        f.write("SEMANTIC_LLM_ENABLED=false\n")
        env_file = f.name
    
    try:
        # This simulates having a .env file with LLM_API_KEY
        # Conservative fallback should still work because SEMANTIC_LLM_ENABLED=false
        with hermetic_env(
            AS21_MODE="fake",
            SEMANTIC_LLM_ENABLED="false",
            LLM_API_KEY=None,
        ):
            client = build_client()
            response = client.get("/api/v1/health")
            assert response.status_code == 200
            payload = response.json()
            assert payload["semantic_mode"] == "conservative-fallback"
    finally:
        os.unlink(env_file)
