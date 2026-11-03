"""Verify source-declared current workflow status types in one complete sprint read.

Pure internal preflight: never infer statusType from display status names or
completion counts. The returned map is not a public API response. The local
observation timestamp is captured separately by the bounded collector; it is
NOT an AS21 transaction/snapshot token.
"""
from __future__ import annotations

from typing import Any

from .sprint_forecast_source import validate_complete_sprint_collection


def extract_sprint_current_status_types(
    sprint_payload: dict[str, Any], *, max_tasks: int = 100,
) -> dict[str, str]:
    """Extract exactly source-declared types for every canonical member.

    Only source_data.swtr_attributes[code=workflow_status].value.statusType
    is accepted, matching the canonical row from the existing read-only route.
    Duplicate identical source attributes are tolerated, conflicts fail closed.
    """
    if not isinstance(sprint_payload, dict):
        raise ValueError("sprint_source_malformed")
    tasks = validate_complete_sprint_collection(sprint_payload, max_tasks=max_tasks)
    result: dict[str, str] = {}
    for task in tasks:
        task_key = task["source_id"]
        attrs = task["source_data"].get("swtr_attributes")
        if not isinstance(attrs, list):
            raise ValueError("current_status_source_missing")
        candidates: set[str] = set()
        for item in attrs:
            if not isinstance(item, dict):
                raise ValueError("current_status_source_malformed")
            if item.get("code") != "workflow_status":
                continue
            value = item.get("value")
            if not isinstance(value, dict):
                raise ValueError("current_status_type_unverified")
            declared = value.get("statusType")
            if isinstance(declared, dict):
                declared = declared.get("code")
            if not isinstance(declared, str) or not declared or declared != declared.strip():
                raise ValueError("current_status_type_unverified")
            candidates.add(declared)
        if not candidates:
            raise ValueError("current_status_type_unverified")
        if len(candidates) != 1:
            raise ValueError("current_status_type_conflict")
        result[task_key] = next(iter(candidates))
    return result
