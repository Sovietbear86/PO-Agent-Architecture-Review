"""Flagged, bounded, out-of-Core execution of independently missing goals.

Only API orchestration: all additional work runs through governed V4.process.
This module never calls private handlers, never infers source facts, and never
credits a goal unless its terminal observation is source-backed.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

from po_agent.harness import HarnessRequest
from .goal_coverage import (
    RequestGoal, _credit_prior_observations, check_goal_coverage, detect_goals,
)

MAX_GOALS = 3
MAX_EXTRA_CALLS = 2
TOTAL_DEADLINE_SECONDS = 110.0


@dataclass(frozen=True)
class MissingGoalResult:
    response: dict[str, Any]
    attempted: int
    proven: tuple[str, ...]
    unresolved: tuple[str, ...]


def _goal_query(goal: RequestGoal) -> str | None:
    """Generic, typed goal rendering; no person/task-specific routing."""
    if goal.kind == "task_lookup" and goal.task_key:
        return f"Покажи задачу {goal.task_key}"
    if goal.kind == "task_hierarchy" and goal.task_key:
        return f"Покажи иерархию задачи {goal.task_key}"
    if goal.kind == "task_relations" and goal.task_key:
        return f"Покажи связанные задачи для {goal.task_key}"
    if goal.kind == "person_tasks" and goal.person and goal.space:
        return f"Покажи задачи {goal.person} в {goal.space}"
    return None


def _rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    data = response.get("data")
    rows = data.get("results") if isinstance(data, dict) else None
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _source_verified_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    """Only REAL_AS21 terminal facts may prove a successful goal."""
    verified = []
    for row in _rows(response):
        data = row.get("data")
        if (
            isinstance(data, dict)
            and data.get("source") == "REAL_AS21"
            and data.get("source_unavailable") is not True
            and data.get("source_complete") is not False
        ):
            verified.append(row)
    return verified


def _coverage_view(
    response: dict[str, Any], prior: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    data = response.get("data")
    verified = {**response, "data": {**(data if isinstance(data, dict) else {}),
                                    "results": _source_verified_rows(response)}}
    # Credit prior only if it passes the existing strict canonical/provenance
    # validation. This private copy is NEVER used as the public results list.
    return _credit_prior_observations(verified, prior)


async def run_bounded_missing_goals(
    runtime: Any,
    response: dict[str, Any],
    original_query: str,
    session_id: str,
    *,
    prior: tuple[dict[str, Any], ...] = (),
    loaded_skills: tuple[str, ...] = (),
    session_context: dict[str, str] | None = None,
    deadline_seconds: float = TOTAL_DEADLINE_SECONDS,
) -> MissingGoalResult:
    """Try each missing supported goal once within a shared bounded deadline.

    This deliberately NEVER converts a failed/clarification response into
    success, and never re-runs a goal already backed by source-proven evidence.
    Caller MUST use only in an isolated trusted session (auth track is OPEN).
    """
    if response.get("status") != "COMPLETED":
        return MissingGoalResult(response, 0, (), ())
    goals = detect_goals(original_query)
    if not 2 <= len(goals) <= MAX_GOALS:
        return MissingGoalResult(response, 0, (), ())
    current = dict(response)
    data = response.get("data")
    current["data"] = dict(data) if isinstance(data, dict) else {}
    current["data"]["results"] = list(_rows(response))
    view = _coverage_view(current, prior)
    initial_coverage = check_goal_coverage(view, goals)
    if not initial_coverage.unproven:
        return MissingGoalResult(response, 0, initial_coverage.proven, ())
    attempted = 0
    source_errors: list[str] = []
    # One per missing goal; cap applies to the WHOLE user query, not each call.
    pending = [g for g in goals if g.goal_id in initial_coverage.unproven]
    start = time.monotonic()
    for goal in pending[:MAX_EXTRA_CALLS]:
        remain = deadline_seconds - (time.monotonic() - start)
        if remain <= 0:
            source_errors.append("missing_goal_deadline_exhausted")
            break
        prompt = _goal_query(goal)
        if not prompt:
            source_errors.append("missing_goal_not_supported")
            continue
        attempted += 1
        try:
            result = await asyncio.wait_for(
                runtime.process(HarnessRequest(
                    query=prompt, session_id=session_id,
                    resume_loaded_skills=loaded_skills,
                    resume_observations=prior,
                    session_context=session_context or {},
                )),
                timeout=min(remain, 100.0),
            )
            step = result.to_dict()
        except Exception as exc:
            # Keep the error typed but never fabricate source unavailability.
            source_errors.append(f"missing_goal_execution_{type(exc).__name__}")
            break
        if step.get("status") != "COMPLETED":
            source_errors.append(f"missing_goal_step_{step.get('status', 'FAILED')}")
            continue
        rows = _source_verified_rows(step)
        if not rows:
            source_errors.append("missing_goal_unverified_source")
            continue
        temporary = {**current, "data": {**current["data"],
                      "results": [*current["data"]["results"], *rows]}}
        proof = check_goal_coverage(_coverage_view(temporary, prior), (goal,))
        if proof.unproven:
            source_errors.append("missing_goal_terminal_mismatch")
            continue
        current["data"]["results"].extend(rows)

    final = check_goal_coverage(_coverage_view(current, prior), goals)
    if not final.unproven:
        # Compose from SOURCE-VERIFIED per-goal terminal answers ONLY.
        # Do not reuse the original free-form LLM synthesis: it may contain
        # an unsupported negative inference about another, missing goal.
        final_view = _coverage_view(current, prior)
        all_rows = _rows(final_view)
        goal_texts: list[str] = []
        for goal in goals:
            proof_indexes = final.evidence.get(goal.goal_id, ())
            text = ""
            for index in proof_indexes:
                if 0 <= index < len(all_rows):
                    candidate = str(all_rows[index].get("answer") or "").strip()
                    if candidate:
                        text = candidate[:900]
                        break
            if not text:
                break
            goal_texts.append(text)
        if len(goal_texts) != len(goals):
            current["status"] = "PARTIAL"
            current["answer"] = "Цели подтверждены источником, но полный проверенный ответ пока недоступен."
            current["warnings"] = [
                *list(current.get("warnings") or []),
                "v4_goal_answer_evidence_missing",
            ]
        else:
            current["status"] = "COMPLETED"
            current["answer"] = "\n\n".join(goal_texts)
    else:
        current["status"] = "PARTIAL"
        current["answer"] = "Часть целей выполнена; оставшиеся не удалось подтвердить."
        current["warnings"] = [
            *list(current.get("warnings") or []),
            "v4_missing_goal_execution_partial",
            *source_errors,
        ]
    current["question"] = None
    current["options"] = []
    current["clarification_id"] = None
    state = current["data"].setdefault("_agent_core_v4", {})
    if isinstance(state, dict):
        state["goal_coverage"] = {
            "requested": len(goals),
            "proven": list(final.proven),
            "unproven": list(final.unproven),
            "extra_calls": attempted,
        }
    return MissingGoalResult(current, attempted, final.proven, final.unproven)
