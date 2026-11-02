"""Pure validation for authoritative sprint closure facts.

The read-only facade collects complete sprint membership and complete per-task
workflow history separately. This module does NOT invent task status, dates,
business calendars, sprint baseline or throughput.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from typing import Any


def validate_complete_sprint_collection(payload: dict[str, Any], *, max_tasks: int = 100) -> list[dict[str, Any]]:
    """Fail closed on incomplete or ambiguous sprint membership."""
    if payload.get("complete") is not True or payload.get("membership_proven") is not True:
        raise ValueError("sprint_membership_incomplete")
    tasks = payload.get("complete_tasks")
    if not isinstance(tasks, list) or len(tasks) > max_tasks:
        raise ValueError("sprint_membership_over_limit")
    seen: set[str] = set()
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("invalid_task")
        key = task.get("source_id")
        if not isinstance(key, str) or not key or key in seen:
            raise ValueError("duplicate_or_missing_task_id")
        source_data = task.get("source_data")
        if not isinstance(source_data, dict) or source_data.get("sprint_membership_proven") is not True:
            raise ValueError("task_sprint_membership_unproven")
        seen.add(key)
    return tasks


def complete_workflow_history(payload: dict[str, Any], task_key: str) -> list[dict[str, Any]]:
    """Verify source completeness, task identity and tz-aware workflow dates."""
    if not isinstance(payload, dict) or payload.get("task_code") != task_key:
        raise ValueError("task_history_identity_mismatch")
    page = payload.get("page_info")
    if not isinstance(page, dict) or page.get("complete") is not True or page.get("has_next") is not False:
        raise ValueError("task_history_incomplete")
    events = payload.get("events")
    if not isinstance(events, list):
        raise ValueError("invalid_task_history")
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for event in events:
        if not isinstance(event, dict) or event.get("task_code") != task_key:
            raise ValueError("invalid_history_event")
        if event.get("field_code") != "workflow_status":
            continue
        raw = event.get("changed_at")
        if not isinstance(raw, str):
            raise ValueError("missing_closure_timestamp")
        try:
            ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("invalid_closure_timestamp") from exc
        if ts.tzinfo is None:
            raise ValueError("history_timezone_missing")
        event_id = event.get("event_id")
        if event_id is None:
            # AS21 history rows may have no source event ID. This is explicitly
            # a LOCAL deduplication key, not a claimed source identifier.
            # Identical timestamp+transition pairs are ambiguous: fail closed.
            old_status, new_status = event.get("old_value"), event.get("new_value")
            if not all(isinstance(v, str) and v for v in (old_status, new_status)):
                raise ValueError("status_event_identity_unverified")
            signature = "\\x1f".join((task_key, ts.isoformat(), old_status, new_status))
            event_id = "local:" + sha256(signature.encode("utf-8")).hexdigest()
        if not isinstance(event_id, str) or not event_id or event_id in seen:
            raise ValueError("duplicate_status_event")
        seen.add(event_id)
        # Neither 'updated_at' nor a guessed closed status is treated as closure.
        out.append({"event_id": event_id, "event_identity_source": "local" if event_id.startswith("local:") else "source",
                    "changed_at": ts.isoformat(),
                    "from_name": event.get("old_value"),
                    "to_name": event.get("new_value"),
                    "from_status_type": event.get("from_status_type"),
                    "to_status_type": event.get("to_status_type")})
    return out
