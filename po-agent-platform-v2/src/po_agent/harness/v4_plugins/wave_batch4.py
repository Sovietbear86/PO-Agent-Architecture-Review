"""Batch 4 plugin: release analytics + portfolio overview.

Release analytics are strictly downstream of authoritative release membership.
With the current A214 source contract that membership is unpopulated, so all
release-derived metrics fail closed instead of treating zero rows as real scope.

Portfolio overview is a bounded cross-space current-sprint summary over the
configured product-space allow-list. It never performs a tenant-wide task scan.
"""
from __future__ import annotations

from typing import Any

from po_agent.domain.models import TaskPriority

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..production_entity_grounding_v2 import APPROVED_PRODUCT_SPACES
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


_WIP_BACKLOG_TYPES = frozenset({"open", "todo", "backlog", "registered"})


def _space(args: dict[str, str]) -> str:
    value = str(args.get("space") or "").strip().upper()
    if not value:
        raise V4NeedsClarification("Укажите продукт/пространство релиза.")
    return value


def _release_id(args: dict[str, str]) -> str:
    value = str(args.get("release_id") or "").strip()
    if not value:
        raise V4NeedsClarification("Укажите релиз.")
    return value


async def _release_tasks(runtime: Any, args: dict[str, str]):
    space = _space(args)
    release_id = _release_id(args)
    tasks = list(await runtime.adapter.get_release_tasks(release_id, space))
    if not tasks:
        raise V4CapabilityUnavailable(
            "release analytics require authoritative release-to-task membership; "
            "the current REAL AS21 source does not expose populated release linkage"
        )
    return space, release_id, tasks


def _task_row(task: Any) -> dict[str, Any]:
    return {
        "key": task.key,
        "title": task.title,
        "status": task.status_raw or task.status.value,
        "assignee": task.assignee_login or task.assignee_id or task.assignee,
        "priority": task.priority.value if task.priority else None,
        "blocked": bool(task.is_blocked),
        "completed": bool(task.is_completed),
        "estimate_hours": task.estimate_hours,
        "depends_on": list(task.depends_on),
        "age_days": task.age_days,
    }


def _evidence(tasks: list[Any], kind: str) -> list[Evidence]:
    return [
        Evidence(
            type=kind,
            source="as21",
            entity_id=task.key,
            label=task.title,
            value=task.status_raw or task.status.value,
        )
        for task in tasks
    ]


def build_release_progress(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, release_id, tasks = await _release_tasks(runtime, args)
        total = len(tasks)
        completed = [task for task in tasks if task.is_completed]
        blocked = [task for task in tasks if task.is_blocked]
        active = [task for task in tasks if task.is_open]
        with_estimate = [task for task in tasks if isinstance(task.estimate_hours, (int, float))]
        estimate_coverage = round(len(with_estimate) / total * 100.0, 1) if total else 0.0
        effort = None
        if len(with_estimate) == total and total:
            total_est = sum(float(task.estimate_hours) for task in tasks)
            done_est = sum(float(task.estimate_hours) for task in completed)
            effort = {
                "estimated_hours_total": round(total_est, 2),
                "estimated_hours_completed": round(done_est, 2),
                "completion_percent": round(done_est / total_est * 100.0, 1) if total_est > 0 else None,
            }
        data = {
            "space": space,
            "release_id": release_id,
            "total": total,
            "completed": len(completed),
            "active": len(active),
            "blocked": len(blocked),
            "task_completion_percent": round(len(completed) / total * 100.0, 1) if total else 0.0,
            "estimate_coverage_percent": estimate_coverage,
            "effort_progress": effort,
            "source": "REAL_AS21",
            "membership": "source_backed_release_task_query",
        }
        return CapabilityResult(
            answer=(
                f"{release_id}: выполнено {len(completed)}/{total} "
                f"({data['task_completion_percent']:g}%), заблокировано {len(blocked)}."
            ),
            data=data,
            evidence=_evidence(tasks, "release_progress_task"),
            warnings=[] if effort is not None else ["effort_progress_unavailable_incomplete_estimates"],
        )
    return execute


def build_release_blockers(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, release_id, tasks = await _release_tasks(runtime, args)
        blocked = [task for task in tasks if task.is_blocked]
        return CapabilityResult(
            answer=f"В релизе {release_id} заблокировано задач: {len(blocked)}.",
            data={
                "space": space,
                "release_id": release_id,
                "count": len(blocked),
                "task_keys": [task.key for task in blocked],
                "tasks": [_task_row(task) for task in blocked],
                "source": "REAL_AS21",
                "membership": "source_backed_release_task_query",
            },
            evidence=_evidence(blocked, "release_blocker_task"),
        )
    return execute


def build_release_dependencies(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, release_id, tasks = await _release_tasks(runtime, args)
        release_keys = {task.key for task in tasks}
        internal = []
        external = []
        for task in tasks:
            for dependency in task.depends_on:
                edge = {"task_key": task.key, "depends_on": dependency}
                (internal if dependency in release_keys else external).append(edge)
        return CapabilityResult(
            answer=(
                f"{release_id}: внутренних зависимостей {len(internal)}, "
                f"внешних {len(external)}."
            ),
            data={
                "space": space,
                "release_id": release_id,
                "internal": internal,
                "external": external,
                "dependency_count": len(internal) + len(external),
                "source": "REAL_AS21",
                "membership": "source_backed_release_task_query",
            },
            evidence=_evidence(tasks, "release_dependency_source"),
        )
    return execute


def build_release_risk_queue(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space, release_id, tasks = await _release_tasks(runtime, args)
        queue = []
        for task in tasks:
            score = 0
            reasons: list[str] = []
            if task.is_blocked:
                score += 50
                reasons.append("blocked")
            if task.priority in (TaskPriority.CRITICAL, TaskPriority.URGENT):
                score += 30
                reasons.append("high_priority")
            elif task.priority == TaskPriority.HIGH:
                score += 15
                reasons.append("priority_high")
            if not (task.assignee_login or task.assignee_id or task.assignee) and not task.is_completed:
                score += 15
                reasons.append("unassigned")
            if task.age_days >= 14 and not task.is_completed:
                score += 10
                reasons.append("aging_14d")
            if score:
                queue.append({
                    "task": _task_row(task),
                    "risk_score": min(score, 100),
                    "reasons": reasons,
                })
        queue.sort(key=lambda item: (-item["risk_score"], item["task"]["key"]))
        return CapabilityResult(
            answer=f"В очереди рисков релиза {release_id}: {len(queue)} задач.",
            data={
                "space": space,
                "release_id": release_id,
                "risk_count": len(queue),
                "risk_queue": queue,
                "scoring_version": "release_risk_v1",
                "source": "REAL_AS21",
                "membership": "source_backed_release_task_query",
            },
            evidence=_evidence(
                [task for task in tasks if any(row["task"]["key"] == task.key for row in queue)],
                "release_risk_task",
            ),
            warnings=["risk_score_is_deterministic_operational_priority_not_employee_score"],
        )
    return execute


def _is_wip(task: Any) -> bool:
    if not task.is_open:
        return False
    status_type = str(task.status_type or "").strip().casefold()
    status_category = str(getattr(task.status_category, "value", "") or "").casefold()
    return status_type not in _WIP_BACKLOG_TYPES and status_category != "backlog"


def build_portfolio_overview(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        rows = []
        evidence: list[Evidence] = []
        for space in sorted(APPROVED_PRODUCT_SPACES):
            getter = getattr(runtime.adapter, "get_current_sprint_id", None)
            if getter is None:
                raise V4CapabilityUnavailable("portfolio.overview requires current-sprint source support")
            try:
                sprint_id = await getter(space)
            except Exception:
                # Source exceptions must not be hidden as an empty product row.
                raise
            if not sprint_id:
                rows.append({
                    "space": space,
                    "state": "NO_CURRENT_SPRINT",
                    "sprint_id": None,
                    "total": None,
                    "completed": None,
                    "open": None,
                    "blocked": None,
                    "wip": None,
                })
                continue
            tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
            if not tasks:
                rows.append({
                    "space": space,
                    "state": "CURRENT_SPRINT_WITHOUT_MEMBERSHIP",
                    "sprint_id": sprint_id,
                    "total": None,
                    "completed": None,
                    "open": None,
                    "blocked": None,
                    "wip": None,
                })
                continue
            completed = sum(1 for task in tasks if task.is_completed)
            open_count = sum(1 for task in tasks if task.is_open)
            blocked = sum(1 for task in tasks if task.is_blocked)
            wip = sum(1 for task in tasks if _is_wip(task))
            row = {
                "space": space,
                "state": "SOURCE_BACKED",
                "sprint_id": sprint_id,
                "total": len(tasks),
                "completed": completed,
                "open": open_count,
                "blocked": blocked,
                "wip": wip,
                "completion_percent": round(completed / len(tasks) * 100.0, 1),
            }
            rows.append(row)
            evidence.append(Evidence(
                type="portfolio_sprint",
                source="as21",
                entity_id=sprint_id,
                label=space,
                value=row,
            ))
        source_backed = [row for row in rows if row["state"] == "SOURCE_BACKED"]
        data = {
            "spaces": rows,
            "space_count": len(rows),
            "source_backed_space_count": len(source_backed),
            "total_current_sprint_tasks": sum(int(row["total"]) for row in source_backed),
            "total_blocked": sum(int(row["blocked"]) for row in source_backed),
            "source": "REAL_AS21",
            "scope": "approved_product_spaces_current_sprints",
        }
        return CapabilityResult(
            answer=(
                f"Портфель: {len(source_backed)}/{len(rows)} пространств имеют "
                f"подтверждённый текущий спринт с задачами; заблокировано {data['total_blocked']} задач."
            ),
            data=data,
            evidence=evidence,
            warnings=[
                "portfolio_overview_is_current_sprint_operational_snapshot",
                "spaces_without_current_sprint_are_reported_not_inferred",
            ],
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("release.progress", "Calculate release task-count progress only from authoritative release membership.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
    CapabilitySpecV4("release.blockers", "List blocked release tasks only from authoritative release membership.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
    CapabilitySpecV4("release.dependencies", "Analyze task dependency edges inside/outside a release only from authoritative release membership.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
    CapabilitySpecV4("release.risk_queue", "Build deterministic operational release risk queue only from authoritative release membership.", {"space": "required canonical product space", "release_id": "required source-backed release id"}),
    CapabilitySpecV4("portfolio.overview", "Summarize current-sprint operational state across the configured approved product spaces using only bounded per-space source reads.", {}),
)

_RELEASE_CAPS = ("space.resolve", "release.search")

SKILLS = (
    SkillSpecV4(
        "release.progress",
        "Show release completion only when source-backed release membership exists.",
        ("Resolve space and release with release.search(require_single=true), then call release.progress.", "If membership is unavailable, fail closed; never treat zero rows as a real zero-scope release."),
        _RELEASE_CAPS + ("release.progress",),
        completion=(CompletionRequirement("release.progress", data_keys=("release_id", "total")),),
    ),
    SkillSpecV4(
        "release.blockers",
        "Show blocked tasks of a release only from authoritative release membership.",
        ("Resolve space and release, then call release.blockers.",),
        _RELEASE_CAPS + ("release.blockers",),
        completion=(CompletionRequirement("release.blockers", data_keys=("release_id", "count")),),
    ),
    SkillSpecV4(
        "release.dependencies",
        "Show internal/external dependency edges of a release only from authoritative release membership.",
        ("Resolve space and release, then call release.dependencies.",),
        _RELEASE_CAPS + ("release.dependencies",),
        completion=(CompletionRequirement("release.dependencies", data_keys=("release_id", "dependency_count")),),
    ),
    SkillSpecV4(
        "release.risk_queue",
        "Show a deterministic operational release risk queue only from authoritative release membership.",
        ("Resolve space and release, then call release.risk_queue.", "Risk score is task operational priority, not employee scoring."),
        _RELEASE_CAPS + ("release.risk_queue",),
        completion=(CompletionRequirement("release.risk_queue", data_keys=("release_id", "risk_count")),),
    ),
    SkillSpecV4(
        "portfolio.overview",
        "Show a bounded operational portfolio snapshot over approved product spaces and their current sprints.",
        ("Call portfolio.overview. Preserve spaces with no current sprint as explicit states rather than inventing data.",),
        ("portfolio.overview",),
        completion=(CompletionRequirement("portfolio.overview", data_keys=("space_count", "source_backed_space_count")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("release.progress", handler_builder=build_release_progress),
    CapabilityBindingV4("release.blockers", handler_builder=build_release_blockers),
    CapabilityBindingV4("release.dependencies", handler_builder=build_release_dependencies),
    CapabilityBindingV4("release.risk_queue", handler_builder=build_release_risk_queue),
    CapabilityBindingV4("portfolio.overview", handler_builder=build_portfolio_overview),
)

UI = {
    "release.progress": UIContractV4("analysis", preferred_widget="release_progress", required_fields=("release_id", "total")),
    "release.blockers": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("release_id", "count", "tasks")),
    "release.dependencies": UIContractV4("analysis", preferred_widget="dependency_graph", required_fields=("release_id", "internal", "external")),
    "release.risk_queue": UIContractV4("task_collection", preferred_widget="risk_queue", required_fields=("release_id", "risk_queue")),
    "portfolio.overview": UIContractV4("analysis", preferred_widget="portfolio_overview", required_fields=("spaces", "space_count")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.batch4.release_portfolio",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
