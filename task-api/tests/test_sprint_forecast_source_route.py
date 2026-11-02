"""Offline tests for read-only sprint source-proof facade; no REAL AS21."""
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.history import HistoryResponse, HistoryEvent
from app.routers import swtr_read


def complete_sprint():
    return {
        "sprint_id": "PRD-SPRNT-1", "complete": True, "membership_proven": True,
        "complete_tasks": [
            {"source_id": "PRD-1", "source_data": {"sprint_membership_proven": True}},
            {"source_id": "PRD-2", "source_data": {"sprint_membership_proven": True}},
        ],
    }


def history(code):
    return HistoryResponse(
        task_code=code,
        events=[HistoryEvent(task_code=code, field_code="workflow_status",
                             old_value="In Progress", new_value="Done",
                             changed_at="2026-10-21T10:00:00+00:00")],
        page_info={"complete": True, "has_next": False},
    )


@pytest.mark.asyncio
async def test_facade_passes_plain_args_and_returns_safe_counts(monkeypatch):
    sprint = AsyncMock(return_value=complete_sprint())
    task_history = AsyncMock(side_effect=lambda code: history(code))
    monkeypatch.setattr(swtr_read, "get_sprint_tasks", sprint)
    monkeypatch.setattr(swtr_read, "get_task_history", task_history)

    result = await swtr_read.get_sprint_forecast_source_evidence("PRD-SPRNT-1", max_tasks=100)
    assert result == {
        "sprint_id": "PRD-SPRNT-1", "source": "REAL_AS21", "complete": True,
        "membership_proven": True, "task_count": 2,
        "history_complete_count": 2, "scope": "sprint_only",
        "forecast": None, "committed_predictability": None,
    }
    assert sprint.await_args.kwargs == {
        "sprint_id": "PRD-SPRNT-1", "space": None, "page": 0,
        "limit": 100, "complete": True, "include_task_type": False,
        "max_pages": 10,
    }
    assert task_history.await_count == 2
    assert "history_by_task" not in result


@pytest.mark.asyncio
async def test_facade_incomplete_sprint_is_typed_422(monkeypatch):
    data = {**complete_sprint(), "complete": False}
    monkeypatch.setattr(swtr_read, "get_sprint_tasks", AsyncMock(return_value=data))
    get_history = AsyncMock()
    monkeypatch.setattr(swtr_read, "get_task_history", get_history)
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_forecast_source_evidence("PRD-SPRNT-1", max_tasks=100)
    assert err.value.status_code == 422
    assert err.value.detail["reason"] == "sprint_membership_incomplete"
    assert get_history.await_count == 0


@pytest.mark.asyncio
async def test_facade_invalid_sprint_does_not_touch_source(monkeypatch):
    get_sprint = AsyncMock()
    monkeypatch.setattr(swtr_read, "get_sprint_tasks", get_sprint)
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_forecast_source_evidence("../bad", max_tasks=100)
    assert err.value.status_code == 400
    get_sprint.assert_not_awaited()


@pytest.mark.asyncio
async def test_facade_bad_history_fails_closed(monkeypatch):
    monkeypatch.setattr(swtr_read, "get_sprint_tasks", AsyncMock(return_value=complete_sprint()))
    async def wrong_history(key):
        return HistoryResponse(task_code=key, events=[], page_info={"complete": False, "has_next": True})
    monkeypatch.setattr(swtr_read, "get_task_history", wrong_history)
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_forecast_source_evidence("PRD-SPRNT-1", max_tasks=100)
    assert err.value.status_code == 422
    assert err.value.detail["reason"] == "task_history_incomplete"
