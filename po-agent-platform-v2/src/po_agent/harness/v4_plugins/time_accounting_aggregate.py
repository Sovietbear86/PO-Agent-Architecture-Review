"""A215F: source-backed sprint/team/release time accounting and actual utilization.

All aggregation is over bounded authoritative task memberships and per-task
worklog reads. No tenant-wide scans, no local cache, and no estimate/workload
substitution.
"""
from __future__ import annotations

import asyncio
from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..capacity_policy import available_capacity_for_calendar_days
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


_MAX_WORKLOG_CONCURRENCY = 8


def _space(args: dict[str, str]) -> str:
    value = str(args.get("space") or "").strip().upper()
    if not value:
        raise V4NeedsClarification("Укажите продукт/пространство.")
    return value


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        try:
            return date.fromisoformat(text[:10])
        except ValueError:
            return None


async def _sprint_context(runtime: Any, sprint_id: str, space: str):
    tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
    if not tasks:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose task membership for sprint {sprint_id}")
    list_sprints = getattr(runtime.adapter, "list_sprints", None)
    if list_sprints is None:
        raise V4CapabilityUnavailable("sprint time accounting requires source-backed sprint period metadata")
    rows = [row for row in await list_sprints(space) if str(row.get("code") or "").casefold() == sprint_id.casefold()]
    if len(rows) != 1:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose a unique period for sprint {sprint_id}")
    start = _parse_date(rows[0].get("start_at"))
    finish = _parse_date(rows[0].get("finish_at"))
    if start is None or finish is None or finish < start:
        raise V4CapabilityUnavailable(f"REAL AS21 sprint {sprint_id} has no usable start/finish dates")
    return tasks, start, finish


async def _current_sprint_context(runtime: Any, space: str):
    getter = getattr(runtime.adapter, "get_current_sprint_id", None)
    if getter is None:
        raise V4CapabilityUnavailable("current-sprint source is unavailable")
    sprint_id = await getter(space)
    if not sprint_id:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose a current sprint for {space}")
    tasks, start, finish = await _sprint_context(runtime, sprint_id, space)
    return sprint_id, tasks, start, finish


async def _bounded_worklogs(runtime: Any, tasks: list[Any]) -> list[dict[str, Any]]:
    reader = getattr(runtime.adapter, "get_task_worklogs", None)
    if reader is None:
        raise V4CapabilityUnavailable("time aggregation requires the bounded task worklog source")

    semaphore = asyncio.Semaphore(_MAX_WORKLOG_CONCURRENCY)

    async def read(task: Any):
        async with semaphore:
            payload = await reader(task.key)
        if not payload.get("complete"):
            raise V4CapabilityUnavailable(f"incomplete worklog collection for {task.key}")
        entries = payload.get("entries")
        if not isinstance(entries, list):
            raise V4CapabilityUnavailable(f"malformed worklog collection for {task.key}")
        return task.key, entries

    pairs = await asyncio.gather(*(read(task) for task in tasks)) if tasks else []
    result: list[dict[str, Any]] = []
    for task_key, entries in pairs:
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            row = dict(entry)
            row["task_key"] = task_key
            result.append(row)
    return result


def _within(entry: dict[str, Any], start: date, finish: date) -> bool:
    current = _parse_date(entry.get("date"))
    return current is not None and start <= current <= finish


def _aggregate(entries: list[dict[str, Any]]) -> dict[str, Any]:
    by_member: dict[str, float] = defaultdict(float)
    by_task: dict[str, float] = defaultdict(float)
    by_type: dict[str, float] = defaultdict(float)
    by_date: dict[str, float] = defaultdict(float)
    unknown_user_hours = 0.0

    for entry in entries:
        hours = entry.get("duration_hours")
        if not isinstance(hours, (int, float)):
            raise V4CapabilityUnavailable("worklog entry has no normalized duration")
        hours = float(hours)
        user = entry.get("user") if isinstance(entry.get("user"), dict) else {}
        external_id = str(user.get("external_id") or "").strip()
        task_key = str(entry.get("task_key") or "").strip()
        work_type = entry.get("type") if isinstance(entry.get("type"), dict) else {}
        type_name = str(work_type.get("name") or work_type.get("code") or "unknown")
        date_key = str(entry.get("date") or "")

        if external_id:
            by_member[external_id] += hours
        else:
            unknown_user_hours += hours
        if task_key:
            by_task[task_key] += hours
        by_type[type_name] += hours
        if date_key:
            by_date[date_key] += hours

    total = sum(float(entry.get("duration_hours") or 0.0) for entry in entries)
    return {
        "total_hours": round(total, 2),
        "worklog_count": len(entries),
        "by_member": [
            {"member": key, "hours": round(value, 2)}
            for key, value in sorted(by_member.items(), key=lambda item: (-item[1], item[0]))
        ],
        "by_task": [
            {"task_key": key, "hours": round(value, 2)}
            for key, value in sorted(by_task.items(), key=lambda item: (-item[1], item[0]))
        ],
        "by_type": [
            {"work_type": key, "hours": round(value, 2)}
            for key, value in sorted(by_type.items(), key=lambda item: (-item[1], item[0]))
        ],
        "by_date": [
            {"date": key, "hours": round(value, 2)}
            for key, value in sorted(by_date.items())
        ],
        "unknown_user_hours": round(unknown_user_hours, 2),
    }


def _evidence(entries: list[dict[str, Any]]) -> list[Evidence]:
    rows: list[Evidence] = []
    for entry in entries:
        user = entry.get("user") if isinstance(entry.get("user"), dict) else {}
        work_type = entry.get("type") if isinstance(entry.get("type"), dict) else {}
        rows.append(Evidence(
            type="worklog",
            source="as21",
            entity_id=str(entry.get("id") or entry.get("task_key") or ""),
            label=str(work_type.get("name") or "worklog"),
            value={
                "task_key": entry.get("task_key"),
                "date": entry.get("date"),
                "user": user.get("external_id"),
                "duration_hours": entry.get("duration_hours"),
            },
        ))
    return rows


def build_sprint_time_spent(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id = str(args.get("sprint_id") or "").strip().upper()
        space = _space(args)
        if not sprint_id:
            raise V4NeedsClarification("Укажите спринт.")
        tasks, start, finish = await _sprint_context(runtime, sprint_id, space)
        entries = [row for row in await _bounded_worklogs(runtime, tasks) if _within(row, start, finish)]
        agg = _aggregate(entries)
        data = {
            "space": space,
            "sprint_id": sprint_id,
            "period_start": start.isoformat(),
            "period_finish": finish.isoformat(),
            "task_count": len(tasks),
            **agg,
            "source": "REAL_AS21",
            "scope": "sprint_period_worklogs",
        }
        return CapabilityResult(
            answer=f"В {sprint_id} списано {agg['total_hours']:g} ч по {agg['worklog_count']} списаниям.",
            data=data,
            evidence=_evidence(entries),
        )
    return execute


def build_team_time_spent(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space = _space(args)
        sprint_id, tasks, start, finish = await _current_sprint_context(runtime, space)
        entries = [row for row in await _bounded_worklogs(runtime, tasks) if _within(row, start, finish)]
        agg = _aggregate(entries)
        data = {
            "space": space,
            "sprint_id": sprint_id,
            "period_start": start.isoformat(),
            "period_finish": finish.isoformat(),
            **agg,
            "source": "REAL_AS21",
            "scope": "current_sprint_worklogs",
        }
        return CapabilityResult(
            answer=f"Команда {space} списала {agg['total_hours']:g} ч в текущем спринте {sprint_id}.",
            data=data,
            evidence=_evidence(entries),
        )
    return execute


def build_team_utilization_actual(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space = _space(args)
        sprint_id, tasks, start, finish = await _current_sprint_context(runtime, space)
        entries = [row for row in await _bounded_worklogs(runtime, tasks) if _within(row, start, finish)]
        agg = _aggregate(entries)
        calendar_days = (finish - start).days + 1
        policy = available_capacity_for_calendar_days(calendar_days)
        capacity = float(policy["available_capacity_hours_for_period"])

        rows = []
        for member_row in agg["by_member"]:
            spent = float(member_row["hours"])
            rows.append({
                "member": member_row["member"],
                "actual_hours": spent,
                "available_capacity_hours": capacity,
                "utilization_percent": round(spent / capacity * 100.0, 1) if capacity > 0 else 0.0,
                "over_capacity": spent > capacity,
            })

        return CapabilityResult(
            answer=f"Фактическая утилизация команды {space} рассчитана по списаниям в {sprint_id}.",
            data={
                "space": space,
                "sprint_id": sprint_id,
                "period_start": start.isoformat(),
                "period_finish": finish.isoformat(),
                "calendar_days": calendar_days,
                "capacity_hours_per_member": capacity,
                "capacity_policy": policy,
                "members": rows,
                "total_actual_hours": agg["total_hours"],
                "worklog_count": agg["worklog_count"],
                "unknown_user_hours": agg["unknown_user_hours"],
                "source": "REAL_AS21_PLUS_OWNER_POLICY",
                "numerator_source": "REAL_AS21_WORKLOGS",
                "denominator_source": "OWNER_POLICY",
            },
            evidence=_evidence(entries),
            warnings=["capacity_denominator_owner_policy_average_2026"],
        )
    return execute


def build_release_time_spent(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space = _space(args)
        release_id = str(args.get("release_id") or "").strip()
        if not release_id:
            raise V4NeedsClarification("Укажите релиз.")
        tasks = list(await runtime.adapter.get_release_tasks(release_id, space))
        if not tasks:
            raise V4CapabilityUnavailable(
                "release.time_spent requires authoritative release-to-task membership; "
                "the current REAL AS21 source does not expose populated release linkage"
            )
        entries = await _bounded_worklogs(runtime, tasks)
        agg = _aggregate(entries)
        return CapabilityResult(
            answer=f"По задачам релиза {release_id} списано {agg['total_hours']:g} ч.",
            data={
                "space": space,
                "release_id": release_id,
                "task_count": len(tasks),
                **agg,
                "source": "REAL_AS21",
                "scope": "release_membership_worklogs",
            },
            evidence=_evidence(entries),
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("sprint.time_spent", "Aggregate dated REAL AS21 worklogs across authoritative sprint membership and sprint period.", {"space": "required canonical product space", "sprint_id": "required canonical sprint id"}),
    CapabilitySpecV4("team.time_spent", "Aggregate actual team worklogs for the authoritative current sprint.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.utilization_actual", "Calculate actual current-sprint utilization from REAL AS21 worklogs divided by the owner-approved period-normalized 2026 capacity policy.", {"space": "required canonical product space"}),
    CapabilitySpecV4("release.time_spent", "Aggregate worklogs across authoritative release membership only.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
)

SKILLS = (
    SkillSpecV4(
        "sprint.time_spent",
        "Show actual time spent in a sprint, grouped by member/task/type/date.",
        ("Resolve the product space and sprint, then call sprint.time_spent.",),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.time_spent"),
        completion=(CompletionRequirement("sprint.time_spent", data_keys=("sprint_id", "worklog_count")),),
    ),
    SkillSpecV4(
        "team.time_spent",
        "Show actual team time spent in the current sprint.",
        ("Resolve the product space, then call team.time_spent.",),
        ("space.resolve", "team.time_spent"),
        completion=(CompletionRequirement("team.time_spent", data_keys=("space", "sprint_id", "worklog_count")),),
    ),
    SkillSpecV4(
        "team.utilization_actual",
        "Show actual team utilization from worklogs using the owner-approved 2026 average capacity policy normalized to the sprint period.",
        (
            "Resolve the product space, then call team.utilization_actual.",
            "Treat REAL AS21 worklogs as numerator and OWNER_POLICY as denominator; keep both provenance labels visible.",
        ),
        ("space.resolve", "team.utilization_actual"),
        completion=(CompletionRequirement("team.utilization_actual", data_keys=("space", "sprint_id", "worklog_count", "capacity_policy")),),
    ),
    SkillSpecV4(
        "release.time_spent",
        "Show actual time spent across release tasks only when authoritative release membership exists.",
        (
            "Resolve the product space and release with release.search.",
            "Call release.time_spent with source-backed release id and space.",
            "If release membership is unavailable, fail closed instead of returning zero.",
        ),
        ("space.resolve", "release.search", "release.time_spent"),
        completion=(CompletionRequirement("release.time_spent", data_keys=("release_id", "total_hours")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("sprint.time_spent", handler_builder=build_sprint_time_spent),
    CapabilityBindingV4("team.time_spent", handler_builder=build_team_time_spent),
    CapabilityBindingV4("team.utilization_actual", handler_builder=build_team_utilization_actual),
    CapabilityBindingV4("release.time_spent", handler_builder=build_release_time_spent),
)

UI = {
    "sprint.time_spent": UIContractV4("analysis", preferred_widget="time_spent_breakdown", required_fields=("sprint_id", "total_hours", "by_member")),
    "team.time_spent": UIContractV4("analysis", preferred_widget="time_spent_breakdown", required_fields=("space", "sprint_id", "total_hours", "by_member")),
    "team.utilization_actual": UIContractV4("analysis", preferred_widget="team_utilization", required_fields=("space", "sprint_id", "members", "capacity_policy")),
    "release.time_spent": UIContractV4("analysis", preferred_widget="time_spent_breakdown", required_fields=("release_id", "total_hours")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.time_accounting.aggregate",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
