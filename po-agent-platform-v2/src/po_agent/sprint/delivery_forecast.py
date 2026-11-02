"""Deterministic, source-gated sprint delivery forecast.

This is a pure calculator, NOT an AS21 reader and NOT committed predictability.
Callers must provide a complete, bounded sprint membership snapshot, verified
task resolution dates and authoritative sprint dates. No invented history or rates.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import ceil, isfinite
from typing import Literal


ForecastState = Literal["READY", "INSUFFICIENT_EVIDENCE", "SOURCE_UNAVAILABLE"]


@dataclass(frozen=True)
class SprintForecastInput:
    sprint_key: str
    sprint_start: date
    sprint_end: date
    as_of: datetime
    scope_total: int
    closed_total: int
    # Verified *per-task* closure timestamps for ALL tasks closed by as_of.
    closed_at: tuple[datetime, ...]
    complete_membership: bool
    complete_closure_timestamps: bool
    source: str = "REAL_AS21"
    # None = source did not provide a trustable working-day calendar.
    working_weekdays: tuple[int, ...] | None = None
    # Source outage is distinguishable from true zero.
    source_available: bool = True


def _workdays(start: date, end: date, weekdays: tuple[int, ...]) -> int:
    if end < start:
        return 0
    return sum((start + timedelta(days=i)).weekday() in weekdays
               for i in range((end - start).days + 1))


def _incomplete(reason: str, state: ForecastState = "INSUFFICIENT_EVIDENCE") -> dict:
    return {"status": state, "reason": reason, "forecast": None, "method": "observed_throughput_v1"}


def forecast_sprint(value: SprintForecastInput) -> dict:
    """Return a typed estimate; never fabricate committed baseline or confidence."""
    if not value.source_available:
        return _incomplete("source_unavailable", "SOURCE_UNAVAILABLE")
    if value.source != "REAL_AS21":
        return _incomplete("source_not_authoritative")
    if not value.complete_membership:
        return _incomplete("incomplete_sprint_membership")
    if not value.complete_closure_timestamps:
        return _incomplete("incomplete_closure_history")
    if value.working_weekdays is None or not value.working_weekdays or any(
        not isinstance(x, int) or isinstance(x, bool) or x not in range(7)
        for x in value.working_weekdays
    ):
        return _incomplete("working_calendar_unverified")
    if len(set(value.working_weekdays)) != len(value.working_weekdays):
        return _incomplete("working_calendar_invalid")
    if value.sprint_end < value.sprint_start:
        return _incomplete("invalid_sprint_dates")
    if value.as_of.tzinfo is None or any(x.tzinfo is None for x in value.closed_at):
        return _incomplete("timezone_missing")
    now = value.as_of.date()
    if now < value.sprint_start:
        return _incomplete("sprint_not_started")
    if value.scope_total < 0 or not 0 <= value.closed_total <= value.scope_total:
        return _incomplete("invalid_scope_counts")
    if len(value.closed_at) != value.closed_total:
        return _incomplete("closure_count_mismatch")
    # Compare closure calendar dates in the explicitly supplied as_of timezone.
    # Different UTC offsets must not change which product-local day was closed.
    local_closures = tuple(x.astimezone(value.as_of.tzinfo) for x in value.closed_at)
    if any(x > value.as_of or not (value.sprint_start <= x.date() <= value.sprint_end) for x in local_closures):
        return _incomplete("closure_out_of_scope")
    if value.scope_total == 0:
        return _incomplete("empty_sprint_scope")

    observed_until = min(now, value.sprint_end)
    elapsed = _workdays(value.sprint_start, observed_until, value.working_weekdays)
    remaining = _workdays(observed_until + timedelta(days=1),
                          value.sprint_end, value.working_weekdays)
    if elapsed == 0:
        return _incomplete("no_elapsed_workdays")
    if elapsed < 3 and value.closed_total < value.scope_total:
        return _incomplete("insufficient_observation_window")
    # No rate estimate without at least three observed closures; explicit zero
    # stays an observation, never a 0% prediction masquerading as certainty.
    if value.closed_total < 3:
        return _incomplete("insufficient_closure_events")

    rate = value.closed_total / elapsed
    if not isfinite(rate) or rate <= 0:
        return _incomplete("invalid_observed_rate")
    open_count = value.scope_total - value.closed_total
    predicted_new = min(open_count, rate * remaining)
    projected_closed = min(value.scope_total, value.closed_total + predicted_new)
    eta_workdays = ceil(open_count / rate) if open_count else 0
    return {
        "status": "READY",
        "reason": None,
        "method": "observed_throughput_v1",
        "source": value.source,
        "as_of": value.as_of.isoformat(),
        "sprint_key": value.sprint_key,
        "sprint_start": value.sprint_start.isoformat(),
        "sprint_end": value.sprint_end.isoformat(),
        "scope_total": value.scope_total,
        "closed_total": value.closed_total,
        "open_count": open_count,
        "elapsed_workdays": elapsed,
        "remaining_workdays": remaining,
        "observed_tasks_per_workday": round(rate, 4),
        "eta_workdays": eta_workdays,
        "forecast_closed_by_end": round(projected_closed, 2),
        "forecast_completion_percent": round(100 * projected_closed / value.scope_total, 1),
        "forecast_scope_kind": "current_scope_not_committed",
        "committed_predictability": None,
        "confidence_state": "heuristic_no_probability_claim",
    }
