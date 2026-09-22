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


class _ContinuationV4Runtime:
    plugin_ids = ("builtin.core.a188",)

    def __init__(self):
        self.requests = []

    async def process(self, request):
        self.requests.append(request)
        if len(self.requests) == 1:
            return HarnessResponse(
                status=ResponseStatus.NEEDS_CLARIFICATION,
                trace_id="trace-clarify",
                session_id=request.session_id or "missing",
                question="Уточните пространство.",
                options=["DMS", "WMB"],
                intent="skill_native_v4",
                skill_id="tasks.search",
                skill_version="4.0.0-poc",
                data={
                    "_agent_core_v4": {
                        "runtime": "Agent Core v4",
                        "semantic_prepass_used": False,
                        "loaded_skills": ["tasks.search"],
                        "trajectory": [],
                        "continuation_observations": [
                            {
                                "step": 1,
                                "capability_id": "member.resolve",
                                "arguments": {"reference": "Гаранин"},
                                "answer": "Пользователь подтверждён.",
                                "data": {
                                    "member_login": "Garanin.R.V",
                                    "external_id": "Garanin.R.V",
                                    "source": "REAL_AS21",
                                },
                            }
                        ],
                        "continuation_required_skills": ["tasks.search"],
                    }
                },
            )
        return HarnessResponse(
            status=ResponseStatus.COMPLETED,
            trace_id="trace-complete",
            session_id=request.session_id or "missing",
            answer="Найдено задач: 6.",
            intent="skill_native_v4",
            skill_id="tasks.search",
            skill_version="4.0.0-poc",
            data={"count": 6, "_agent_core_v4": {"semantic_prepass_used": False}},
        )

    def ui_contract(self, skill_id):
        return _UIContract() if skill_id == "tasks.search" else None


@pytest.mark.asyncio
async def test_clarification_continuation_restores_generic_harness_execution_state(monkeypatch):
    import po_agent.api.v1 as api_v1

    runtime = _ContinuationV4Runtime()
    api_v1.set_runtime(None)
    monkeypatch.setattr(api_v1, "get_settings", lambda: SimpleNamespace(
        correlation_id_header="X-Correlation-Id",
        agent_core_v4_enabled=True,
    ))
    monkeypatch.setattr(api_v1, "get_runtime_bundle", lambda: SimpleNamespace(v4_runtime=runtime))

    first = await query_agent(
        QueryRequest(query="задачи Гаранина в сентябрьском спринте", session_id="ui-cont"),
        _HeadersRequest(),
    )
    assert first["status"] == "NEEDS_CLARIFICATION"
    clarification_id = first["clarification_id"]
    assert clarification_id
    # Internal resume observations/goals must not leak into the public payload.
    state = first["data"]["_agent_core_v4"]
    assert "continuation_observations" not in state
    assert "continuation_required_skills" not in state

    second = await query_agent(
        QueryRequest(
            query="DMS",
            session_id="ui-cont",
            clarification_id=clarification_id,
            clarification_option="DMS",
        ),
        _HeadersRequest(),
    )
    assert second["status"] == "COMPLETED"
    resumed = runtime.requests[1]
    assert resumed.resume_loaded_skills == ("tasks.search",)
    assert resumed.required_completion_skills == ("tasks.search",)
    assert len(resumed.resume_observations) == 1
    assert resumed.resume_observations[0]["capability_id"] == "member.resolve"
    assert "Исходный запрос пользователя" in resumed.query
    assert "Ответ пользователя на уточнение: DMS" in resumed.query


@pytest.mark.asyncio
async def test_health_uses_lightweight_source_probe_not_unscoped_task_search(monkeypatch):
    import po_agent.api.v1 as api_v1

    class Adapter:
        def __init__(self):
            self.health_calls = 0
            self.search_calls = 0

        async def source_health(self):
            self.health_calls += 1
            return {"status": "ok"}

        async def search_tasks(self, *args, **kwargs):
            self.search_calls += 1
            raise AssertionError("health must not perform unscoped task search")

    adapter = Adapter()
    readiness = SimpleNamespace(summary=lambda: {"ready": 1}, available_facts=frozenset({"tasks", "attachments", "history"}))
    bundle = SimpleNamespace(
        mode="task-api",
        adapter=adapter,
        readiness=readiness,
        v4_runtime=SimpleNamespace(plugin_ids=("builtin.core.a188",)),
    )
    monkeypatch.setattr(api_v1, "get_settings", lambda: SimpleNamespace(
        correlation_id_header="X-Correlation-Id",
        semantic_llm_enabled=False,
        llm_api_key=None,
        agent_core_v3_enabled=False,
        agent_core_v4_enabled=True,
        as21_mode="task-api",
    ))
    monkeypatch.setattr(api_v1, "get_runtime_bundle", lambda: bundle)

    response = await api_v1.health_check(_HeadersRequest())
    assert response["status"] == "healthy"
    assert adapter.health_calls == 1
    assert adapter.search_calls == 0
