"""Owner-approved source-proven sprint forecast. Scalar-only presentation DTO.

No cross-package dependency on Agent Core; computes the exact conservative
observed-throughput formula used by po_agent.sprint.delivery_forecast.
Internal per-task history and closure mappings never leave this boundary.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from math import ceil
from pathlib import Path
from zoneinfo import ZoneInfo

from .sprint_forecast_policy import SprintForecastPolicy, validate_forecast_policy
from .sprint_forecast_pipeline import collect_and_project_sprint_closures


_POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "sprint_forecast_policy.json"


def approved_policy() -> SprintForecastPolicy:
    """Explicit owner-approved product policy; fail closed on missing/altered configuration."""
    try:
        raw = json.loads(_POLICY_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, dict) or raw.get("version") != 1 or raw.get("holidays_supported") is not False:
            raise ValueError("forecast_policy_unverified")
        if raw.get("method") != "observed_throughput_v1":
            raise ValueError("forecast_policy_method_unverified")
        owner, approved = raw["approved_by"], datetime.fromisoformat(raw["approved_on"])
        if not isinstance(owner, str) or not owner.startswith("Product Owner"):
            raise ValueError("forecast_policy_authority_missing")
        values = raw["terminal_status_types"]
        weekdays = raw["working_weekdays"]
        if not isinstance(values, list) or not isinstance(weekdays, list):
            raise ValueError("forecast_policy_schema_invalid")
        policy = SprintForecastPolicy(
            timezone_name=raw["timezone_name"],
            working_weekdays=tuple(weekdays),
            terminal_status_types=frozenset(values),
            authority=owner,
            approved_at=approved,
        )
        validate_forecast_policy(policy)
        return policy
    except (OSError, KeyError, ValueError, TypeError) as exc:
        raise ValueError("forecast_policy_unavailable") from exc


def workdays(start: date, end: date, weekdays: tuple[int, ...]) -> int:
    if end < start:
        return 0
    return sum((start + timedelta(days=i)).weekday() in weekdays
               for i in range((end - start).days + 1))


def scalar_delivery_forecast(
    proof: dict, *, sprint_id: str, start: date, end: date, policy: SprintForecastPolicy,
) -> dict:
    """Strict source-gated forecast; never include task keys, histories or PII."""
    zone, weekdays, _ = validate_forecast_policy(policy)
    def stop(reason: str) -> dict:
        return {
            "sprint_id": sprint_id, "status": "INSUFFICIENT_EVIDENCE",
            "reason": reason, "forecast_completion_percent": None,
            "forecast_closed_by_end": None, "observed_tasks_per_workday": None,
            "source": "REAL_AS21", "committed_predictability": None,
            "method": "observed_throughput_v1",
        }
    if (not isinstance(proof, dict) or proof.get("status") != "SOURCE_PROVEN"
            or proof.get("source") != "REAL_AS21" or proof.get("sprint_id") != sprint_id):
        return stop("forecast_provenance_unverified")
    if not isinstance(start, date) or not isinstance(end, date) or start > end:
        return stop("invalid_sprint_dates")
    as_of_raw = proof.get("snapshot_observed_at")
    try:
        as_of = datetime.fromisoformat(as_of_raw)
    except (TypeError, ValueError):
        return stop("sprint_snapshot_unverified")
    if as_of.tzinfo is None:
        return stop("sprint_snapshot_timezone_missing")
    now = as_of.astimezone(zone).date()
    if now < start:
        return stop("sprint_not_started")
    count, closed = proof.get("scope_total"), proof.get("closed_total")
    if type(count) is not int or type(closed) is not int or count <= 0 or not 0 <= closed <= count:
        return stop("invalid_scope_counts")
    closes = proof.get("closed_at_by_task")
    if not isinstance(closes, dict) or len(closes) != closed:
        return stop("closure_count_mismatch")
    for key, raw in closes.items():
        if not isinstance(key, str) or not key or not isinstance(raw, str):
            return stop("closure_evidence_invalid")
        try:
            timestamp = datetime.fromisoformat(raw)
        except ValueError:
            return stop("closure_evidence_invalid")
        if timestamp.tzinfo is None or timestamp > as_of or not start <= timestamp.astimezone(zone).date() <= end:
            return stop("closure_out_of_scope")
    elapsed = workdays(start, min(now, end), weekdays)
    remaining = workdays(min(now, end) + timedelta(days=1), end, weekdays)
    if elapsed < 3 and closed < count:
        return stop("insufficient_observation_window")
    if closed < 3:
        return stop("insufficient_closure_events")
    rate = closed / elapsed if elapsed > 0 else 0
    if rate <= 0:
        return stop("invalid_observed_rate")
    open_count = count - closed
    projection = min(count, closed + min(open_count, rate * remaining))
    return {
        "sprint_id": sprint_id,
        "status": "READY",
        "reason": None,
        "method": "observed_throughput_v1",
        "source": "REAL_AS21",
        "as_of": as_of.astimezone(zone).isoformat(),
        "sprint_start": start.isoformat(),
        "sprint_end": end.isoformat(),
        "scope_total": count,
        "closed_total": closed,
        "open_count": open_count,
        "elapsed_workdays": elapsed,
        "remaining_workdays": remaining,
        "observed_tasks_per_workday": round(rate, 4),
        "eta_workdays": ceil(open_count / rate) if open_count else 0,
        "forecast_closed_by_end": round(projection, 2),
        "forecast_completion_percent": round(100 * projection / count, 1),
        "forecast_scope_kind": "current_scope_not_committed",
        "committed_predictability": None,
        "confidence_state": "heuristic_no_probability_claim",
        "calendar_note": "Mon-Fri; holidays excluded only as non-working weekends",
    }
