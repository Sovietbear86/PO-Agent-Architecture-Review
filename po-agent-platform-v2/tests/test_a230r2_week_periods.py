"""A230R2.1: deterministic week-period regression; no live AS21 required."""
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from po_agent.harness.v4_plugins._task_live_handlers import _parse_human_created_period

MSK = ZoneInfo("Europe/Moscow")


@pytest.mark.parametrize("phrase", [
    "за последнюю неделю",
    "последнюю неделю",
    "за последней неделе",
    "last week",
])
def test_rolling_week_is_seven_calendar_days_in_moscow(phrase):
    now = datetime(2026, 10, 22, 19, 30, tzinfo=MSK)
    start, end, kind = _parse_human_created_period(phrase, now=now)
    assert (start.isoformat(), end.isoformat(), kind) == (
        "2026-10-16T00:00:00+03:00",
        "2026-10-22T19:30:00+03:00",
        "last_7_calendar_days",
    )


@pytest.mark.parametrize("phrase", ["за прошлую неделю", "предыдущую неделю", "previous week"])
def test_previous_calendar_week_is_not_rolling_week(phrase):
    now = datetime(2026, 10, 22, 19, 30, tzinfo=MSK)
    start, end, kind = _parse_human_created_period(phrase, now=now)
    assert start.isoformat() == "2026-10-12T00:00:00+03:00"
    assert end.isoformat() == "2026-10-18T23:59:59.999999+03:00"
    assert kind == "previous_calendar_week"


def test_week_does_not_change_explicit_start_to_now():
    now = datetime(2026, 10, 22, 19, 30, tzinfo=MSK)
    start, end, kind = _parse_human_created_period("с 30.09.2026", now=now)
    assert start.isoformat() == "2026-09-30T00:00:00+03:00"
    assert end == now
    assert kind == "explicit_start_to_now"


def test_malformed_week_is_rejected():
    with pytest.raises(ValueError):
        _parse_human_created_period("за несуществующую неделю", now=datetime(2026, 10, 22, tzinfo=MSK))
