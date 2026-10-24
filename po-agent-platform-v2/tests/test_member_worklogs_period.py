"""A230R3.1: source-filtered member/date worklog plugin tests (no REAL AS21 writes)."""
from datetime import date
from types import SimpleNamespace

import pytest

from po_agent.harness.agent_core_v4 import V4NeedsClarification, V4CapabilityUnavailable
from po_agent.harness.v4_plugins.time_accounting_period import (
    parse_worklog_period, build_member_worklogs_period,
)


@pytest.mark.parametrize("period,expected", [
    ("за 2 недели", ("2026-10-11", "2026-10-24")),
    ("за последние 2 недели", ("2026-10-11", "2026-10-24")),
    ("последние 3 недели", ("2026-10-04", "2026-10-24")),
    ("за 14 дней", ("2026-10-11", "2026-10-24")),
    ("с 21.09.2026 по сегодня", ("2026-09-21", "2026-10-24")),
    ("сегодня", ("2026-10-24", "2026-10-24")),
    ("вчера", ("2026-10-23", "2026-10-23")),
    ("за неделю", ("2026-10-18", "2026-10-24")),
    ("последняя неделя", ("2026-10-18", "2026-10-24")),
    ("за месяц", ("2026-09-25", "2026-10-24")),
    ("этот месяц", ("2026-10-01", "2026-10-24")),
])
def test_relative_and_explicit_dates(period, expected):
    assert parse_worklog_period({"period": period}, date(2026, 10, 24)) == expected


@pytest.mark.parametrize("period", ["за 400 дней", "за 0 недель", "январь", "когда-нибудь"])
def test_ambiguous_or_unsafe_period_is_typed_clarification(period):
    with pytest.raises(V4NeedsClarification):
        parse_worklog_period({"period": period}, date(2026, 10, 24))


def test_explicit_dates_take_precedence():
    args = {"period": "за 2 недели", "date_from": "2026-10-01", "date_to": "сегодня"}
    assert parse_worklog_period(args, date(2026, 10, 24)) == ("2026-10-01", "2026-10-24")


@pytest.mark.asyncio
async def test_member_author_scoped_source_with_complete_zero():
    called = {}
    class Adapter:
        async def get_member_worklogs_period(self, member, begin, end, **kwargs):
            called.update(member=member, begin=begin, end=end, **kwargs)
            return {"member_login": member, "date_from":begin,"date_to":end,
                    "source":"REAL_AS21", "complete":True, "entries":[],
                    "worklog_count":0, "total_hours":0.0}
    handler = build_member_worklogs_period(SimpleNamespace(adapter=Adapter()))
    response = await handler({"member_login":"Ivanov.I.I", "date_from":"2026-10-01",
                              "date_to":"2026-10-23","space":"PAY"})
    assert called["space"] == "PAY"
    assert called["member"] == "Ivanov.I.I"
    assert response.data["complete"] is True
    assert response.data["worklog_count"] == 0
    assert len(response.evidence) == 1


@pytest.mark.asyncio
async def test_member_incomplete_report_rejected():
    class Adapter:
        async def get_member_worklogs_period(self, *a, **kw):
            return {"complete":False, "source":"REAL_AS21", "entries":[],
                    "worklog_count":0, "total_hours":0}
    handler = build_member_worklogs_period(SimpleNamespace(adapter=Adapter()))
    with pytest.raises(V4CapabilityUnavailable):
        await handler({"member_login":"Ivanov.I.I","period":"за 2 недели"})
