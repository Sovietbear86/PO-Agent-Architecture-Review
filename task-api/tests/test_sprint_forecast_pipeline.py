"""Offline owner-policy-gated sprint closure projection. No AS21 requests."""
from datetime import datetime, timezone

import pytest

from app.services.sprint_forecast_pipeline import collect_and_project_sprint_closures
from app.services.sprint_forecast_policy import SprintForecastPolicy


def policy():
    # Test-only illustrative values. There is NO production authorization.
    return SprintForecastPolicy(
        timezone_name="Europe/Moscow",
        working_weekdays=(0, 1, 2, 3, 4),
        terminal_status_types=frozenset({"done"}),
        authority="synthetic-test-only",
        approved_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
    )


def row(key, status_type):
    return {
        "source_id": key,
        "status": "display label is not a statusType",
        "source_data": {
            "sprint_membership_proven": True,
            "swtr_attributes": [{
                "code": "workflow_status",
                "value": {"name": "untrusted localized label", "statusType": status_type},
            }],
        },
    }


def sprint(status1="done", status2="in_progress"):
    return {
        "sprint_id": "PRD-SPRNT-1", "complete": True,
        "membership_proven": True,
        "complete_tasks": [row("PRD-1", status1), row("PRD-2", status2)],
    }


def event(code, before, after, result_type, when):
    return {
        "task_code": code, "field_code": "workflow_status",
        "event_id": None, "old_value": before, "new_value": after,
        "to_status_type": result_type, "changed_at": when,
    }


def history(code, *, reopen=False, late=False, missing_type=False):
    if code == "PRD-1":
        events = [
            event(code, "Open", "In progress", "in_progress", "2026-10-20T09:00:00Z"),
            event(code, "In progress", "Resolved",
                  None if missing_type else "done",
                  "2100-10-21T09:00:00Z" if late else "2026-10-21T09:00:00Z"),
        ]
        if reopen:
            events.append(event(code, "Resolved", "In progress", "in_progress",
                                "2026-10-22T09:00:00Z"))
    else:
        events = [event(code, "Open", "In progress", "in_progress", "2026-10-20T08:00:00Z")]
    return {
        "task_code": code,
        "page_info": {"complete": True, "has_next": False},
        "events": events,
    }


async def run(*, approved=True, reopen=False, late=False, missing_type=False,
              missing_current=False, calls=None):
    calls = calls if calls is not None else []

    async def read_sprint(key):
        calls.append(("sprint", key))
        payload = sprint(status1="in_progress" if reopen else "done")
        if missing_current:
            payload["complete_tasks"][0]["source_data"]["swtr_attributes"] = []
        return payload

    async def read_history(key):
        calls.append(("history", key))
        return history(key, reopen=reopen, late=late, missing_type=missing_type)

    return await collect_and_project_sprint_closures(
        "PRD-SPRNT-1",
        policy=policy() if approved else None,
        read_sprint=read_sprint,
        read_history=read_history,
        max_tasks=3,
        concurrency=2,
    )


@pytest.mark.asyncio
async def test_complete_lowercase_source_evidence_produces_only_private_closures():
    calls = []
    proof = await run(calls=calls)
    assert proof["status"] == "SOURCE_PROVEN"
    assert proof["source"] == "REAL_AS21"
    assert proof["sprint_id"] == "PRD-SPRNT-1"
    assert proof["scope_total"] == 2
    assert proof["closed_total"] == 1
    assert list(proof["closed_at_by_task"]) == ["PRD-1"]
    assert proof["closed_at_by_task"]["PRD-1"] == "2026-10-21T09:00:00+00:00"
    assert proof["committed_predictability"] is None
    assert proof["forecast"] is None
    assert datetime.fromisoformat(proof["snapshot_observed_at"]).tzinfo is not None
    assert len([c for c in calls if c[0] == "sprint"]) == 1
    assert len([c for c in calls if c[0] == "history"]) == 2


@pytest.mark.asyncio
async def test_no_approved_policy_prevents_all_source_reads():
    calls = []
    with pytest.raises(ValueError, match="forecast_product_policy_missing"):
        await run(approved=False, calls=calls)
    assert calls == []


@pytest.mark.asyncio
async def test_reopen_is_not_counted_as_terminal():
    result = await run(reopen=True)
    assert result["status"] == "SOURCE_PROVEN"
    assert result["closed_total"] == 0
    assert result["closed_at_by_task"] == {}


@pytest.mark.asyncio
async def test_future_transition_must_not_be_counted():
    with pytest.raises(ValueError, match="status_transition_outside_snapshot"):
        await run(late=True)


@pytest.mark.asyncio
async def test_missing_authoritative_event_type_fails_closed():
    with pytest.raises(ValueError, match="status_transition_type_unverified"):
        await run(missing_type=True)


@pytest.mark.asyncio
async def test_missing_current_status_type_stops_before_history_reads():
    calls = []
    with pytest.raises(ValueError, match="current_status_type_unverified"):
        await run(missing_current=True, calls=calls)
    assert calls == [("sprint", "PRD-SPRNT-1")]
