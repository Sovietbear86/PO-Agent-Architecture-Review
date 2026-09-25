"""Source-backed task time-accounting skills.

These skills use only the bounded per-task worklog facade proven in A215C.
They do not infer capacity/utilization and do not perform tenant-wide scans.
"""
from __future__ import annotations

from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


def _task_key(args: dict[str, str]) -> str:
    task_key = str(args.get("task_key") or "").strip().upper()
    if not task_key:
        raise V4NeedsClarification("Укажите задачу.")
    return task_key


def _worklog_evidence(task_key: str, entries: list[dict[str, Any]]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for item in entries:
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        work_type = item.get("type") if isinstance(item.get("type"), dict) else {}
        worklog_id = str(item.get("id") or "").strip() or None
        label = str(work_type.get("name") or "worklog")
        value = {
            "date": item.get("date"),
            "user": user.get("external_id"),
            "duration_hours": item.get("duration_hours"),
        }
        evidence.append(
            Evidence(
                type="task_worklog",
                source="as21",
                entity_id=worklog_id or task_key,
                label=label,
                value=value,
            )
        )
    return evidence


def build_task_time_spent(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        task_key = _task_key(args)
        reader = getattr(runtime.adapter, "get_task_worklogs", None)
        if reader is None:
            raise V4CapabilityUnavailable("task.time_spent requires a bounded worklog source")
        payload = await reader(task_key)
        if not payload.get("complete"):
            raise V4CapabilityUnavailable("task.time_spent requires a complete bounded worklog collection")
        total = payload.get("total_hours")
        entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
        if total is None:
            raise V4CapabilityUnavailable("REAL AS21 did not expose cumulative time spent for the task")
        entry_total = payload.get("entry_total_hours")
        if isinstance(entry_total, (int, float)) and abs(float(entry_total) - float(total)) > 1e-6:
            raise V4CapabilityUnavailable("worklog aggregate does not match the complete entry collection")

        data = {
            "task_key": task_key,
            "time_spent_hours": float(total),
            "worklog_count": len(entries),
            "source": "REAL_AS21",
            "complete": True,
            "convention": payload.get("convention") or {},
        }
        return CapabilityResult(
            answer=f"По задаче {task_key} списано {float(total):g} ч.",
            data=data,
            evidence=_worklog_evidence(task_key, entries),
        )
    return execute


def build_task_worklogs(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        task_key = _task_key(args)
        reader = getattr(runtime.adapter, "get_task_worklogs", None)
        if reader is None:
            raise V4CapabilityUnavailable("task.worklogs requires a bounded worklog source")
        payload = await reader(task_key)
        if not payload.get("complete"):
            raise V4CapabilityUnavailable("task.worklogs requires a complete bounded worklog collection")
        entries = payload.get("entries") if isinstance(payload.get("entries"), list) else []
        rows = []
        for item in entries:
            user = item.get("user") if isinstance(item.get("user"), dict) else {}
            work_type = item.get("type") if isinstance(item.get("type"), dict) else {}
            rows.append({
                "id": item.get("id"),
                "date": item.get("date"),
                "user_external_id": user.get("external_id"),
                "user_name": " ".join(
                    str(part).strip()
                    for part in (user.get("last_name"), user.get("first_name"), user.get("middle_name"))
                    if part and str(part).strip()
                ),
                "work_type_code": work_type.get("code"),
                "work_type_name": work_type.get("name"),
                "duration_hours": item.get("duration_hours"),
                "comment": item.get("comment"),
            })
        total = payload.get("total_hours")
        return CapabilityResult(
            answer=f"По задаче {task_key} найдено списаний: {len(rows)}, всего {float(total or 0):g} ч.",
            data={
                "task_key": task_key,
                "count": len(rows),
                "time_spent_hours": float(total) if isinstance(total, (int, float)) else None,
                "worklogs": rows,
                "source": "REAL_AS21",
                "complete": True,
            },
            evidence=_worklog_evidence(task_key, entries),
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("task.time_spent", "Read cumulative actual time spent for one task from REAL AS21 worklogs.", {"task_key": "required canonical task key"}),
    CapabilitySpecV4("task.worklogs", "Read dated, user-attributed worklog entries for one task from REAL AS21.", {"task_key": "required canonical task key"}),
)

SKILLS = (
    SkillSpecV4(
        "task.time_spent",
        "Report actual time written off/spent on one task.",
        ("Call task.time_spent with the user-supplied task key.",),
        ("task.time_spent",),
        completion=(CompletionRequirement("task.time_spent", data_keys=("task_key", "time_spent_hours")),),
    ),
    SkillSpecV4(
        "task.worklogs",
        "Show the individual time-accounting entries for one task.",
        ("Call task.worklogs with the user-supplied task key.",),
        ("task.worklogs",),
        completion=(CompletionRequirement("task.worklogs", data_keys=("task_key", "worklogs")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("task.time_spent", handler_builder=build_task_time_spent),
    CapabilityBindingV4("task.worklogs", handler_builder=build_task_worklogs),
)

UI = {
    "task.time_spent": UIContractV4("analysis", preferred_widget="task_time_spent", required_fields=("task_key", "time_spent_hours")),
    "task.worklogs": UIContractV4("task_collection", preferred_widget="task_worklogs", required_fields=("task_key", "worklogs")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.time_accounting.task",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
