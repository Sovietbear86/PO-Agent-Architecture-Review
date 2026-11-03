"""Pure adapter from validated source closure evidence to Delivery Forecast.

This does NOT fetch AS21, infer terminal statuses, approve business calendars,
wire any V4 capability, or make a committed-scope Predictability claim.
Evidence must be produced by a separate authoritative, complete source gate.
"""
from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .delivery_forecast import SprintForecastInput, forecast_sprint


def forecast_from_proven_closures(
    proof: dict[str, Any],
    *,
    sprint_start: date,
    sprint_end: date,
    as_of: datetime,
    product_timezone: str,
    working_weekdays: tuple[int, ...],
    expected_sprint_id: str | None = None,
) -> dict[str, Any]:
    """Project complete source-proven closures into a typed heuristic forecast.

    Fails closed with a *typed, no-forecast* result on missing evidence/config.
    The caller must independently authorize terminal types before producing
    `proof`; this function cannot establish that authorization.
    """
    def incomplete(reason: str) -> dict[str, Any]:
        return {"status": "INSUFFICIENT_EVIDENCE", "reason": reason,
                "method": "observed_throughput_v1", "forecast": None,
                "committed_predictability": None}

    if not isinstance(proof, dict) or proof.get("status") != "SOURCE_PROVEN" or proof.get("source") != "REAL_AS21":
        return incomplete("closure_provenance_missing")
    sprint_id = proof.get("sprint_id")
    if not isinstance(sprint_id, str) or not re.fullmatch(
        r"[A-Z][A-Z0-9_-]*-SPRNT-[0-9]+", sprint_id, flags=re.IGNORECASE
    ):
        return incomplete("sprint_identity_unverified")
    if expected_sprint_id is not None and (
        not isinstance(expected_sprint_id, str)
        or sprint_id.upper() != expected_sprint_id.upper()
    ):
        return incomplete("sprint_identity_mismatch")
    if not isinstance(sprint_start, date) or isinstance(sprint_start, datetime):
        return incomplete("invalid_sprint_dates")
    if not isinstance(sprint_end, date) or isinstance(sprint_end, datetime):
        return incomplete("invalid_sprint_dates")
    if not isinstance(as_of, datetime) or as_of.tzinfo is None:
        return incomplete("timezone_missing")
    if not isinstance(product_timezone, str) or not product_timezone:
        return incomplete("product_timezone_unconfigured")
    try:
        timezone = ZoneInfo(product_timezone)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        return incomplete("product_timezone_invalid")
    if (not isinstance(working_weekdays, tuple) or not working_weekdays
            or any(type(day) is not int or day not in range(7) for day in working_weekdays)
            or len(set(working_weekdays)) != len(working_weekdays)):
        return incomplete("working_calendar_unverified")
    count, closed = proof.get("scope_total"), proof.get("closed_total")
    if type(count) is not int or type(closed) is not int or count < 0 or not 0 <= closed <= count:
        return incomplete("invalid_scope_counts")
    timestamps = proof.get("closed_at_by_task")
    if not isinstance(timestamps, dict) or len(timestamps) != closed:
        return incomplete("closure_count_mismatch")
    parsed: list[datetime] = []
    for key, timestamp in timestamps.items():
        if not isinstance(key, str) or not key or not isinstance(timestamp, str):
            return incomplete("closure_evidence_malformed")
        try:
            value = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return incomplete("closure_evidence_malformed")
        if value.tzinfo is None:
            return incomplete("closure_timezone_missing")
        parsed.append(value)
    result = forecast_sprint(SprintForecastInput(
        sprint_key=sprint_id,
        sprint_start=sprint_start,
        sprint_end=sprint_end,
        as_of=as_of.astimezone(timezone),
        scope_total=count,
        closed_total=closed,
        closed_at=tuple(parsed),
        complete_membership=True,
        complete_closure_timestamps=True,
        working_weekdays=working_weekdays,
        source="REAL_AS21",
    ))
    result["committed_predictability"] = None
    return result
