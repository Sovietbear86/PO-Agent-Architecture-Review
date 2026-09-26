from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4CapabilityUnavailable
from po_agent.harness.v4_plugin_registry import discover_v4_plugins
from po_agent.harness.v4_plugins.wave_batch6_release_forecast import build_release_forecast


def _status(value: str):
    return SimpleNamespace(value=value)


def _task(
    key: str,
    *,
    completed: bool,
    created_at: datetime,
    closed_at: datetime | None = None,
    resolved_at: datetime | None = None,
):
    return SimpleNamespace(
        key=key,
        title=key,
        is_completed=completed,
        is_open=not completed,
        is_blocked=False,
        status_raw="Closed" if completed else "In progress",
        status=_status("Closed" if completed else "In progress"),
        created_at=created_at,
        updated_at=closed_at or created_at,
        closed_at=closed_at,
        resolved_at=resolved_at,
    )


class FakeAdapter:
    def __init__(self, tasks):
        self.tasks = list(tasks)

    async def get_release_tasks(self, release_id: str, space: str | None = None):
        return list(self.tasks)


def _runtime(tasks):
    return SimpleNamespace(adapter=FakeAdapter(tasks))


def test_release_forecast_plugin_is_registry_discovered():
    registry = discover_v4_plugins()
    assert "builtin.batch6.release_forecast" in registry.plugin_ids
    ids = {skill.id for skill in registry.skills()}
    assert "release.forecast" in ids


def test_release_forecast_fails_closed_without_authoritative_membership():
    with pytest.raises(V4CapabilityUnavailable, match="release-to-task membership"):
        asyncio.run(
            build_release_forecast(_runtime([]))(
                {"space": "WMB", "release_id": "r1"}
            )
        )


def test_release_forecast_never_uses_updated_at_as_completion_proxy():
    created = datetime(2026, 9, 1, tzinfo=timezone.utc)
    tasks = [
        _task("WMB-1", completed=True, created_at=created),
        _task("WMB-2", completed=True, created_at=created),
        _task("WMB-3", completed=False, created_at=created),
    ]
    with pytest.raises(V4CapabilityUnavailable, match="at least two completed release tasks"):
        asyncio.run(
            build_release_forecast(_runtime(tasks))(
                {"space": "WMB", "release_id": "r1"}
            )
        )


def test_release_forecast_projects_from_authoritative_completion_history():
    created = datetime(2026, 9, 1, tzinfo=timezone.utc)
    tasks = [
        _task(
            "WMB-1",
            completed=True,
            created_at=created,
            closed_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
        ),
        _task(
            "WMB-2",
            completed=True,
            created_at=created,
            resolved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
        ),
        _task("WMB-3", completed=False, created_at=created),
        _task("WMB-4", completed=False, created_at=created),
    ]

    result = asyncio.run(
        build_release_forecast(_runtime(tasks))(
            {"space": "WMB", "release_id": "r1"}
        )
    )

    assert result.data["state"] == "FORECAST"
    assert result.data["total_tasks"] == 4
    assert result.data["completed_tasks"] == 2
    assert result.data["remaining_tasks"] == 2
    assert result.data["completed_tasks_with_authoritative_timestamp"] == 2
    assert result.data["observation_days"] == 10.0
    assert result.data["observed_throughput_tasks_per_day"] == 0.2
    assert result.data["forecast_days_remaining"] == 10.0
    assert result.data["method"] == "linear_task_throughput_v1"
    assert result.data["completion_timestamp_policy"] == "closed_at_or_resolved_at_only"
    assert "forecast_is_operational_projection_not_commitment" in result.warnings


def test_release_forecast_completed_release_returns_actual_completion_not_projection():
    created = datetime(2026, 9, 1, tzinfo=timezone.utc)
    tasks = [
        _task(
            "WMB-1",
            completed=True,
            created_at=created,
            closed_at=datetime(2026, 9, 6, tzinfo=timezone.utc),
        ),
        _task(
            "WMB-2",
            completed=True,
            created_at=created,
            resolved_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
        ),
    ]

    result = asyncio.run(
        build_release_forecast(_runtime(tasks))(
            {"space": "WMB", "release_id": "r1"}
        )
    )

    assert result.data["state"] == "COMPLETED"
    assert result.data["forecast_kind"] == "actual_completion"
    assert result.data["method"] == "authoritative_latest_completion_timestamp"
    assert result.data["forecast_date"].startswith("2026-09-11")


def test_release_forecast_completion_contract_requires_terminal_forecast_fields():
    registry = discover_v4_plugins()
    skill = next(skill for skill in registry.skills() if skill.id == "release.forecast")
    req = skill.completion[0]
    assert req.capability_id == "release.forecast"
    assert req.data_keys == ("release_id", "state", "forecast_date", "method")
