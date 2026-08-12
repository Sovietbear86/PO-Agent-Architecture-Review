import pytest

from po_agent.harness import HarnessRequest, ResponseStatus, build_fake_runtime
from po_agent.harness.operational_history import ExecutionRecord, SQLiteHistoryStore


@pytest.mark.asyncio
async def test_successful_execution_is_recorded_with_evidence_and_versions():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="Покажи WMB-102", session_id="history-s1"))

    record = runtime.history.get(response.trace_id)
    assert record is not None
    assert record.status == "COMPLETED"
    assert record.session_id == "history-s1"
    assert record.intent == "task_lookup"
    assert record.skill_id == "task-lookup"
    assert record.capability_id == "task.lookup"
    assert {item["label"] for item in record.evidence} >= {"title", "status", "assignee"}
    assert record.llm_used is False
    assert record.versions.agent == "2.1-recovery"
    assert record.versions.router == "deterministic-v1"


@pytest.mark.asyncio
async def test_failed_execution_is_recorded_with_error_category():
    runtime = build_fake_runtime()
    response = await runtime.process(HarnessRequest(query="", session_id="history-s2"))

    assert response.status is ResponseStatus.FAILED
    record = runtime.history.get(response.trace_id)
    assert record is not None
    assert record.status == "FAILED"
    assert record.error_category == "query_empty"
    assert record.warnings == ["query_empty"]


@pytest.mark.asyncio
async def test_session_history_is_ordered_and_not_used_as_implicit_prompt_context():
    runtime = build_fake_runtime()
    first = await runtime.process(HarnessRequest(query="Покажи WMB-101", session_id="same-session"))
    second = await runtime.process(HarnessRequest(query="Найди login", session_id="same-session"))

    records = runtime.history.by_session("same-session")
    assert [record.trace_id for record in records] == [first.trace_id, second.trace_id]

    # Operational history is audit/eval material, not automatic conversational memory.
    third = await runtime.process(HarnessRequest(query="что с ней?", session_id="same-session"))
    assert third.skill_id == "task-search"
    assert third.data["query"] == "что с ней?"


def test_history_store_is_append_only_for_trace_ids():
    store = SQLiteHistoryStore()
    record = ExecutionRecord(
        trace_id="trace-1",
        session_id="s",
        timestamp="2026-08-12T20:00:00+00:00",
        request="q",
        status="COMPLETED",
        intent="x",
        skill_id="skill",
        skill_version="1.0.0",
        capability_id="cap",
    )
    store.append(record)
    with pytest.raises(ValueError, match="trace already exists"):
        store.append(record)
