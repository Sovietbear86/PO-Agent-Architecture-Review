"""Batch 3 plugin: team analysis extensions + release scope.

The plugin preserves the V4 architecture invariant: all behavior is registry-
discovered and source bounded; no Agent Core/planner/runtime business routing is
added here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ...config.real_team import get_real_team_members
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


_TOKEN = re.compile(r"[A-Za-zА-Яа-яЁё0-9+#.]{2,}")
_STOP = {
    "для", "или", "это", "как", "при", "над", "под", "без", "его", "ее", "её",
    "the", "and", "for", "with", "from", "task", "задача", "нужно", "требуется",
}


def _tokens(text: str) -> set[str]:
    return {x.casefold() for x in _TOKEN.findall(text or "") if x.casefold() not in _STOP}


def _team_profiles(space: str) -> list[dict[str, Any]]:
    members = get_real_team_members()
    if not members:
        raise V4CapabilityUnavailable(
            "team competency source is configured in task-api/config/team_members.yaml but is unavailable at runtime"
        )
    rows = []
    for member in members:
        products = {str(x).strip().upper() for x in (member.get("products") or [])}
        if space not in products:
            continue
        rows.append(member)
    return rows


def _profile_tokens(profile: dict[str, Any]) -> set[str]:
    declared = " ".join([
        str(profile.get("professional_profile") or ""),
        " ".join(str(x) for x in (profile.get("competencies") or [])),
        " ".join(str(x) for x in (profile.get("products") or [])),
    ])
    return _tokens(declared)


def _profile_evidence(profile: dict[str, Any]) -> Evidence:
    competencies = ", ".join(str(x) for x in (profile.get("competencies") or []))
    value = "; ".join(
        x for x in (str(profile.get("professional_profile") or ""), competencies) if x
    ) or "declared profile"
    return Evidence(
        type="team_profile",
        source="team_config",
        entity_id=str(profile.get("login") or profile.get("id") or ""),
        label=str(profile.get("full_name") or profile.get("login") or "team member"),
        value=value,
    )


async def _ground_task(runtime: Any, args: dict[str, str]):
    key = str(args.get("task_key") or "").strip().upper()
    if not key:
        raise V4NeedsClarification("Укажите задачу для сопоставления компетенций.")
    task = await runtime.adapter.get_task(key)
    if task is None:
        raise V4CapabilityUnavailable(f"REAL AS21 did not expose task {key}")
    return task


def build_team_competency_match(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space = _space(args)
        task = await _ground_task(runtime, args)
        profiles = _team_profiles(space)
        task_tokens = _tokens(f"{task.title} {getattr(task, 'description', '') or ''}")
        rows = []
        evidence = [
            Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status_raw or task.status.value)
        ]
        for profile in profiles:
            matched = sorted(task_tokens & _profile_tokens(profile))
            if not matched:
                continue
            rows.append({
                "member": profile.get("login"),
                "full_name": profile.get("full_name"),
                "matched_terms": matched,
                "match_count": len(matched),
                "professional_profile": profile.get("professional_profile"),
                "competencies": list(profile.get("competencies") or []),
                "products": list(profile.get("products") or []),
            })
            evidence.append(_profile_evidence(profile))
        rows.sort(key=lambda row: (-int(row["match_count"]), str(row["member"])))
        return CapabilityResult(
            answer=f"Для {task.key} найдено {len(rows)} совпадений с явно заявленными компетенциями команды {space}.",
            data={
                "space": space,
                "task_key": task.key,
                "matches": rows,
                "method": "declared_repository_profile_token_overlap",
                "competency_source": "task-api/config/team_members.yaml",
                "source": "REAL_AS21_PLUS_TEAM_CONFIG",
            },
            evidence=evidence,
            warnings=[] if rows else ["no_declared_competency_match"],
        )
    return execute


def build_team_assignee_recommendation(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, sprint_id, sprint_tasks = await _current_sprint_tasks(runtime, args)
        task = await _ground_task(runtime, args)
        profiles = _team_profiles(space)
        task_tokens = _tokens(f"{task.title} {getattr(task, 'description', '') or ''}")

        active = [t for t in sprint_tasks if not t.is_completed]
        load = Counter(_member(t) for t in active)
        wip = Counter(_member(t) for t in active if _is_wip(t))
        blocked = Counter(_member(t) for t in active if t.is_blocked)

        rows = []
        evidence = [
            Evidence(type="task", source="as21", entity_id=task.key, label=task.title, value=task.status_raw or task.status.value)
        ]
        for profile in profiles:
            matched = sorted(task_tokens & _profile_tokens(profile))
            if not matched:
                continue
            login = str(profile.get("login") or "")
            rows.append({
                "member": login,
                "full_name": profile.get("full_name"),
                "matched_terms": matched,
                "match_count": len(matched),
                "active_tasks": load.get(login, 0),
                "wip": wip.get(login, 0),
                "blocked": blocked.get(login, 0),
                "professional_profile": profile.get("professional_profile"),
                "competencies": list(profile.get("competencies") or []),
            })
            evidence.append(_profile_evidence(profile))

        rows.sort(key=lambda row: (
            -int(row["match_count"]),
            int(row["active_tasks"]),
            int(row["wip"]),
            int(row["blocked"]),
            str(row["member"]),
        ))
        recommendation = rows[0]["member"] if rows else None
        return CapabilityResult(
            answer=(
                f"Для {task.key} наиболее обоснованный кандидат по заявленным компетенциям и текущей нагрузке — {recommendation}."
                if recommendation
                else f"Для {task.key} нет достаточного совпадения с явно заявленными компетенциями команды {space}."
            ),
            data={
                "space": space,
                "sprint_id": sprint_id,
                "task_key": task.key,
                "recommendation": recommendation,
                "candidates": rows,
                "method": "declared_repository_profile_then_bounded_current_sprint_load",
                "competency_source": "task-api/config/team_members.yaml",
                "load_scope": "authoritative_current_sprint",
                "source": "REAL_AS21_PLUS_TEAM_CONFIG",
            },
            evidence=evidence + _evidence(active, "team_current_load_task"),
            warnings=[] if rows else ["insufficient_declared_competency_evidence"],
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
    CapabilitySpecV4("team.competency_match", "Match a task against declared repository-backed team competencies.", {"space": "required canonical product space", "task_key": "required canonical task key"}),
    CapabilitySpecV4("team.assignee_recommendation", "Recommend an assignee from declared repository-backed competencies plus bounded current-sprint load.", {"space": "required canonical product space", "task_key": "required canonical task key"}),
    CapabilitySpecV4("team.bottlenecks", "Describe current-sprint task concentration and blocked-task hotspots by assignee.", {"space": "required canonical product space"}),
    CapabilitySpecV4("team.distribution", "Describe current-sprint task/status distribution by assignee.", {"space": "required canonical product space"}),
    CapabilitySpecV4("release.scope", "List release membership only from bounded, source-backed release-task linkage.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
)

SKILLS = (
    SkillSpecV4(
        "team.competency_match",
        "Match a task to explicitly declared team competencies from the repository-backed team directory.",
        (
            "Resolve the product space and the task key.",
            "Call team.competency_match with space and task_key.",
            "Use only declared competencies/professional profiles from task-api/config/team_members.yaml; never invent levels or seniority.",
        ),
        ("space.resolve", "team.competency_match"),
        completion=(CompletionRequirement("team.competency_match", data_keys=("space", "task_key", "matches")),),
    ),
    SkillSpecV4(
        "team.assignee_recommendation",
        "Recommend an assignee from declared repository-backed competencies plus bounded current-sprint operational load.",
        (
            "Resolve the product space and the task key.",
            "Call team.assignee_recommendation with space and task_key.",
            "Use declared competencies plus bounded current-sprint active/WIP/blocked load only; do not tenant-scan or score employee performance.",
        ),
        ("space.resolve", "team.assignee_recommendation"),
        completion=(CompletionRequirement("team.assignee_recommendation", data_keys=("space", "task_key", "candidates")),),
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
