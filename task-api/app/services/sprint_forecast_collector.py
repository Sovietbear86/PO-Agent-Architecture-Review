"""Bounded read-only sprint closure evidence collector (not a forecast).

Dependency-injected source readers enable offline contract tests. Never infer
completion from updated_at or text status labels. Do not expose raw source rows.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from collections.abc import Awaitable, Callable
from typing import Any

from .sprint_forecast_snapshot import extract_sprint_current_status_types
from .sprint_forecast_source import (
    complete_workflow_history,
    validate_complete_sprint_collection,
)


async def collect_sprint_workflow_evidence(
    sprint_id: str,
    *,
    read_sprint: Callable[[str], Awaitable[dict[str, Any]]],
    read_history: Callable[[str], Awaitable[dict[str, Any]]],
    max_tasks: int = 100,
    concurrency: int = 5,
    timeout_seconds: float = 90.0,
    require_current_status_types: bool = False,
) -> dict[str, Any]:
    """Prove every task and every status history, else fail closed.

    This does not compute throughput and does not guess terminal statuses.
    Callers must supply source-authoritative terminal classification, local
    calendar and sprint dates in the later deterministic projection boundary.
    """
    if not isinstance(sprint_id, str) or not sprint_id.strip():
        raise ValueError("invalid_sprint_id")
    if not 1 <= max_tasks <= 100 or not 1 <= concurrency <= 5:
        raise ValueError("invalid_source_bounds")
    if not 1.0 <= timeout_seconds <= 120.0:
        raise ValueError("invalid_source_timeout")

    async def _bounded() -> dict[str, Any]:
        source = await read_sprint(sprint_id)
        if not isinstance(source, dict) or source.get("sprint_id") != sprint_id:
            raise ValueError("sprint_source_identity_mismatch")
        tasks = validate_complete_sprint_collection(source, max_tasks=max_tasks)
        # Capture the local observation time immediately after the sprint read.
        # It is NOT a source transactional snapshot; downstream must compare
        # every history transition against it and the observed status type.
        if require_current_status_types:
            current_types = extract_sprint_current_status_types(source, max_tasks=max_tasks)
            observed_at = datetime.now(timezone.utc).isoformat()
        else:
            current_types = None
            observed_at = None
        semaphore = asyncio.Semaphore(concurrency)

        async def _one(task: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
            key = task["source_id"]
            async with semaphore:
                raw = await read_history(key)
                return key, complete_workflow_history(raw, key)

        results = await asyncio.gather(*(_one(t) for t in tasks))
        result = {
            "sprint_id": sprint_id,
            "source": "REAL_AS21",
            "complete": True,
            "membership_proven": True,
            "task_count": len(tasks),
            "history_complete_count": len(results),
            "max_tasks": max_tasks,
            "history_by_task": {key: history for key, history in results},
            "scope": "sprint_only",
            "forecast": None,
            "committed_predictability": None,
        }
        if require_current_status_types:
            # Private collection evidence only; the existing public counts-only
            # source-evidence route never enables or returns this mapping.
            result["current_status_types"] = current_types
            result["snapshot_observed_at"] = observed_at
        return result

    try:
        return await asyncio.wait_for(_bounded(), timeout=timeout_seconds)
    except TimeoutError as exc:
        raise ValueError("sprint_source_timeout") from exc
