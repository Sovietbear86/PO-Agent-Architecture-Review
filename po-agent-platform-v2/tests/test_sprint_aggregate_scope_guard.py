"""A230R3.3 R2: avoid presenting within-sprint hours as lifetime totals."""
from datetime import date
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4NeedsClarification
from po_agent.harness.v4_plugins import time_accounting_aggregate as aggregate


def test_explicit_lifetime_filter_cannot_be_silently_dropped():
    for text in ("за всё время", "за все время", "lifetime", "all-time"):
        with pytest.raises(V4NeedsClarification):
            aggregate._assert_sprint_calendar_scope({"period": text})
    aggregate._assert_sprint_calendar_scope({"period": "текущий спринт"})


@pytest.mark.asyncio
async def test_sprint_aggregate_labels_date_scope(monkeypatch):
    async def context(*_):
        return ([SimpleNamespace(key="PAY-123")],
                date(2026, 10, 18), date(2026, 11, 1))

    async def worklogs(*_):
        return [
            {"id": "wl-1", "task_key": "PAY-123", "date": "2026-10-20",
             "duration_hours": 4.0,
             "user": {"external_id": "Ivanov.I.I"}},
            {"id": "wl-2", "task_key": "PAY-123", "date": "2026-10-01",
             "duration_hours": 10.0,
             "user": {"external_id": "Ivanov.I.I"}},
        ]

    monkeypatch.setattr(aggregate, "_sprint_context", context)
    monkeypatch.setattr(aggregate, "_bounded_worklogs", worklogs)
    result = await aggregate.build_sprint_time_spent(SimpleNamespace(adapter=None))(
        {"space": "PAY", "sprint_id": "PAY-SPRNT-5"}
    )
    assert result.data["total_hours"] == 4
    assert result.data["worklog_count"] == 1
    assert result.data["time_basis"] == "logged_on_within_sprint_dates"
    assert result.data["all_time_total"] is False
    assert result.data["outside_period_included"] is False
    assert "не сумма за всё время" in result.answer


@pytest.mark.asyncio
async def test_lifetime_request_does_not_read_task_worklogs(monkeypatch):
    async def no_context(*_):
        raise AssertionError("Must not query source on unsupported lifetime scope")
    monkeypatch.setattr(aggregate, "_sprint_context", no_context)
    with pytest.raises(V4NeedsClarification):
        await aggregate.build_sprint_time_spent(SimpleNamespace(adapter=None))(
            {"space": "PAY", "sprint_id": "PAY-SPRNT-5",
             "period": "за всё время"}
        )
