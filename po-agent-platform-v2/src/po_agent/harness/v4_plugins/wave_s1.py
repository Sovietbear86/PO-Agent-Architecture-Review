"""Wave S1 plugin: bounded sprint flow metrics + release search.

This plugin is intentionally self-contained and registry-discovered. Adding it
must not require Agent Core/planner/runtime business edits.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..agent_core_v4 import (
    CapabilitySpecV4,
    SkillSpecV4,
    V4CapabilityUnavailable,
    V4NeedsClarification,
)
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


def _normalize_sprint_id(value: Any) -> str:
    sprint_id = str(value or "").strip().upper()
    if not sprint_id:
        raise V4NeedsClarification("Укажите спринт.")
    return sprint_id


def _normalize_space(value: Any) -> str | None:
    space = str(value or "").strip().upper()
    return space or None


def _task_row(task: Any) -> dict[str, Any]:
    return {
        "key": task.key,
        "status": task.status_raw or task.status.value,
        "status_type": task.status_type,
        "status_category": task.status_category.value,
        "assignee": task.assignee,
        "is_open": bool(task.is_open),
        "is_completed": bool(task.is_completed),
    }


async def _sprint_tasks(runtime: Any, args: dict[str, str]):
    sprint_id = _normalize_sprint_id(args.get("sprint_id"))
    space = _normalize_space(args.get("space"))
    tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
    if not tasks:
        raise V4NeedsClarification(
            f"Не удалось подтвердить задачи спринта {sprint_id} по данным REAL AS21."
        )
    return sprint_id, space, tasks


def _sprint_evidence(sprint_id: str, label: str, value: Any) -> list[Evidence]:
    return [
        Evidence(
            type="sprint_metric",
            source="as21",
            entity_id=sprint_id,
            label=label,
            value=value,
        )
    ]


def build_sprint_scope(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        completed = [task for task in tasks if task.is_completed]
        open_tasks = [task for task in tasks if task.is_open]
        undecodable = [
            task for task in tasks
            if not task.is_completed and not task.is_open
        ]
        unassigned = [
            task for task in tasks
            if not any(
                str(value or "").strip()
                for value in (task.assignee, task.assignee_login, task.assignee_id)
            )
        ]
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "total": len(tasks),
            "completed": len(completed),
            "open": len(open_tasks),
            "undecodable_status": len(undecodable),
            "unassigned": len(unassigned),
            "task_keys": [task.key for task in tasks],
            "source": "REAL_AS21",
            "formula": "scope = complete source-backed sprint task collection",
        }
        return CapabilityResult(
            answer=(
                f"Scope {sprint_id}: всего {len(tasks)} задач, "
                f"завершено {len(completed)}, открыто {len(open_tasks)}."
            ),
            data=data,
            evidence=_sprint_evidence(sprint_id, "sprint scope", data),
        )
    return execute


def build_sprint_velocity(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        completed = [task for task in tasks if task.is_completed]
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "velocity": len(completed),
            "unit": "tasks/sprint",
            "completed": len(completed),
            "total": len(tasks),
            "task_keys": [task.key for task in completed],
            "source": "REAL_AS21",
            "formula": "task_count_velocity = completed_tasks_in_current_sprint_snapshot",
            "story_points_available": False,
        }
        return CapabilityResult(
            answer=(
                f"Скорость {sprint_id} по доступной task-count метрике: "
                f"{len(completed)} задач/спринт. Story points источником не подтверждены."
            ),
            data=data,
            evidence=_sprint_evidence(sprint_id, "sprint task-count velocity", data),
            warnings=["velocity_unit_tasks_not_story_points"],
        )
    return execute


def _parse_source_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


async def _sprint_metadata(runtime: Any, sprint_id: str, space: str | None) -> dict[str, Any]:
    list_sprints = getattr(runtime.adapter, "list_sprints", None)
    if list_sprints is None:
        raise V4CapabilityUnavailable("sprint throughput requires source-backed sprint dates")
    inferred_space = space or sprint_id.split("-SPRNT-", 1)[0]
    rows = list(await list_sprints(inferred_space))
    match = next(
        (row for row in rows if str(row.get("code") or "").strip().casefold() == sprint_id.casefold()),
        None,
    )
    if match is None:
        raise V4CapabilityUnavailable(
            f"sprint metadata is unavailable for {sprint_id}"
        )
    return match


def build_sprint_throughput(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        meta = await _sprint_metadata(runtime, sprint_id, space)
        start = _parse_source_datetime(meta.get("start_at"))
        finish = _parse_source_datetime(meta.get("finish_at"))
        if start is None:
            raise V4CapabilityUnavailable(
                "sprint throughput requires an authoritative sprint start timestamp"
            )
        now = datetime.now(tz=start.tzinfo)
        end = min(now, finish) if finish is not None else now
        if end < start:
            raise V4CapabilityUnavailable("sprint period is not active yet")
        elapsed_days = max((end - start).total_seconds() / 86400.0, 1.0)
        completed = [task for task in tasks if task.is_completed]
        throughput = len(completed) / elapsed_days
        data = {
            "sprint_id": sprint_id,
            "space": space or meta.get("space"),
            "throughput": round(throughput, 3),
            "unit": "completed_tasks/calendar_day",
            "completed": len(completed),
            "total": len(tasks),
            "elapsed_days": round(elapsed_days, 3),
            "start_at": start.isoformat(),
            "measurement_end": end.isoformat(),
            "source": "REAL_AS21",
            "formula": "completed_tasks_current_snapshot / max(1, elapsed_calendar_days)",
        }
        return CapabilityResult(
            answer=(
                f"Throughput {sprint_id}: {data['throughput']} завершённых задач/день "
                f"по текущему snapshot."
            ),
            data=data,
            evidence=_sprint_evidence(sprint_id, "sprint throughput", data),
            warnings=["throughput_is_current_snapshot_rate"],
        )
    return execute


_WIP_BACKLOG_TYPES = frozenset({"open", "todo", "backlog", "registered"})


def _is_wip(task: Any) -> bool:
    if not task.is_open:
        return False
    status_type = str(task.status_type or "").strip().casefold()
    if status_type in _WIP_BACKLOG_TYPES:
        return False
    if task.status_category.value == "backlog":
        return False
    return True


def build_sprint_wip(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        wip = [task for task in tasks if _is_wip(task)]
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "wip": len(wip),
            "unit": "tasks",
            "total": len(tasks),
            "task_keys": [task.key for task in wip],
            "tasks": [_task_row(task) for task in wip],
            "source": "REAL_AS21",
            "formula": (
                "WIP = non-terminal tasks excluding source backlog/open/todo/registered states"
            ),
        }
        return CapabilityResult(
            answer=f"WIP {sprint_id}: {len(wip)} задач в работе.",
            data=data,
            evidence=[
                Evidence(
                    type="task",
                    source="as21",
                    entity_id=task.key,
                    label="sprint WIP",
                    value=task.status_raw or task.status.value,
                )
                for task in wip
            ],
        )
    return execute


def _version_row(value: Any) -> dict[str, Any] | None:
    if isinstance(value, str):
        release_id = value.strip()
        return {"id": release_id, "name": release_id} if release_id else None
    if not isinstance(value, dict):
        return None
    release_id = str(
        value.get("id")
        or value.get("code")
        or value.get("version")
        or value.get("name")
        or ""
    ).strip()
    if not release_id:
        return None
    return {
        "id": release_id,
        "name": str(value.get("name") or release_id),
        "status": value.get("status") or value.get("state"),
        "raw": value,
    }


def build_release_search(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        space = _normalize_space(args.get("space"))
        query = str(args.get("query") or "").strip() or None
        require_single = str(args.get("require_single") or "").strip().casefold() in {
            "1", "true", "yes", "y",
        }
        search = getattr(runtime.adapter, "search_versions_bounded", None)
        if search is None:
            raise V4CapabilityUnavailable(
                "release.search requires a bounded source-backed release directory"
            )
        raw = await search(query=query, space=space)
        if not isinstance(raw, list):
            raise V4CapabilityUnavailable("release directory returned malformed data")
        rows = []
        seen = set()
        for item in raw:
            row = _version_row(item)
            if row is None or row["id"].casefold() in seen:
                continue
            seen.add(row["id"].casefold())
            rows.append(row)
        if not rows:
            raise V4NeedsClarification(
                "В REAL AS21 не найден подходящий релиз. Уточните название или идентификатор."
            )
        if require_single and len(rows) != 1:
            raise V4NeedsClarification(
                "Найдено несколько релизов. Какой использовать?",
                options=tuple(row["id"] for row in rows),
            )
        data = {
            "space": space,
            "query": query,
            "count": len(rows),
            "releases": rows,
            "release_id": rows[0]["id"] if len(rows) == 1 else None,
            "source": "REAL_AS21",
            "bounded": True,
        }
        return CapabilityResult(
            answer=(
                f"Найден релиз: {rows[0]['id']}."
                if len(rows) == 1
                else "Найдены релизы: " + ", ".join(row["id"] for row in rows) + "."
            ),
            data=data,
            evidence=[
                Evidence(
                    type="release",
                    source="as21",
                    entity_id=row["id"],
                    label=row["name"],
                    value=row.get("status"),
                )
                for row in rows
            ],
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4(
        "sprint.scope",
        "Calculate exact current sprint scope from the complete REAL AS21 sprint task collection.",
        {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"},
    ),
    CapabilitySpecV4(
        "sprint.velocity",
        "Calculate task-count velocity from current REAL AS21 sprint completion state; unit is tasks/sprint, never story points unless source adds them.",
        {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"},
    ),
    CapabilitySpecV4(
        "sprint.throughput",
        "Calculate current snapshot throughput as completed tasks per elapsed calendar day using REAL AS21 sprint dates.",
        {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"},
    ),
    CapabilitySpecV4(
        "sprint.wip",
        "Calculate current WIP from source-backed non-terminal sprint tasks excluding backlog/open/todo/registered states.",
        {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"},
    ),
    CapabilitySpecV4(
        "release.search",
        "Search a bounded REAL AS21 release/version directory by optional product space and query.",
        {
            "space": "optional canonical product space",
            "query": "optional release/version text",
            "require_single": "optional true when another skill needs exactly one release",
        },
    ),
)

SKILLS = (
    SkillSpecV4(
        "sprint.scope",
        "Show exact current scope of a sprint from the complete live sprint collection.",
        (
            "If the user supplied a sprint id, validate it with sprint.resolve.",
            "If the user supplied a month/period, resolve it with space.resolve + sprint.search.",
            "If the user supplied only a product/space (for example 'scope sprint DMS') or explicitly asks for the current sprint, use space.resolve + sprint.current.",
            "Then call sprint.scope with the resolved sprint_id; identity-only observations must not terminate the metric request.",
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.scope"),
        completion=(CompletionRequirement("sprint.scope", data_keys=("sprint_id", "total", "task_key_count")),),
    ),
    SkillSpecV4(
        "sprint.velocity",
        "Show sprint velocity using the explicitly defined task-count unit supported by the source.",
        (
            "Resolve the sprint generically: explicit id -> sprint.resolve; month/period -> space.resolve + sprint.search; product-only/current-sprint request -> space.resolve + sprint.current.",
            "Then call sprint.velocity with the resolved sprint_id.",
            "Never imply story-point velocity when story points are not source-backed.",
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.velocity"),
        completion=(CompletionRequirement("sprint.velocity", data_keys=("sprint_id", "velocity", "unit")),),
    ),
    SkillSpecV4(
        "sprint.throughput",
        "Show current sprint throughput as completed tasks per elapsed calendar day.",
        (
            "Resolve the sprint generically: explicit id -> sprint.resolve; month/period -> space.resolve + sprint.search; product-only/current-sprint request -> space.resolve + sprint.current.",
            "Then call sprint.throughput with the resolved sprint_id.",
            "Keep the snapshot formula/unit visible; do not present it as historical event throughput.",
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.throughput"),
        completion=(CompletionRequirement("sprint.throughput", data_keys=("sprint_id", "throughput", "unit")),),
    ),
    SkillSpecV4(
        "sprint.wip",
        "Show current sprint work-in-progress from source-backed task states.",
        (
            "Resolve the sprint generically: explicit id -> sprint.resolve; month/period -> space.resolve + sprint.search; product-only/current-sprint request -> space.resolve + sprint.current.",
            "Then call sprint.wip with the resolved sprint_id; never guess a sprint id from product name.",
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", "sprint.wip"),
        completion=(CompletionRequirement("sprint.wip", data_keys=("sprint_id", "wip", "task_key_count")),),
    ),
    SkillSpecV4(
        "release.search",
        "Find real releases/versions by space, name or identifier using the bounded source directory.",
        (
            "Validate product space when the user supplied one, then call release.search.",
            "For a direct search/list request leave require_single false.",
            "When another skill needs exactly one release, use require_single=true so ambiguity becomes typed clarification.",
            "Never treat a product space such as DMS as a release id.",
        ),
        ("space.resolve", "release.search"),
        completion=(CompletionRequirement("release.search", data_keys=("releases", "count")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("sprint.scope", handler_builder=build_sprint_scope),
    CapabilityBindingV4("sprint.velocity", handler_builder=build_sprint_velocity),
    CapabilityBindingV4("sprint.throughput", handler_builder=build_sprint_throughput),
    CapabilityBindingV4("sprint.wip", handler_builder=build_sprint_wip),
    CapabilityBindingV4("release.search", handler_builder=build_release_search),
)

UI = {
    "sprint.scope": UIContractV4(
        "analysis", preferred_widget="sprint_scope", required_fields=("sprint_id", "total")
    ),
    "sprint.velocity": UIContractV4(
        "analysis", preferred_widget="sprint_metric", required_fields=("sprint_id", "velocity", "unit")
    ),
    "sprint.throughput": UIContractV4(
        "analysis", preferred_widget="sprint_metric", required_fields=("sprint_id", "throughput", "unit")
    ),
    "sprint.wip": UIContractV4(
        "task_collection", preferred_widget="task_table", required_fields=("sprint_id", "wip", "tasks")
    ),
    "release.search": UIContractV4(
        "release_collection", preferred_widget="release_list", required_fields=("releases", "count")
    ),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.wave_s1.sprint_flow_release_search",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
