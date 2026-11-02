"""Source-to-forecast projection preflight. No baseline or calculated forecast.

Only source-verified lifecycle transitions may contribute completed dates. All
statuses must be classified through explicit source statusType bindings, not
human-language status labels or updated_at. The caller must supply canonical
present status type for each task and a bound, complete history from collector.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def verify_forecast_closure_inputs(
    evidence: dict[str, Any],
    *,
    current_status_types: dict[str, str],
    terminal_status_types: frozenset[str],
    event_status_types: dict[str, dict[str, str]],
    as_of: datetime,
) -> dict[str, Any]:
    """Validate exact current task scope and authoritative closure events.

    event_status_types: task_key -> {event_id -> authoritative resulting statusType}.
    This explicit mapping prevents guessing based on localized workflow labels.
    """
    if not isinstance(evidence, dict) or evidence.get("complete") is not True:
        raise ValueError("forecast_source_incomplete")
    if evidence.get("source") != "REAL_AS21" or evidence.get("membership_proven") is not True:
        raise ValueError("forecast_source_not_authoritative")
    histories = evidence.get("history_by_task")
    if not isinstance(histories, dict) or evidence.get("task_count") != len(histories):
        raise ValueError("forecast_scope_mismatch")
    if evidence.get("history_complete_count") != len(histories):
        raise ValueError("forecast_history_incomplete")
    if as_of.tzinfo is None:
        raise ValueError("forecast_as_of_timezone_missing")
    if (not isinstance(terminal_status_types, frozenset)
            or not terminal_status_types
            or any(not isinstance(t, str) or not t for t in terminal_status_types)):
        raise ValueError("terminal_status_contract_missing")
    if not isinstance(current_status_types, dict) or set(current_status_types) != set(histories):
        raise ValueError("current_status_contract_incomplete")
    if not isinstance(event_status_types, dict) or set(event_status_types) != set(histories):
        raise ValueError("event_status_contract_incomplete")

    resolved: dict[str, str] = {}
    for task_key, events in histories.items():
        if not isinstance(task_key, str) or not isinstance(events, list):
            raise ValueError("invalid_forecast_history")
        current = current_status_types[task_key]
        if not isinstance(current, str) or not current:
            raise ValueError("current_status_unverified")
        event_types = event_status_types[task_key]
        if not isinstance(event_types, dict):
            raise ValueError("event_status_contract_incomplete")
        if not events:
            # A terminal task with no source-proven closure cannot be projected.
            if current in terminal_status_types:
                raise ValueError("terminal_closure_event_missing")
            if event_types:
                raise ValueError("event_status_contract_mismatch")
            continue

        last_event_time: datetime | None = None
        last_type: str | None = None
        last_terminal_at: datetime | None = None
        seen_events: set[str] = set()
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("invalid_forecast_history")
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id or event_id in seen_events:
                raise ValueError("status_event_identity_unverified")
            seen_events.add(event_id)
            status_type = event_types.get(event_id)
            if not isinstance(status_type, str) or not status_type:
                raise ValueError("status_transition_type_unverified")
            try:
                timestamp = datetime.fromisoformat(str(event["changed_at"]).replace("Z", "+00:00"))
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError("invalid_status_transition_timestamp") from exc
            if timestamp.tzinfo is None or timestamp > as_of:
                raise ValueError("status_transition_outside_snapshot")
            if last_event_time is not None and timestamp <= last_event_time:
                raise ValueError("status_transition_order_unverified")
            last_event_time, last_type = timestamp, status_type
            if status_type in terminal_status_types:
                last_terminal_at = timestamp
            else:
                last_terminal_at = None  # reopened task invalidates prior closure

        if last_type != current:
            raise ValueError("current_status_history_mismatch")
        if current in terminal_status_types:
            if last_terminal_at is None:
                raise ValueError("terminal_closure_event_missing")
            resolved[task_key] = last_terminal_at.isoformat()

    return {
        "status": "SOURCE_PROVEN",
        "source": "REAL_AS21",
        "sprint_id": evidence.get("sprint_id"),
        "scope_total": len(histories),
        "closed_total": len(resolved),
        # Internal only: caller must never send this keyed map directly to UI.
        "closed_at_by_task": resolved,
        "committed_predictability": None,
        "forecast": None,
    }


def bind_source_status_types(
    evidence: dict[str, Any],
    *,
    current_status_types: dict[str, str],
    terminal_status_types: frozenset[str],
    as_of: datetime,
) -> dict[str, Any]:
    """Bind already-proven AS21 per-event types into the existing projector.

    Types are exact, source-declared values (including lowercase). No name
    inference and no guessed terminal set. Missing statusType fails closed.
    The returned closed_at_by_task mapping is INTERNAL, never UI-facing.
    """
    if not isinstance(evidence, dict) or not isinstance(evidence.get("history_by_task"), dict):
        raise ValueError("forecast_source_incomplete")
    if not isinstance(terminal_status_types, frozenset) or not terminal_status_types:
        raise ValueError("terminal_status_contract_missing")
    if not all(isinstance(x, str) and x and x == x.strip() for x in terminal_status_types):
        raise ValueError("terminal_status_contract_invalid")
    event_types: dict[str, dict[str, str]] = {}
    for task_key, events in evidence["history_by_task"].items():
        if not isinstance(task_key, str) or not isinstance(events, list):
            raise ValueError("invalid_forecast_history")
        mapped: dict[str, str] = {}
        for event in events:
            if not isinstance(event, dict):
                raise ValueError("invalid_forecast_history")
            event_id = event.get("event_id")
            declared = event.get("to_status_type")
            if not isinstance(event_id, str) or not event_id or event_id in mapped:
                raise ValueError("status_event_identity_unverified")
            if not isinstance(declared, str) or not declared or declared != declared.strip():
                raise ValueError("status_transition_type_unverified")
            mapped[event_id] = declared
        event_types[task_key] = mapped
    return verify_forecast_closure_inputs(
        evidence,
        current_status_types=current_status_types,
        terminal_status_types=terminal_status_types,
        event_status_types=event_types,
        as_of=as_of,
    )
