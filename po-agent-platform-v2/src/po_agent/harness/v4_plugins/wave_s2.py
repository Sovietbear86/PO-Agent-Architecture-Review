"""Wave S2 plugin: five sprint analytics skills.

Batch policy: >=5 skills per owner wave when dependencies allow.
This plugin is registry-discovered and contains no Agent Core routing edits.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from statistics import mean, median
from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
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


async def _sprint_tasks(runtime: Any, args: dict[str, str]):
    sprint_id = _normalize_sprint_id(args.get("sprint_id"))
    space = _normalize_space(args.get("space"))
    tasks = list(await runtime.adapter.get_sprint_tasks(sprint_id, space))
    if not tasks:
        raise V4NeedsClarification(
            f"Не удалось подтвердить задачи спринта {sprint_id} по данным REAL AS21."
        )
    return sprint_id, space, tasks


def _metric_evidence(sprint_id: str, label: str, value: Any) -> list[Evidence]:
    return [Evidence(type="sprint_metric", source="as21", entity_id=sprint_id, label=label, value=value)]


def _source_flag(task: Any, name: str) -> bool:
    source_data = getattr(task, "source_data", None)
    return isinstance(source_data, dict) and source_data.get(name) is True


def _aware_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc) if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


async def _completed_history_metrics(runtime: Any, sprint_id: str, tasks: list[Any]) -> list[dict[str, Any]]:
    completed = [task for task in tasks if task.is_completed]
    if not completed:
        raise V4CapabilityUnavailable(f"{sprint_id}: нет завершённых задач для history-based метрики")
    missing_created = [
        task.key for task in completed
        if not _source_flag(task, "_canonical_created_at_from_source")
    ]
    if missing_created:
        raise V4CapabilityUnavailable(
            f"{sprint_id}: sprint task rows lack source created_at: {', '.join(missing_created[:8])}"
        )

    semaphore = asyncio.Semaphore(8)

    async def one(task: Any):
        async with semaphore:
            transitions = list(await runtime.adapter.get_task_history(task.key))
        if not transitions:
            return None
        ordered = sorted(transitions, key=lambda item: _aware_utc(item.timestamp))
        first_transition = _aware_utc(ordered[0].timestamp)
        terminal_transition = _aware_utc(ordered[-1].timestamp)
        created_at = _aware_utc(task.created_at)
        if terminal_transition < first_transition or terminal_transition < created_at:
            raise V4CapabilityUnavailable(f"{task.key}: неконсистентная временная шкала истории")
        return {
            "task_key": task.key,
            "created_at": created_at,
            "cycle_start": first_transition,
            "terminal_at": terminal_transition,
            "cycle_hours": (terminal_transition - first_transition).total_seconds() / 3600.0,
            "lead_hours": (terminal_transition - task.created_at).total_seconds() / 3600.0,
        }

    rows = list(await asyncio.gather(*(one(task) for task in completed)))
    missing = [task.key for task, row in zip(completed, rows) if row is None]
    if missing:
        raise V4CapabilityUnavailable(
            f"{sprint_id}: history неполна для завершённых задач: {', '.join(missing[:8])}"
        )
    return [row for row in rows if row is not None]


def _summary(values: list[float]) -> dict[str, float]:
    return {
        "avg": round(mean(values), 2),
        "median": round(median(values), 2),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
    }


def build_sprint_cycle_time(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        rows = await _completed_history_metrics(runtime, sprint_id, tasks)
        values = [row["cycle_hours"] for row in rows]
        summary = _summary(values)
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "completed_sample": len(rows),
            "cycle_time_hours": summary,
            "task_metrics": [
                {
                    "task_key": row["task_key"],
                    "cycle_start": row["cycle_start"].isoformat(),
                    "terminal_at": row["terminal_at"].isoformat(),
                    "cycle_hours": round(row["cycle_hours"], 2),
                }
                for row in rows
            ],
            "source": "REAL_AS21_HISTORY",
            "formula": "terminal workflow transition - first workflow status transition; completed tasks only",
        }
        return CapabilityResult(
            answer=(
                f"Cycle time {sprint_id}: медиана {summary['median']} ч, "
                f"среднее {summary['avg']} ч по {len(rows)} завершённым задачам."
            ),
            data=data,
            evidence=_metric_evidence(sprint_id, "sprint cycle time", summary),
            warnings=["cycle_time_completed_tasks_only", "cycle_start_first_workflow_transition"],
        )
    return execute


def build_sprint_lead_time(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        rows = await _completed_history_metrics(runtime, sprint_id, tasks)
        values = [row["lead_hours"] for row in rows]
        summary = _summary(values)
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "completed_sample": len(rows),
            "lead_time_hours": summary,
            "task_metrics": [
                {
                    "task_key": row["task_key"],
                    "created_at": row["created_at"].isoformat(),
                    "terminal_at": row["terminal_at"].isoformat(),
                    "lead_hours": round(row["lead_hours"], 2),
                }
                for row in rows
            ],
            "source": "REAL_AS21_HISTORY",
            "formula": "terminal workflow transition - authoritative task created_at; completed tasks only",
        }
        return CapabilityResult(
            answer=(
                f"Lead time {sprint_id}: медиана {summary['median']} ч, "
                f"среднее {summary['avg']} ч по {len(rows)} завершённым задачам."
            ),
            data=data,
            evidence=_metric_evidence(sprint_id, "sprint lead time", summary),
            warnings=["lead_time_completed_tasks_only"],
        )
    return execute


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


async def _previous_sprint_id(runtime: Any, sprint_id: str, space: str | None) -> str:
    list_sprints = getattr(runtime.adapter, "list_sprints", None)
    if list_sprints is None:
        raise V4CapabilityUnavailable("carryover requires source-backed sprint directory")
    inferred_space = space or sprint_id.split("-SPRNT-", 1)[0]
    rows = list(await list_sprints(inferred_space))
    current = next((row for row in rows if str(row.get("code") or "").upper() == sprint_id), None)
    if current is None:
        raise V4CapabilityUnavailable(f"Не найдены метаданные спринта {sprint_id}")
    current_start = _parse_dt(current.get("start_at"))
    if current_start is None:
        raise V4CapabilityUnavailable(f"{sprint_id}: отсутствует authoritative start_at")
    candidates = []
    for row in rows:
        code = str(row.get("code") or "").strip().upper()
        if not code or code == sprint_id:
            continue
        finish = _parse_dt(row.get("finish_at"))
        start = _parse_dt(row.get("start_at"))
        boundary = finish or start
        if boundary is not None and boundary <= current_start:
            candidates.append((boundary, code))
    if not candidates:
        raise V4CapabilityUnavailable(f"{sprint_id}: не найден предыдущий source-backed спринт")
    candidates.sort()
    return candidates[-1][1]


def build_sprint_carryover(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, current_tasks = await _sprint_tasks(runtime, args)
        previous_id = str(args.get("previous_sprint_id") or "").strip().upper()
        if not previous_id:
            previous_id = await _previous_sprint_id(runtime, sprint_id, space)
        previous_tasks = list(await runtime.adapter.get_sprint_tasks(previous_id, space))
        if not previous_tasks:
            raise V4CapabilityUnavailable(f"{previous_id}: previous sprint task set unavailable")
        current_keys = {task.key for task in current_tasks}
        previous_keys = {task.key for task in previous_tasks}
        carryover = sorted(current_keys & previous_keys)
        data = {
            "sprint_id": sprint_id,
            "previous_sprint_id": previous_id,
            "space": space,
            "carryover": len(carryover),
            "current_total": len(current_keys),
            "previous_total": len(previous_keys),
            "carryover_ratio_current": round(len(carryover) / len(current_keys), 4) if current_keys else 0.0,
            "task_keys": carryover,
            "source": "REAL_AS21",
            "formula": "intersection(previous complete sprint membership, current complete sprint membership)",
        }
        return CapabilityResult(
            answer=(
                f"Carryover {previous_id} → {sprint_id}: {len(carryover)} задач "
                f"({data['carryover_ratio_current']:.1%} текущего scope)."
            ),
            data=data,
            evidence=[
                Evidence(type="task", source="as21", entity_id=key, label="carryover", value=previous_id)
                for key in carryover
            ],
        )
    return execute


def _baseline_total(meta: dict[str, Any]) -> int | None:
    for key in ("committed_count", "baseline_total", "planned_count", "scope_at_start"):
        value = meta.get(key)
        if isinstance(value, int) and value >= 0:
            return value
    committed = meta.get("committed_tasks")
    if isinstance(committed, list):
        return len({str(item) for item in committed if item})
    return None


async def _sprint_meta(runtime: Any, sprint_id: str, space: str | None) -> dict[str, Any]:
    list_sprints = getattr(runtime.adapter, "list_sprints", None)
    if list_sprints is None:
        raise V4CapabilityUnavailable("predictability requires source-backed sprint baseline")
    inferred_space = space or sprint_id.split("-SPRNT-", 1)[0]
    rows = list(await list_sprints(inferred_space))
    meta = next((row for row in rows if str(row.get("code") or "").upper() == sprint_id), None)
    if meta is None:
        raise V4CapabilityUnavailable(f"{sprint_id}: sprint metadata unavailable")
    return meta


def build_sprint_predictability(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        meta = await _sprint_meta(runtime, sprint_id, space)
        baseline = _baseline_total(meta)
        if baseline is None:
            raise V4CapabilityUnavailable(
                "sprint.predictability requires committed/baseline scope from REAL AS21; current scope is not a substitute"
            )
        completed = sum(1 for task in tasks if task.is_completed)
        ratio = round(completed / baseline, 4) if baseline else 1.0
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "baseline_committed": baseline,
            "completed": completed,
            "predictability": ratio,
            "unit": "completed/current_committed_baseline",
            "source": "REAL_AS21",
            "formula": "completed tasks / authoritative committed baseline",
        }
        return CapabilityResult(
            answer=f"Predictability {sprint_id}: {ratio:.1%} ({completed}/{baseline}).",
            data=data,
            evidence=_metric_evidence(sprint_id, "sprint predictability", data),
        )
    return execute


def build_sprint_risk_queue(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        sprint_id, space, tasks = await _sprint_tasks(runtime, args)
        now = datetime.now(timezone.utc)
        rows = []
        missing_created = 0
        missing_deadline = 0
        for task in tasks:
            if not task.is_open:
                continue
            created_from_source = _source_flag(task, "_canonical_created_at_from_source")
            deadline_from_source = _source_flag(task, "_canonical_deadline_from_source")
            if not created_from_source:
                missing_created += 1
            if task.due_date is not None and not deadline_from_source:
                missing_deadline += 1

            overdue_days = 0
            if task.due_date is not None and deadline_from_source:
                due = _aware_utc(task.due_date)
                overdue_days = max(0, (now - due).days)

            age_days = 0
            if created_from_source:
                created = _aware_utc(task.created_at)
                age_days = max(0, (now - created).days)

            reasons = []
            if task.is_blocked:
                reasons.append("blocked")
            if overdue_days > 0:
                reasons.append(f"overdue:{overdue_days}d")
            if age_days >= 14:
                reasons.append(f"aging:{age_days}d")
            if not reasons:
                continue
            rows.append({
                "task_key": task.key,
                "title": task.title,
                "status": task.status_raw or task.status.value,
                "assignee": task.assignee,
                "blocked": bool(task.is_blocked),
                "overdue_days": overdue_days,
                "age_days": age_days,
                "reasons": reasons,
            })
        rows.sort(key=lambda row: (not row["blocked"], -row["overdue_days"], -row["age_days"], row["task_key"]))
        for index, row in enumerate(rows, start=1):
            row["rank"] = index
        data = {
            "sprint_id": sprint_id,
            "space": space,
            "count": len(rows),
            "queue": rows,
            "source": "REAL_AS21",
            "formula": "blocked first, then overdue_days desc, then age_days desc; no employee scoring",
        }
        warnings = []
        limitations = []
        if missing_created:
            warnings.append("risk_queue_created_at_source_missing")
            limitations.append(f"aging недоступен для {missing_created} открытых задач")
        if missing_deadline:
            warnings.append("risk_queue_deadline_source_missing")
            limitations.append(f"deadline недоступен для {missing_deadline} открытых задач")
        caveat = f" Ограничения источника: {'; '.join(limitations)}." if limitations else ""
        return CapabilityResult(
            answer=f"Очередь рисков {sprint_id}: {len(rows)} задач требуют внимания.{caveat}",
            data=data,
            evidence=[
                Evidence(type="task_risk", source="as21", entity_id=row["task_key"], label=";".join(row["reasons"]), value=row["rank"])
                for row in rows
            ],
            warnings=warnings,
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("sprint.cycle_time", "Calculate completed-task cycle time from authoritative workflow history.", {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"}),
    CapabilitySpecV4("sprint.lead_time", "Calculate completed-task lead time from created_at to terminal workflow transition.", {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"}),
    CapabilitySpecV4("sprint.carryover", "Calculate carryover as task-key intersection between previous and current complete sprint memberships.", {"sprint_id": "required canonical sprint id", "space": "optional canonical product space", "previous_sprint_id": "optional explicit previous sprint"}),
    CapabilitySpecV4("sprint.predictability", "Calculate predictability only when an authoritative committed/baseline scope exists.", {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"}),
    CapabilitySpecV4("sprint.risk_queue", "Build an evidence-backed task attention queue from blocked/overdue/aging facts; never score people.", {"sprint_id": "required canonical sprint id", "space": "optional canonical product space"}),
)


def _metric_skill(skill_id: str, description: str, metric_capability: str, completion_keys: tuple[str, ...], extra: tuple[str, ...] = ()) -> SkillSpecV4:
    return SkillSpecV4(
        skill_id,
        description,
        (
            "Resolve sprint generically: explicit id -> sprint.resolve; period/month -> space.resolve + sprint.search; product-only/current -> space.resolve + sprint.current.",
            f"Then call {metric_capability} with the resolved sprint_id.",
            *extra,
        ),
        ("space.resolve", "sprint.resolve", "sprint.search", "sprint.current", metric_capability),
        completion=(CompletionRequirement(metric_capability, data_keys=completion_keys),),
    )


SKILLS = (
    _metric_skill(
        "sprint.cycle_time",
        "Show cycle-time distribution for completed sprint tasks from authoritative history.",
        "sprint.cycle_time",
        ("sprint_id", "completed_sample", "cycle_time_hours"),
        ("Use completed tasks only; do not infer missing histories.",),
    ),
    _metric_skill(
        "sprint.lead_time",
        "Show lead-time distribution for completed sprint tasks from authoritative history.",
        "sprint.lead_time",
        ("sprint_id", "completed_sample", "lead_time_hours"),
        ("Use completed tasks only; created_at and terminal transition must be source-backed.",),
    ),
    _metric_skill(
        "sprint.carryover",
        "Show tasks carried from the immediately previous source-backed sprint into this sprint.",
        "sprint.carryover",
        ("sprint_id", "previous_sprint_id", "carryover", "task_key_count"),
        ("If previous_sprint_id was not supplied, resolve the predecessor from authoritative sprint dates.",),
    ),
    _metric_skill(
        "sprint.predictability",
        "Show completed-vs-committed sprint predictability only when an authoritative baseline exists.",
        "sprint.predictability",
        ("sprint_id", "baseline_committed", "completed", "predictability"),
        ("Never substitute current scope for a missing committed baseline; fail closed instead.",),
    ),
    _metric_skill(
        "sprint.risk_queue",
        "Show a sprint task attention queue using blocked, overdue and aging evidence only.",
        "sprint.risk_queue",
        ("sprint_id", "count"),
        ("Rank tasks, not people; preserve evidence/reasons for every item.",),
    ),
)

BINDINGS = (
    CapabilityBindingV4("sprint.cycle_time", handler_builder=build_sprint_cycle_time),
    CapabilityBindingV4("sprint.lead_time", handler_builder=build_sprint_lead_time),
    CapabilityBindingV4("sprint.carryover", handler_builder=build_sprint_carryover),
    CapabilityBindingV4("sprint.predictability", handler_builder=build_sprint_predictability),
    CapabilityBindingV4("sprint.risk_queue", handler_builder=build_sprint_risk_queue),
)

UI = {
    "sprint.cycle_time": UIContractV4("analysis", preferred_widget="sprint_metric", required_fields=("sprint_id", "cycle_time_hours")),
    "sprint.lead_time": UIContractV4("analysis", preferred_widget="sprint_metric", required_fields=("sprint_id", "lead_time_hours")),
    "sprint.carryover": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("sprint_id", "carryover")),
    "sprint.predictability": UIContractV4("analysis", preferred_widget="sprint_metric", required_fields=("sprint_id", "predictability")),
    "sprint.risk_queue": UIContractV4("task_collection", preferred_widget="task_table", required_fields=("sprint_id", "count", "queue")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.wave_s2.sprint_history_risk",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
