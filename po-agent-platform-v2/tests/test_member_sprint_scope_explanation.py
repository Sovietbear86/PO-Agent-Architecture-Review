"""A230R3.3: sprint period claims must not imply lifetime task totals."""
from datetime import date
from types import SimpleNamespace

import pytest

from po_agent.harness.v4_plugins import time_accounting_member as accounting


@pytest.mark.asyncio
@pytest.mark.parametrize("builder", [
    accounting.build_member_time_spent,
    accounting.build_member_worklogs,
])
async def test_sprint_answer_discloses_calendar_scope(monkeypatch, builder):
    async def fake_context(_runtime, _args):
        tasks = [SimpleNamespace(key="PAY-123")]
        return ("Ivanov.I.I", "PAY", "PAY-SPRNT-5", tasks,
                date(2026, 10, 18), date(2026, 11, 1), [])
    monkeypatch.setattr(accounting, "_member_sprint_entries", fake_context)
    result = await builder(SimpleNamespace(adapter=None))({})
    assert "2026-10-18" in result.answer
    assert "2026-11-01" in result.answer
    assert "не учитываются" in result.answer
    assert result.data["time_basis"] == "logged_on_within_sprint_dates"
    assert result.data["outside_period_included"] is False
    assert result.data["sprint_task_count"] == 1
    assert result.data["total_hours"] == 0


def test_period_and_sprint_are_distinct_skills():
    from po_agent.harness.v4_plugins.time_accounting_period import PLUGIN as period
    from po_agent.harness.v4_plugins.time_accounting_member import PLUGIN as sprint
    assert period.plugin_id != sprint.plugin_id
    assert "member.worklogs_period" in {cap.id for cap in period.capabilities}
    assert "member.worklogs" in {cap.id for cap in sprint.capabilities}
