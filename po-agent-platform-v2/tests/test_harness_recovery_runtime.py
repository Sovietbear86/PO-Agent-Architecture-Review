"""Acceptance tests for the first recovered harness vertical slice."""

import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime


@pytest.mark.asyncio
async def test_exact_task_lookup_runs_through_versioned_skill_and_adapter():
    runtime = build_fake_runtime()

    response = await runtime.process(HarnessRequest(query="Найди задачу WMB-102"))

    assert response.status is ResponseStatus.COMPLETED
    assert response.intent == "task_lookup"
    assert response.skill_id == "task-lookup"
    assert response.skill_version == "1.0.0"
    assert response.data["task"]["key"] == "WMB-102"
    assert response.data["task"]["title"] == "Fix login bug"
    assert response.evidence
    assert {item.label for item in response.evidence} >= {"title", "status", "assignee"}
    assert response.trace_id
    assert response.latency_ms >= 0


@pytest.mark.asyncio
async def test_phrase_search_runs_through_search_skill():
    runtime = build_fake_runtime()

    response = await runtime.process(HarnessRequest(query="Найди login"))

    assert response.status is ResponseStatus.COMPLETED
    assert response.intent == "task_search"
    assert response.skill_id == "task-search"
    assert response.data["count"] == 2
    assert {task["key"] for task in response.data["tasks"]} == {"WMB-101", "WMB-102"}
    assert len(response.evidence) == 2


@pytest.mark.asyncio
async def test_session_id_is_preserved_and_trace_id_is_unique():
    runtime = build_fake_runtime()

    first = await runtime.process(HarnessRequest(query="WMB-101", session_id="session-1"))
    second = await runtime.process(HarnessRequest(query="WMB-101", session_id="session-1"))

    assert first.session_id == second.session_id == "session-1"
    assert first.trace_id != second.trace_id


@pytest.mark.asyncio
async def test_empty_query_returns_typed_failure_without_exception_details():
    runtime = build_fake_runtime()

    response = await runtime.process(HarnessRequest(query="   "))

    assert response.status is ResponseStatus.FAILED
    assert response.warnings == ["query_empty"]
    assert response.answer == "Пустой запрос."


def test_capability_allowlist_rejects_unknown_handler():
    runtime = build_fake_runtime()

    with pytest.raises(ValueError, match="not allow-listed"):
        import asyncio
        asyncio.run(runtime.capabilities.execute("unknown.capability", {}))
