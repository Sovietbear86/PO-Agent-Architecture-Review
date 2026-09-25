"""Batch 2 plugin: scope-change + current-sprint team operational metrics.

All skills are registry-discovered. The team metrics are intentionally scoped to
one authoritative current sprint in one product space; they never scan a whole
tenant or infer a static team roster from historical tasks.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..capacity_policy import available_capacity_for_calendar_days, default_monthly_capacity
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


_BACKLOG_TYPES = frozenset({"open", "todo", "backlog", "registered"})


def _space(args: dict[str, str]) -> str:
    value = str(args.get("space") or "").strip().upper()
    if not value:
        raise V4NeedsClarification("Укажите продукт/пространство команды.")
    return value


def _member(task: Any) -> str:
    for value in (getattr(task, "assignee_login", None), getattr(task, "assignee_id", None), getattr(task, "assignee", None)):
        if value and str(value).strip():
            return str(value).strip()
    return "unassigned"


def _is_wip(task: Any) -> bool:
    if not getattr(task, "is_open", False):
        return False
    status_type = str(getattr(task, "status_type", None) or "").strip().casefold()
    status_category = str(getattr(getattr(task, "status_category", None), "value", "") or "").casefold()
    if status_type in _BACKLOG_TYPES or status_category == "backlog":
        return False
    return True


async def _current_sprint_tasks(runtime: Any, args: dict[str, str]):
    space = _space(args)
    getter = getattr(runtime.adapter, "get_current_sprint_id", None)
    if getter is None:
        raise V4CapabilityUnavailable("team metrics require an authoritative current-sprint source")
    sprint_id = await getter(space)
    if not sprint_id:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose a current sprint for {space}")
    tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
    return space, sprint_id, tasks


async def _sprint_calendar_days(runtime: Any, space: str, sprint_id: str) -> int:
    list_sprints = getattr(runtime.adapter, "list_sprints", None)
    if list_sprints is None:
        raise V4CapabilityUnavailable("team.capacity requires source-backed sprint period metadata")
    rows = [row for row in await list_sprints(space) if str(row.get("code") or "").casefold() == sprint_id.casefold()]
    if len(rows) != 1:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose a unique period for sprint {sprint_id}")
    try:
        start = datetime.fromisoformat(str(rows[0].get("start_at") or "").replace("Z", "+00:00")).date()
        finish = datetime.fromisoformat(str(rows[0].get("finish_at") or "").replace("Z", "+00:00")).date()
    except ValueError as exc:
        raise V4CapabilityUnavailable(f"REAL AS21 sprint {sprint_id} has invalid start/finish dates") from exc
    if finish < start:
        raise V4CapabilityUnavailable(f"REAL AS21 sprint {sprint_id} has an invalid period")
    return (finish - start).days + 1


def _task_evidence(tasks: list[Any], kind: str) -> list[Evidence]:
    return [
        Evidence(
            type=kind,
            source="as21",
            entity_id=task.key,
            label=task.title,
            value=_member(task),
        )
        for task in tasks
    ]


def build_sprint_scope_change(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id = str(args.get("sprint_id") or "").strip().upper()
        space = str(args.get("space") or "").strip().upper() or None
        if not sprint_id:
            raise V4NeedsClarification("Укажите спринт.")
        # Validate that the requested sprint exists and has a source-backed
        # collection before classifying the missing historical baseline.
        await runtime.adapter.get_sprint_tasks(sprint_id, space)
        raise V4CapabilityUnavailable(
            "sprint.scope_change requires an authoritative sprint-start commitment baseline; "
            "REAL AS21 currently exposes only the current sprint membership"
        )
    return execute


def build_team_workload(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        rows: dict[str, dict[str, Any]] = {}
        for task in tasks:
            member = _member(task)
            row = rows.setdefault(member, {
                "member": member,
                "active_tasks": 0,
                "wip": 0,
                "blocked": 0,
                "completed": 0,
            })
            if task.is_completed:
                row["completed"] += 1
                continue
            row["active_tasks"] += 1
            if _is_wip(task):
                row["wip"] += 1
            if task.is_blocked:
                row["blocked"] += 1
        workload = sorted(rows.values(), key=lambda row: (-row["active_tasks"], -row["wip"], row["member"]))
        data = {
            "space": space,
            "sprint_id": sprint_id,
            "members_count": len(workload),
            "active_tasks": sum(row["active_tasks"] for row in workload),
            "completed_tasks": sum(row["completed"] for row in workload),
            "unassigned_active_tasks": next((row["active_tasks"] for row in workload if row["member"] == "unassigned"), 0),
            "workload": workload,
            "source": "REAL_AS21",
            "scope": "current_sprint",
            "formula": "task-count workload grouped by canonical assignee within authoritative current sprint",
        }
        return CapabilityResult(
            answer=f"Нагрузка команды {space} в {sprint_id}: {data['active_tasks']} активных задач.",
            data=data,
            evidence=_task_evidence(tasks, "team_workload_task"),
            warnings=["task_count_workload_not_capacity"],
        )
    return execute


def build_team_wip(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        selected = [task for task in tasks if _is_wip(task)]
        counts = Counter(_member(task) for task in selected)
        rows = [{"member": member, "wip": count} for member, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
        return CapabilityResult(
            answer=f"WIP команды {space} в {sprint_id}: {len(selected)} задач.",
            data={
                "space": space, "sprint_id": sprint_id, "total_wip": len(selected),
                "by_member": rows, "task_keys": [task.key for task in selected],
                "source": "REAL_AS21", "scope": "current_sprint",
            },
            evidence=_task_evidence(selected, "team_wip_task"),
        )
    return execute


def build_team_blocked(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        selected = [task for task in tasks if task.is_blocked]
        counts = Counter(_member(task) for task in selected)
        rows = [{"member": member, "blocked": count} for member, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))]
        return CapabilityResult(
            answer=f"Заблокировано у команды {space} в {sprint_id}: {len(selected)} задач.",
            data={
                "space": space, "sprint_id": sprint_id, "total_blocked": len(selected),
                "by_member": rows, "task_keys": [task.key for task in selected],
                "source": "REAL_AS21", "scope": "current_sprint",
            },
            evidence=_task_evidence(selected, "team_blocked_task"),
        )
    return execute


def build_team_capacity(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        active = [task for task in tasks if not task.is_completed and _member(task) != "unassigned"]
        missing_estimate = [task.key for task in active if getattr(task, "estimate_hours", None) is None]
        if missing_estimate:
            raise V4CapabilityUnavailable(
                "team.capacity cannot be calculated from REAL AS21 because active assigned tasks "
                "do not expose source-backed estimates; an explicit capacity baseline alone is insufficient"
            )

        raw_capacity = str(args.get("capacity_hours") or "").strip()
        if raw_capacity:
            try:
                capacity_hours = float(raw_capacity)
            except ValueError as exc:
                raise V4NeedsClarification("Capacity должен быть числом часов на исполнителя.") from exc
            if capacity_hours <= 0:
                raise V4NeedsClarification("Capacity должен быть больше нуля.")
            capacity_source = "explicit_user_baseline"
            capacity_policy = None
        else:
            calendar_days = await _sprint_calendar_days(runtime, space, sprint_id)
            policy = available_capacity_for_calendar_days(calendar_days)
            capacity_hours = float(policy["available_capacity_hours_for_period"])
            capacity_source = "owner_policy_default"
            capacity_policy = policy

        by_member: dict[str, dict[str, Any]] = {}
        for task in active:
            member = _member(task)
            row = by_member.setdefault(member, {"member": member, "tasks": 0, "estimated_hours": 0.0})
            row["tasks"] += 1
            row["estimated_hours"] += float(task.estimate_hours)

        rows = []
        for member in sorted(by_member):
            row = by_member[member]
            estimated = round(row["estimated_hours"], 2)
            utilization = round(estimated / capacity_hours * 100.0, 1)
            rows.append({
                "member": member,
                "tasks": row["tasks"],
                "estimated_hours": estimated,
                "capacity_hours": capacity_hours,
                "utilization_percent": utilization,
                "over_capacity": estimated > capacity_hours,
            })

        return CapabilityResult(
            answer=f"Capacity команды {space} рассчитан для {len(rows)} исполнителей при baseline {capacity_hours:g} ч.",
            data={
                "space": space, "sprint_id": sprint_id, "capacity_hours_per_member": capacity_hours,
                "members": rows, "source": "REAL_AS21", "scope": "current_sprint",
                "capacity_source": capacity_source,
                "capacity_policy": capacity_policy,
            },
            evidence=_task_evidence(active, "team_capacity_task"),
            warnings=(
                ["capacity_baseline_user_supplied"]
                if capacity_source == "explicit_user_baseline"
                else ["capacity_baseline_owner_policy"]
            ),
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("sprint.scope_change", "Measure sprint scope change only when an authoritative sprint-start baseline exists.", {"sprint_id": "required canonical sprint id", "space": "optional canonical space"}),
    CapabilitySpecV4("team.workload", "Task-count workload by assignee in the authoritative current sprint of one space.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.wip", "Current-sprint WIP grouped by assignee for one product space.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.blocked", "Current-sprint blocked tasks grouped by assignee for one product space.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.capacity", "Planned utilization from source-backed estimates and the owner-approved 2026 capacity policy normalized to the authoritative sprint period; explicit user capacity may override it.", {"space": "required canonical product space", "capacity_hours": "optional explicit hours per member; otherwise period-normalized owner policy is used"}),
)

SKILLS = (
    SkillSpecV4(
        "sprint.scope_change",
        "Show sprint scope change only from an authoritative sprint-start commitment baseline.",
        (
            "Resolve the sprint generically using sprint.resolve/search/current as appropriate.",
            "Call sprint.scope_change with the canonical sprint id.",
            "If the source lacks a sprint-start commitment baseline, fail closed; never compare to a previous sprint as a substitute.",
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.scope_change"),
        completion=(CompletionRequirement("sprint.scope_change", data_keys=("sprint_id", "scope_change")),),
    ),
    SkillSpecV4(
        "team.workload",
        "Show task-count workload for the team visible in the current sprint of one product space.",
        (
            "Resolve the product space.",
            "Call team.workload; it resolves the authoritative current sprint and groups its complete task set by canonical assignee.",
            "Do not present task counts as capacity or performance scoring.",
        ),
        ("space.resolve", "team.workload"),
        completion=(CompletionRequirement("team.workload", data_keys=("space", "sprint_id", "workload")),),
    ),
    SkillSpecV4(
        "team.wip",
        "Show WIP by assignee for the authoritative current sprint of one product space.",
        ("Resolve the product space, then call team.wip.",),
        ("space.resolve", "team.wip"),
        completion=(CompletionRequirement("team.wip", data_keys=("space", "sprint_id", "total_wip")),),
    ),
    SkillSpecV4(
        "team.blocked",
        "Show blocked tasks by assignee for the authoritative current sprint of one product space.",
        ("Resolve the product space, then call team.blocked.",),
        ("space.resolve", "team.blocked"),
        completion=(CompletionRequirement("team.blocked", data_keys=("space", "sprint_id", "total_blocked")),),
    ),
    SkillSpecV4(
        "team.capacity",
        "Calculate planned utilization from source-backed estimates using the owner-approved 2026 capacity baseline unless the user explicitly overrides it.",
        (
            "Resolve the product space.",
            "Call team.capacity. Source-backed estimates remain mandatory.",
            "If the user provides capacity hours, use them exactly; otherwise normalize the owner policy (247 working days/year × 0.87 × 8h) to the authoritative sprint calendar length.",
            "Never infer estimates or treat missing estimates as zero.",
        ),
        ("space.resolve", "team.capacity"),
        completion=(CompletionRequirement("team.capacity", data_keys=("space", "sprint_id", "members")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("sprint.scope_change", handler_builder=build_sprint_scope_change),
    CapabilityBindingV4("team.workload", handler_builder=build_team_workload),
    CapabilityBindingV4("team.wip", handler_builder=build_team_wip),
    CapabilityBindingV4("team.blocked", handler_builder=build_team_blocked),
    CapabilityBindingV4("team.capacity", handler_builder=build_team_capacity),
)

UI = {
    "sprint.scope_change": UIContractV4("analysis", preferred_widget="sprint_metric", required_fields=("sprint_id",)),
    "team.workload": UIContractV4("analysis", preferred_widget="team_workload", required_fields=("space", "sprint_id", "workload")),
    "team.wip": UIContractV4("task_collection", preferred_widget="team_wip", required_fields=("space", "sprint_id", "total_wip")),
    "team.blocked": UIContractV4("task_collection", preferred_widget="team_blocked", required_fields=("space", "sprint_id", "total_blocked")),
    "team.capacity": UIContractV4("analysis", preferred_widget="team_capacity", required_fields=("space", "sprint_id", "members")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.batch2.team_current_sprint",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
