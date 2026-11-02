"""Offline bounded collector tests; no AS21 calls."""
import asyncio

import pytest

from app.services.sprint_forecast_collector import collect_sprint_workflow_evidence


def sprint():
    return {"sprint_id": "PRD-SPRNT-1", "complete": True, "membership_proven": True,
            "complete_tasks": [
                {"source_id": key, "source_data": {"sprint_membership_proven": True}}
                for key in ("PRD-1", "PRD-2")
            ]}


def history(code):
    return {"task_code": code, "page_info": {"complete": True, "has_next": False},
            "events": [{"task_code": code, "field_code": "workflow_status",
                        "changed_at": "2026-10-21T10:00:00Z",
                        "old_value": "In progress", "new_value": "Done"}]}


@pytest.mark.asyncio
async def test_bounded_collection_requires_complete_evidence():
    async def read_sprint(key):
        return sprint()

    async def read_history(code):
        return history(code)

    result = await collect_sprint_workflow_evidence(
        "PRD-SPRNT-1", read_sprint=read_sprint, read_history=read_history)
    assert result["complete"] is True
    assert result["task_count"] == result["history_complete_count"] == 2
    assert result["forecast"] is None
    assert result["committed_predictability"] is None


@pytest.mark.asyncio
async def test_incomplete_sprint_must_not_launch_history_requests():
    calls = []

    async def read_sprint(key):
        return {**sprint(), "complete": False}

    async def read_history(code):
        calls.append(code)
        return history(code)

    with pytest.raises(ValueError, match="sprint_membership_incomplete"):
        await collect_sprint_workflow_evidence(
            "PRD-SPRNT-1", read_sprint=read_sprint, read_history=read_history)
    assert calls == []


@pytest.mark.asyncio
async def test_incomplete_history_fails_entire_collection():
    async def read_sprint(key):
        return sprint()

    async def read_history(code):
        return {**history(code), "page_info": {"complete": False, "has_next": True}}

    with pytest.raises(ValueError, match="task_history_incomplete"):
        await collect_sprint_workflow_evidence(
            "PRD-SPRNT-1", read_sprint=read_sprint, read_history=read_history)


@pytest.mark.asyncio
async def test_semaphore_never_exceeds_five_history_requests():
    tasks = [{ "source_id": f"PRD-{x}", "source_data": {"sprint_membership_proven": True}} for x in range(16)]
    concurrent = 0
    maximum = 0

    async def read_sprint(key):
        return {**sprint(), "complete_tasks": tasks}

    async def read_history(code):
        nonlocal concurrent, maximum
        concurrent += 1
        maximum = max(maximum, concurrent)
        await asyncio.sleep(0)
        concurrent -= 1
        return history(code)

    out = await collect_sprint_workflow_evidence(
        "PRD-SPRNT-1", read_sprint=read_sprint,
        read_history=read_history, concurrency=5)
    assert maximum <= 5
    assert out["history_complete_count"] == 16


@pytest.mark.asyncio
async def test_timeout_is_typed():
    async def read_sprint(key):
        await asyncio.sleep(2)
        return sprint()

    async def read_history(code):
        return history(code)

    with pytest.raises(ValueError, match="sprint_source_timeout"):
        await collect_sprint_workflow_evidence(
            "PRD-SPRNT-1", read_sprint=read_sprint,
            read_history=read_history, timeout_seconds=1.0)


@pytest.mark.asyncio
async def test_identity_and_bounds_fail_closed():
    async def read_sprint(key):
        return {**sprint(), "sprint_id": "OTHER-SPRNT-1"}

    async def read_history(code):
        return history(code)

    with pytest.raises(ValueError, match="sprint_source_identity_mismatch"):
        await collect_sprint_workflow_evidence(
            "PRD-SPRNT-1", read_sprint=read_sprint, read_history=read_history)
    with pytest.raises(ValueError, match="invalid_source_bounds"):
        await collect_sprint_workflow_evidence(
            "PRD-SPRNT-1", read_sprint=read_sprint,
            read_history=read_history, concurrency=6)
