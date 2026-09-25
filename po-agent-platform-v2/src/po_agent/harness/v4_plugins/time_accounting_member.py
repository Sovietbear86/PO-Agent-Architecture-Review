"""A215G: member-level time accounting within an authoritative sprint.

The plugin completes member time-accounting requests end-to-end in one governed
trajectory. It does not rely on current task assignee for attribution; member
identity comes from each REAL AS21 worklog author.

Arbitrary rolling-period aggregation is intentionally not implemented because
the current source exposes worklogs only through bounded per-task reads. A
source-backed sprint provides the required bounded task universe.
"""
from __future__ import annotations

from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..capacity_policy import available_capacity_for_calendar_days
from ..contracts import CapabilityResult
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin
from .time_accounting_aggregate import _aggregate, _bounded_worklogs, _evidence, _sprint_context, _within


def _member_login(args: dict[str, str]) -> str:
    value = str(args.get("member_login") or args.get("assignee") or "").strip()
    if not value:
        raise V4NeedsClarification("Укажите сотрудника.")
    return value


def _space(args: dict[str, str]) -> str:
    value = str(args.get("space") or "").strip().upper()
    if not value:
        raise V4NeedsClarification(
            "Укажите продукт/пространство и спринт, чтобы ограничить набор задач для анализа списаний."
        )
    return value


def _sprint_id(args: dict[str, str]) -> str:
    value = str(args.get("sprint_id") or "").strip().upper()
    if not value:
        raise V4NeedsClarification(
            "Укажите спринт (например, текущий или сентябрьский), чтобы ограничить набор задач."
        )
    return value


async def _member_sprint_entries(runtime: Any, args: dict[str, str]):
    member_login = _member_login(args)
    space = _space(args)
    sprint_id = _sprint_id(args)
    tasks, start, finish = await _sprint_context(runtime, sprint_id, space)
    all_entries = await _bounded_worklogs(runtime, tasks)
    member_cf = member_login.casefold()
    entries = []
    for row in all_entries:
        if not _within(row, start, finish):
            continue
        user = row.get("user") if isinstance(row.get("user"), dict) else {}
        external_id = str(user.get("external_id") or "").strip()
        if external_id.casefold() == member_cf:
            entries.append(row)
    return member_login, space, sprint_id, tasks, start, finish, entries


def build_member_time_spent(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        member_login, space, sprint_id, tasks, start, finish, entries = await _member_sprint_entries(runtime, args)
        agg = _aggregate(entries)
        return CapabilityResult(
            answer=(
                f"{member_login}: {agg['total_hours']:g} ч по {agg['worklog_count']} списаниям "
                f"в {sprint_id}."
            ),
            data={
                "member_login": member_login,
                "space": space,
                "sprint_id": sprint_id,
                "period_start": start.isoformat(),
                "period_finish": finish.isoformat(),
                "sprint_task_count": len(tasks),
                **agg,
                "source": "REAL_AS21",
                "attribution": "worklog_author_external_id",
                "scope": "member_sprint_worklogs",
            },
            evidence=_evidence(entries),
        )
    return execute


def build_member_worklogs(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        member_login, space, sprint_id, tasks, start, finish, entries = await _member_sprint_entries(runtime, args)
        rows = []
        for row in entries:
            work_type = row.get("type") if isinstance(row.get("type"), dict) else {}
            rows.append({
                "id": row.get("id"),
                "task_key": row.get("task_key"),
                "date": row.get("date"),
                "duration_hours": row.get("duration_hours"),
                "work_type_code": work_type.get("code"),
                "work_type_name": work_type.get("name"),
                "comment": row.get("comment"),
            })
        agg = _aggregate(entries)
        return CapabilityResult(
            answer=(
                f"{member_login}: найдено {len(rows)} списаний на {agg['total_hours']:g} ч "
                f"в {sprint_id}."
            ),
            data={
                "member_login": member_login,
                "space": space,
                "sprint_id": sprint_id,
                "period_start": start.isoformat(),
                "period_finish": finish.isoformat(),
                "sprint_task_count": len(tasks),
                "worklog_count": len(rows),
                "total_hours": agg["total_hours"],
                "worklogs": rows,
                "source": "REAL_AS21",
                "attribution": "worklog_author_external_id",
            },
            evidence=_evidence(entries),
        )
    return execute


def build_member_utilization_actual(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        member_login, space, sprint_id, _tasks, start, finish, entries = await _member_sprint_entries(runtime, args)
        agg = _aggregate(entries)
        calendar_days = (finish - start).days + 1
        policy = available_capacity_for_calendar_days(calendar_days)
        capacity = float(policy["available_capacity_hours_for_period"])
        actual = float(agg["total_hours"])
        utilization = round(actual / capacity * 100.0, 1) if capacity > 0 else 0.0
        return CapabilityResult(
            answer=(
                f"Фактическая утилизация {member_login} в {sprint_id}: {utilization:g}% "
                f"({actual:g} ч / {capacity:g} ч)."
            ),
            data={
                "member_login": member_login,
                "space": space,
                "sprint_id": sprint_id,
                "period_start": start.isoformat(),
                "period_finish": finish.isoformat(),
                "calendar_days": calendar_days,
                "actual_hours": actual,
                "worklog_count": agg["worklog_count"],
                "available_capacity_hours": capacity,
                "utilization_percent": utilization,
                "over_capacity": actual > capacity,
                "capacity_policy": policy,
                "source": "REAL_AS21_PLUS_OWNER_POLICY",
                "numerator_source": "REAL_AS21_WORKLOGS",
                "denominator_source": "OWNER_POLICY",
                "attribution": "worklog_author_external_id",
            },
            evidence=_evidence(entries),
            warnings=["capacity_denominator_owner_policy_average_2026"],
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "member.time_spent",
        "Aggregate actual worklog time for one resolved member within one authoritative sprint.",
        {
            "member_login": "required canonical member login from member.resolve",
            "space": "required canonical product space",
            "sprint_id": "required canonical sprint id",
        },
    ),
    CapabilitySpecV4(
        "member.worklogs",
        "List one resolved member's actual worklog entries within one authoritative sprint.",
        {
            "member_login": "required canonical member login from member.resolve",
            "space": "required canonical product space",
            "sprint_id": "required canonical sprint id",
        },
    ),
    CapabilitySpecV4(
        "member.utilization_actual",
        "Calculate one member's actual sprint utilization from REAL AS21 worklogs divided by the owner-approved period-normalized capacity policy.",
        {
            "member_login": "required canonical member login from member.resolve",
            "space": "required canonical product space",
            "sprint_id": "required canonical sprint id",
        },
    ),
)

_COMMON_CAPS = (
    "space.resolve",
    "sprint.resolve",
    "sprint.search",
    "sprint.current",
    "member.resolve",
)

SKILLS = (
    SkillSpecV4(
        "member.time_spent",
        "Show actual time spent by a person in a specific/current/period-resolved sprint.",
        (
            "Resolve the product space and sprint first so the worklog fan-out has an authoritative bounded task universe.",
            "Resolve the human reference with member.resolve, passing sprint_id and space as context when useful.",
            "Call member.time_spent with the canonical member_login, space and sprint_id.",
            "Complete the aggregation in the same trajectory; do not stop after listing the person's assigned tasks and do not ask the user to confirm a per-task fan-out.",
            "If the user asks only for a rolling period such as '2 weeks' without a bounded sprint/task scope, ask for product/sprint context instead of scanning a tenant or inferring current assignment.",
        ),
        _COMMON_CAPS + ("member.time_spent",),
        completion=(
            CompletionRequirement(
                "member.time_spent",
                data_keys=("member_login", "sprint_id", "worklog_count"),
                covers_resolved_constraints=True,
            ),
        ),
    ),
    SkillSpecV4(
        "member.worklogs",
        "Show the exact worklog entries of a person in a specific/current/period-resolved sprint.",
        (
            "Resolve space, sprint and member, then call member.worklogs.",
            "Attribute work by worklog author externalId, never by current task assignee.",
        ),
        _COMMON_CAPS + ("member.worklogs",),
        completion=(
            CompletionRequirement(
                "member.worklogs",
                data_keys=("member_login", "sprint_id", "worklog_count"),
                covers_resolved_constraints=True,
            ),
        ),
    ),
    SkillSpecV4(
        "member.utilization_actual",
        "Show one person's actual utilization in a sprint from their own worklogs.",
        (
            "Resolve space, sprint and member, then call member.utilization_actual.",
            "Use REAL AS21 worklogs as numerator and OWNER_POLICY as denominator; do not use task assignment counts or estimates.",
        ),
        _COMMON_CAPS + ("member.utilization_actual",),
        completion=(
            CompletionRequirement(
                "member.utilization_actual",
                data_keys=("member_login", "sprint_id", "worklog_count", "capacity_policy"),
                covers_resolved_constraints=True,
            ),
        ),
    ),
)

BINDINGS = (
    CapabilityBindingV4("member.time_spent", handler_builder=build_member_time_spent),
    CapabilityBindingV4("member.worklogs", handler_builder=build_member_worklogs),
    CapabilityBindingV4("member.utilization_actual", handler_builder=build_member_utilization_actual),
)

UI = {
    "member.time_spent": UIContractV4(
        "analysis",
        preferred_widget="member_time_spent",
        required_fields=("member_login", "sprint_id", "total_hours"),
    ),
    "member.worklogs": UIContractV4(
        "task_collection",
        preferred_widget="member_worklogs",
        required_fields=("member_login", "sprint_id", "worklogs"),
    ),
    "member.utilization_actual": UIContractV4(
        "analysis",
        preferred_widget="member_utilization",
        required_fields=("member_login", "sprint_id", "utilization_percent", "capacity_policy"),
    ),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.time_accounting.member",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
