"""Batch 3 plugin: team analysis extensions + release scope.

The plugin preserves the V4 architecture invariant: all behavior is registry-
discovered and source bounded; no Agent Core/planner/runtime business routing is
added here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


_BACKLOG_TYPES = frozenset({"open", "todo", "backlog", "registered"})


def _space(args: dict[str, str]) -> str:
    value = str(args.get("space") or "").strip().upper()
    if not value:
        raise V4NeedsClarification("Укажите продукт/пространство.")
    return value


def _member(task: Any) -> str:
    for value in (
        getattr(task, "assignee_login", None),
        getattr(task, "assignee_id", None),
        getattr(task, "assignee", None),
    ):
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
        raise V4CapabilityUnavailable("team analytics require an authoritative current-sprint source")
    sprint_id = await getter(space)
    if not sprint_id:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose a current sprint for {space}")
    tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
    return space, sprint_id, tasks


def _evidence(tasks: list[Any], kind: str) -> list[Evidence]:
    return [
        Evidence(type=kind, source="as21", entity_id=task.key, label=task.title, value=_member(task))
        for task in tasks
    ]


def build_team_competency_match(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, _tasks = await _current_sprint_tasks(runtime, args)
        raise V4CapabilityUnavailable(
            f"team.competency_match for {space}/{sprint_id} requires an authoritative competency/skill source; "
            "REAL AS21 currently exposes task assignment/state but not validated team competencies"
        )
    return execute


def build_team_assignee_recommendation(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, _tasks = await _current_sprint_tasks(runtime, args)
        raise V4CapabilityUnavailable(
            f"team.assignee_recommendation for {space}/{sprint_id} requires source-backed competencies and availability; "
            "the current source contract is insufficient for a defensible assignee recommendation"
        )
    return execute


def build_team_bottlenecks(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        active = [task for task in tasks if not task.is_completed]
        counts = Counter(_member(task) for task in active)
        total = len(active)
        rows = []
        for member, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            share = round(count / total * 100.0, 1) if total else 0.0
            blocked = sum(1 for task in active if _member(task) == member and task.is_blocked)
            wip = sum(1 for task in active if _member(task) == member and _is_wip(task))
            if share >= 50.0 or count >= 3 or blocked > 0:
                rows.append({
                    "member": member,
                    "active_tasks": count,
                    "share_percent": share,
                    "wip": wip,
                    "blocked": blocked,
                    "reasons": [
                        reason for reason, flag in (
                            ("active_task_concentration", share >= 50.0 or count >= 3),
                            ("blocked_tasks", blocked > 0),
                        ) if flag
                    ],
                })
        return CapabilityResult(
            answer=f"Потенциальных узких мест команды {space} в {sprint_id}: {len(rows)}.",
            data={
                "space": space,
                "sprint_id": sprint_id,
                "active_tasks": total,
                "bottlenecks": rows,
                "thresholds": {"share_percent": 50.0, "active_tasks": 3},
                "source": "REAL_AS21",
                "scope": "current_sprint",
                "semantics": "descriptive_task_concentration_not_employee_performance",
            },
            evidence=_evidence(active, "team_bottleneck_task"),
            warnings=["descriptive_operational_metric_not_employee_score"],
        )
    return execute


def build_team_distribution(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, tasks = await _current_sprint_tasks(runtime, args)
        counts = Counter(_member(task) for task in tasks)
        status_by_member: dict[str, Counter[str]] = defaultdict(Counter)
        blocked_by_member: Counter[str] = Counter()
        wip_by_member: Counter[str] = Counter()
        for task in tasks:
            member = _member(task)
            status_key = str(getattr(task, "status_raw", None) or getattr(task.status, "value", ""))
            status_by_member[member][status_key] += 1
            if task.is_blocked:
                blocked_by_member[member] += 1
            if _is_wip(task):
                wip_by_member[member] += 1
        rows = [
            {
                "member": member,
                "tasks": counts[member],
                "wip": wip_by_member[member],
                "blocked": blocked_by_member[member],
                "status_distribution": dict(sorted(status_by_member[member].items())),
            }
            for member in sorted(counts)
        ]
        return CapabilityResult(
            answer=f"Распределение {len(tasks)} задач команды {space} в {sprint_id} показано по {len(rows)} исполнителям/очередям.",
            data={
                "space": space,
                "sprint_id": sprint_id,
                "total_tasks": len(tasks),
                "members": rows,
                "source": "REAL_AS21",
                "scope": "current_sprint",
            },
            evidence=_evidence(tasks, "team_distribution_task"),
        )
    return execute


def build_release_scope(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        release_id = str(args.get("release_id") or "").strip()
        space = _space(args)
        if not release_id:
            raise V4NeedsClarification("Укажите релиз.")
        tasks = list(await runtime.adapter.get_release_tasks(release_id, space))
        if not tasks:
            raise V4CapabilityUnavailable(
                "release.scope requires authoritative release-to-task membership; "
                "the current REAL AS21 task source does not expose populated release linkage"
            )
        return CapabilityResult(
            answer=f"В scope релиза {release_id}: {len(tasks)} задач.",
            data={
                "space": space,
                "release_id": release_id,
                "count": len(tasks),
                "task_keys": [task.key for task in tasks],
                "source": "REAL_AS21",
                "membership": "source_backed_release_task_query",
            },
            evidence=[
                Evidence(type="release_scope_task", source="as21", entity_id=task.key, label=task.title, value=task.status_raw or task.status.value)
                for task in tasks
            ],
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("team.competency_match", "Match team competencies only from an authoritative competency source.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.assignee_recommendation", "Recommend an assignee only from source-backed competencies and availability.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.bottlenecks", "Describe current-sprint task concentration and blocked-task hotspots by assignee.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.distribution", "Describe current-sprint task/status distribution by assignee.", {"space": "required canonical product space"}),
    CapabilitySpecV4("release.scope", "List release membership only from bounded, source-backed release-task linkage.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
)

SKILLS = (
    SkillSpecV4(
        "team.competency_match",
        "Match competencies only when a validated team competency source exists.",
        (
            "Resolve the product space.",
            "Call team.competency_match.",
            "If the source exposes no authoritative competency matrix, fail closed; never infer competence from current task ownership or titles.",
        ),
        ("space.resolve", "team.competency_match"),
        completion=(CompletionRequirement("team.competency_match", data_keys=("space", "matches")),),
    ),
    SkillSpecV4(
        "team.assignee_recommendation",
        "Recommend an assignee only from source-backed competencies plus availability/capacity.",
        (
            "Resolve the product space.",
            "Call team.assignee_recommendation.",
            "If competence or availability is not source-backed, fail closed; never score people from task count or fabricate a recommendation.",
        ),
        ("space.resolve", "team.assignee_recommendation"),
        completion=(CompletionRequirement("team.assignee_recommendation", data_keys=("space", "recommendations")),),
    ),
    SkillSpecV4(
        "team.bottlenecks",
        "Show descriptive operational bottlenecks in the authoritative current sprint.",
        (
            "Resolve the product space, then call team.bottlenecks.",
            "Interpret the result as task concentration/blockage, not employee performance.",
        ),
        ("space.resolve", "team.bottlenecks"),
        completion=(CompletionRequirement("team.bottlenecks", data_keys=("space", "sprint_id", "bottlenecks")),),
    ),
    SkillSpecV4(
        "team.distribution",
        "Show exact current-sprint task/status distribution by assignee.",
        ("Resolve the product space, then call team.distribution.",),
        ("space.resolve", "team.distribution"),
        completion=(CompletionRequirement("team.distribution", data_keys=("space", "sprint_id", "members")),),
    ),
    SkillSpecV4(
        "release.scope",
        "Show exact release task membership only when authoritative release-to-task linkage exists.",
        (
            "Resolve the product space.",
            "Use release.search with require_single=true to obtain the canonical release id.",
            "Call release.scope with both release_id and space.",
            "If membership is not source-backed, fail closed; never return an empty scope as proof that the release has zero tasks.",
        ),
        ("space.resolve", "release.search", "release.scope"),
        completion=(CompletionRequirement("release.scope", data_keys=("release_id", "count")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("team.competency_match", handler_builder=build_team_competency_match),
    CapabilityBindingV4("team.assignee_recommendation", handler_builder=build_team_assignee_recommendation),
    CapabilityBindingV4("team.bottlenecks", handler_builder=build_team_bottlenecks),
    CapabilityBindingV4("team.distribution", handler_builder=build_team_distribution),
    CapabilityBindingV4("release.scope", handler_builder=build_release_scope),
)

UI = {
    "team.competency_match": UIContractV4("analysis", preferred_widget="team_competency", required_fields=("space",)),
    "team.assignee_recommendation": UIContractV4("analysis", preferred_widget="team_recommendation", required_fields=("space",)),
    "team.bottlenecks": UIContractV4("analysis", preferred_widget="team_bottlenecks", required_fields=("space", "sprint_id", "bottlenecks")),
    "team.distribution": UIContractV4("analysis", preferred_widget="team_distribution", required_fields=("space", "sprint_id", "members")),
    "release.scope": UIContractV4("task_collection", preferred_widget="release_scope", required_fields=("release_id",)),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.batch3.team_release",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
