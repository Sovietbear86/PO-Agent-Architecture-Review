from __future__ import annotations

from types import SimpleNamespace

import pytest

from po_agent.api.v1 import QueryRequest, query_agent
from po_agent.harness.contracts import HarnessResponse, ResponseStatus


class _HeadersRequest:
    headers: dict[str, str] = {}


class _UIContract:
    def compact(self):
        return {
            "result_kind": "task_collection",
            "preferred_widget": "task_table",
            "required_fields": ["count", "tasks"],
            "states": ["LOADING", "SUCCESS_WITH_DATA", "REAL_EMPTY", "SOURCE_UNAVAILABLE", "ERROR"],
        }


class _V4Runtime:
    plugin_ids = ("builtin.core.a188",)

    async def process(self, request):
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id="trace-v4",
            session_id=request.session_id or "missing",
            answer="Найдено задач: 1.",
            intent="skill_native_v4",
            skill_id="tasks.search",
            skill_version="4.0.0-poc",
            data={"count": 1, "tasks": [{"key": "DMS-1", "title": "x"}], "_agent_core_v4": {"semantic_prepass_used": False}},
        )

    def ui_contract(self, skill_id):
        return _UIContract() if skill_id == "tasks.search" else None


class _LegacyRuntime:
    async def process(self, request):
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id="trace-legacy",
            session_id=request.session_id or "missing",
            answer="legacy",
        )


@pytest.mark.asyncio
async def test_public_query_uses_v4_when_enabled_and_ready(monkeypatch):
    import po_agent.api.v1 as api_v1

    v4 = _V4Runtime()
    monkeypatch.setattr(api_v1, "get_settings", lambda: SimpleNamespace(
        correlation_id_header="X-Correlation-Id",
        agent_core_v4_enabled=True,
    ))
    monkeypatch.setattr(api_v1, "get_runtime_bundle", lambda: SimpleNamespace(v4_runtime=v4))

    response = await query_agent(QueryRequest(query="задачи", session_id="ui-1"), _HeadersRequest())

    assert response["runtime"] == "agent_core_v4"
    assert response["session_id"] == "ui-1"
    assert response["skill"]["id"] == "tasks.search"
    assert response["ui"]["preferred_widget"] == "task_table"
    assert response["plugin_ids"] == ["builtin.core.a188"]
    assert response["data"]["_agent_core_v4"]["semantic_prepass_used"] is False


@pytest.mark.asyncio
async def test_public_query_preserves_legacy_path_when_v4_disabled(monkeypatch):
    import po_agent.api.v1 as api_v1

    monkeypatch.setattr(api_v1, "get_settings", lambda: SimpleNamespace(
        correlation_id_header="X-Correlation-Id",
        agent_core_v4_enabled=False,
    ))
    monkeypatch.setattr(api_v1, "get_runtime_bundle", lambda: SimpleNamespace(v4_runtime=None))
    monkeypatch.setattr(api_v1, "get_runtime", lambda: _LegacyRuntime())

    response = await query_agent(QueryRequest(query="legacy", session_id="ui-2"), _HeadersRequest())

    assert response["runtime"] == "legacy_harness"
    assert response["ui"] is None
    assert response["answer"] == "legacy"
