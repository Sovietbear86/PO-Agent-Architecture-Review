from datetime import datetime, timedelta

import pytest

from po_agent.adapters.fake import FakeAS21Adapter
from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.historical_wiring import enable_historical_skills
from po_agent.harness.runtime import HarnessRuntime
from po_agent.harness.source_contracts import ReleaseTimelinePoint, SprintScopeSnapshot


class Snapshots:
    async def get_commitment_snapshot(self, sprint_id: str):
        if sprint_id == "WMB-SPRNT-1":
            return SprintScopeSnapshot(
                sprint_id=sprint_id,
                captured_at=datetime(2026, 8, 1, 9, 0, 0),
                task_keys=("WMB-101", "WMB-102", "WMB-999"),
            )
        return None


class Timeline:
    async def get_timeline(self, release_id: str):
        if release_id != "WMB-2024-Q3":
            return ()
        now = datetime(2026, 8, 10, 12, 0, 0)
        return (
            ReleaseTimelinePoint(release_id, now - timedelta(days=4), completed=0, total=3),
            ReleaseTimelinePoint(release_id, now, completed=1, total=3),
        )


@pytest.mark.asyncio
async def test_carryover_uses_commitment_snapshot_and_current_completion_state():
    runtime = enable_historical_skills(HarnessRuntime(FakeAS21Adapter()), sprint_snapshots=Snapshots())
    response = await runtime.process(HarnessRequest(query="Покажи carryover WMB-SPRNT-1"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "sprint-carryover"
    assert response.data["carryover_task_keys"] == ["WMB-102"]
    assert response.data["missing_from_current_scope"] == ["WMB-999"]
    assert "committed_tasks_missing_from_current_scope" in response.warnings


@pytest.mark.asyncio
async def test_scope_change_is_set_difference_against_commitment_snapshot():
    runtime = enable_historical_skills(HarnessRuntime(FakeAS21Adapter()), sprint_snapshots=Snapshots())
    response = await runtime.process(HarnessRequest(query="Изменение scope WMB-SPRNT-1"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "sprint-scope-change"
    assert response.data["added"] == []
    assert response.data["removed"] == ["WMB-999"]
    assert response.data["scope_change_percent"] == 33.3


@pytest.mark.asyncio
async def test_release_forecast_is_bounded_and_uses_observed_rate_only():
    runtime = enable_historical_skills(HarnessRuntime(FakeAS21Adapter()), release_timeline=Timeline())
    response = await runtime.process(HarnessRequest(query="Дай прогноз WMB-2024-Q3"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "release-forecast"
    assert response.data["bounded"] is True
    assert response.data["observed_rate_tasks_per_day"] == 0.25
    assert response.data["remaining_tasks"] == 2
    assert response.data["forecast_date"] == "2026-08-18"
    assert "forecast_is_linear_observed_rate_not_commitment" in response.warnings


@pytest.mark.asyncio
async def test_release_forecast_refuses_when_timeline_is_insufficient():
    class EmptyTimeline:
        async def get_timeline(self, release_id: str):
            return ()

    runtime = enable_historical_skills(HarnessRuntime(FakeAS21Adapter()), release_timeline=EmptyTimeline())
    response = await runtime.process(HarnessRequest(query="Прогноз WMB-2024-Q3"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.data["forecast_date"] is None
    assert "insufficient_release_timeline" in response.warnings
