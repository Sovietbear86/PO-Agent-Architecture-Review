"""Route-level scalar DTO and early fail-closed contract; offline, no MCP."""
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.routers import swtr_read


def directory(complete=True):
    return {"source": "REAL_AS21", "complete": complete, "sprints": [
        {"code": "PRD-SPRNT-1", "start_at": "2026-10-19T00:00:00Z",
         "finish_at": "2026-10-30T23:00:00Z"},
    ]}


def proof():
    return {
        "sprint_id": "PRD-SPRNT-1", "status": "SOURCE_PROVEN", "source": "REAL_AS21",
        "scope_total": 6, "closed_total": 4,
        "snapshot_observed_at": "2026-10-27T12:00:00+00:00",
        "closed_at_by_task": {
            f"PRD-{i}": f"2026-10-{19 + i}T10:00:00+00:00"
            for i in range(1, 5)
        },
        "history_by_task": {"PRIVATE-RAW": [{"actor": "never send"}]},
    }


@pytest.mark.asyncio
async def test_route_source_proven_scalar_and_no_raw_fields(monkeypatch):
    sprint_dir = AsyncMock(return_value=directory())
    monkeypatch.setattr(swtr_read, "list_space_sprints", sprint_dir)
    from app.services import sprint_forecast_pipeline
    source = AsyncMock(return_value=proof())
    monkeypatch.setattr(sprint_forecast_pipeline, "collect_and_project_sprint_closures", source)
    output = await swtr_read.get_sprint_delivery_forecast("PRD-SPRNT-1")
    assert output["status"] == "READY"
    assert output["forecast_completion_percent"] is not None
    assert output["committed_predictability"] is None
    assert output["source"] == "REAL_AS21"
    assert "closed_at_by_task" not in output
    assert "history_by_task" not in output
    assert "current_status_types" not in output
    assert "snapshot_observed_at" not in output
    assert sprint_dir.await_args.kwargs["space"] == "PRD"
    assert source.await_args.kwargs["concurrency"] == 5
    assert source.await_args.kwargs["max_tasks"] == 100


@pytest.mark.asyncio
async def test_route_invalid_id_does_not_query_source(monkeypatch):
    reader = AsyncMock()
    monkeypatch.setattr(swtr_read, "list_space_sprints", reader)
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_delivery_forecast("../ALL")
    assert err.value.status_code == 400
    reader.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_incomplete_directory_is_typed_failure(monkeypatch):
    monkeypatch.setattr(swtr_read, "list_space_sprints", AsyncMock(return_value=directory(False)))
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_delivery_forecast("PRD-SPRNT-1")
    assert err.value.status_code == 422
    assert err.value.detail["reason"] == "sprint_period_source_incomplete"


@pytest.mark.asyncio
async def test_route_source_validation_error_is_unknown_not_zero(monkeypatch):
    monkeypatch.setattr(swtr_read, "list_space_sprints", AsyncMock(return_value=directory()))
    from app.services import sprint_forecast_pipeline
    monkeypatch.setattr(
        sprint_forecast_pipeline, "collect_and_project_sprint_closures",
        AsyncMock(side_effect=ValueError("status_transition_outside_snapshot")),
    )
    output = await swtr_read.get_sprint_delivery_forecast("PRD-SPRNT-1")
    assert output["status"] == "INSUFFICIENT_EVIDENCE"
    assert output["forecast_completion_percent"] is None
    assert output["reason"] == "status_transition_outside_snapshot"


@pytest.mark.asyncio
async def test_route_missing_sprint_dates_never_calculates(monkeypatch):
    data = directory()
    data["sprints"][0]["finish_at"] = None
    monkeypatch.setattr(swtr_read, "list_space_sprints", AsyncMock(return_value=data))
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_sprint_delivery_forecast("PRD-SPRNT-1")
    assert err.value.status_code == 422
    assert err.value.detail["reason"] == "sprint_period_unverified"
