"""Internal, bounded AS21 sprint closure projection; NOT a forecast or HTTP route.

This is the first non-Core bridge between the opt-in same-read current task
statusType snapshot and complete source-declared lifecycle transitions.
The policy must be explicitly supplied and approved by the product's owner.
No policy is loaded, inferred, or silently activated in this module.

Output includes per-task closure timestamps and must NEVER be served verbatim
by any public endpoint. A future safe projection route must whitelist scalar
fields and must not expose the internal history or task-keyed closure mapping.
"""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

from .sprint_forecast_collector import collect_sprint_workflow_evidence
from .sprint_forecast_policy import SprintForecastPolicy, validate_forecast_policy
from .sprint_forecast_projection import bind_source_status_types


async def collect_and_project_sprint_closures(
    sprint_id: str,
    *,
    policy: SprintForecastPolicy | None,
    read_sprint: Callable[[str], Awaitable[dict[str, Any]]],
    read_history: Callable[[str], Awaitable[dict[str, Any]]],
    max_tasks: int = 100,
    concurrency: int = 5,
    timeout_seconds: float = 90.0,
) -> dict[str, Any]:
    """Return INTERNAL verified closure proof or a typed ValueError.

    Security invariants: policy preflight precedes reads; current statusType
    extracted from the same complete sprint collection; history bounded;
    transition types source-declared; as_of is captured at sprint-read time;
    transitions after that time and current/history mismatch are rejected.
    Does not claim a source-transactional snapshot (AS21 provides no token).
    """
    _, _, terminal_types = validate_forecast_policy(policy)
    if not isinstance(sprint_id, str) or not sprint_id.strip():
        raise ValueError("invalid_sprint_id")
    evidence = await collect_sprint_workflow_evidence(
        sprint_id, read_sprint=read_sprint, read_history=read_history,
        max_tasks=max_tasks, concurrency=concurrency,
        timeout_seconds=timeout_seconds, require_current_status_types=True,
    )
    observed_at = evidence.get("snapshot_observed_at")
    if not isinstance(observed_at, str):
        raise ValueError("sprint_snapshot_missing")
    try:
        as_of = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("sprint_snapshot_invalid") from exc
    if as_of.tzinfo is None:
        raise ValueError("sprint_snapshot_timezone_missing")
    current_types = evidence.get("current_status_types")
    if not isinstance(current_types, dict):
        raise ValueError("sprint_current_status_missing")
    proof = bind_source_status_types(
        evidence, current_status_types=current_types,
        terminal_status_types=terminal_types, as_of=as_of,
    )
    if proof.get("sprint_id") != sprint_id:
        raise ValueError("sprint_source_identity_mismatch")
    # Internal only. This dict contains task keys; do not serialize it as-is
    # into the existing counts-only read-only source-evidence REST endpoint.
    return {**proof, "snapshot_observed_at": observed_at}
