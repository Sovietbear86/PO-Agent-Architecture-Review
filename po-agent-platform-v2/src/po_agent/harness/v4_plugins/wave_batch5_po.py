"""Batch 5: bounded PO workflow skills.

This plugin migrates the five canonical PO skills still missing from V4:
- po.attention_queue
- po.daily_brief
- po.status_report
- po.reminder_draft
- po.local_task_draft

Architecture rules:
- no tenant-wide task scans;
- portfolio-wide views are bounded to approved product spaces and each space's current sprint;
- drafts never write externally;
- reminder drafting requires an explicit source task key;
- no employee performance scoring.
"""
from __future__ import annotations

from typing import Any

from ..agent_core_v4 import CapabilitySpecV4, SkillSpecV4, V4CapabilityUnavailable, V4NeedsClarification
from ..agent_core_v4_completion import CompletionRequirement
from ..contracts import CapabilityResult, Evidence
from ..production_entity_grounding_v2 import APPROVED_PRODUCT_SPACES
from ..v4_plugin_registry import CapabilityBindingV4, UIContractV4, V4SkillPlugin


def _task_row(task: Any) -> dict[str, Any]:
    priority = getattr(task, "priority", None)
    priority_value = getattr(priority, "value", None) if priority is not None else None
    status = getattr(task, "status_raw", None) or getattr(getattr(task, "status", None), "value", None)
    return {
        "key": task.key,
        "title": task.title,
        "status": status,
        "assignee": getattr(task, "assignee_login", None)
        or getattr(task, "assignee_id", None)
        or getattr(task, "assignee", None),
        "priority": priority_value,
        "age_days": getattr(task, "age_days", 0),
        "sprint_id": getattr(task, "sprint_id", None),
        "release_id": getattr(task, "release_id", None),
        "blocked": bool(getattr(task, "is_blocked", False)),
        "completed": bool(getattr(task, "is_completed", False)),
        "space": getattr(task, "project_space", None),
    }


def _evidence(tasks: list[Any], kind: str) -> list[Evidence]:
    result = []
    for task in tasks:
        status = getattr(task, "status_raw", None) or getattr(getattr(task, "status", None), "value", None)
        result.append(
            Evidence(
                type=kind,
                source="as21",
                entity_id=task.key,
                label=task.title,
                value=status,
            )
        )
    return result


def _score(task: Any) -> tuple[int, list[str]]:
    if getattr(task, "is_completed", False):
        return 0, []
    score = 0
    reasons: list[str] = []
    if getattr(task, "is_blocked", False):
        score += 50
        reasons.append("blocked")
    priority = getattr(getattr(task, "priority", None), "value", None)
    if priority in {"Critical", "Urgent"}:
        score += 35
        reasons.append("high_priority")
    age_days = int(getattr(task, "age_days", 0) or 0)
    if age_days >= 14:
        score += 20
        reasons.append("aging_14d")
    elif age_days >= 7:
        score += 10
        reasons.append("aging_7d")
    assignee = (
        getattr(task, "assignee_login", None)
        or getattr(task, "assignee_id", None)
        or getattr(task, "assignee", None)
    )
    if not assignee:
        score += 10
        reasons.append("unassigned")
    return score, reasons


async def _current_sprint_portfolio(runtime: Any) -> tuple[list[dict[str, Any]], list[Any]]:
    getter = getattr(runtime.adapter, "get_current_sprint_id", None)
    task_getter = getattr(runtime.adapter, "get_sprint_tasks", None)
    if getter is None or task_getter is None:
        raise V4CapabilityUnavailable("PO portfolio views require bounded current-sprint source support")

    spaces: list[dict[str, Any]] = []
    all_tasks: list[Any] = []
    for space in sorted(APPROVED_PRODUCT_SPACES):
        sprint_id = await getter(space)
        if not sprint_id:
            spaces.append({
                "space": space,
                "state": "NO_CURRENT_SPRINT",
                "sprint_id": None,
                "task_count": None,
            })
            continue

        tasks = list(await task_getter(sprint_id, space))
        if not tasks:
            spaces.append({
                "space": space,
                "state": "CURRENT_SPRINT_WITHOUT_MEMBERSHIP",
                "sprint_id": sprint_id,
                "task_count": None,
            })
            continue

        spaces.append({
            "space": space,
            "state": "SOURCE_BACKED",
            "sprint_id": sprint_id,
            "task_count": len(tasks),
        })
        all_tasks.extend(tasks)
    return spaces, all_tasks


def build_po_attention_queue(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        spaces, tasks = await _current_sprint_portfolio(runtime)
        ranked = []
        selected = []
        for task in tasks:
            score, reasons = _score(task)
            if score <= 0:
                continue
            selected.append(task)
            ranked.append({
                "task": _task_row(task),
                "attention_score": score,
                "reasons": reasons,
            })
        ranked.sort(key=lambda row: (-int(row["attention_score"]), str(row["task"]["key"])))
        return CapabilityResult(
            answer=f"В очереди внимания PO: {len(ranked)} элементов по текущим спринтам продуктов.",
            data={
                "count": len(ranked),
                "queue": ranked,
                "spaces": spaces,
                "scoring_version": "po_attention_v1",
                "scope": "approved_product_spaces_current_sprints",
                "source": "REAL_AS21",
            },
            evidence=_evidence(selected, "po_attention_task"),
            warnings=["attention_score_is_task_operational_priority_not_employee_score"],
        )
    return execute


def build_po_daily_brief(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        spaces, tasks = await _current_sprint_portfolio(runtime)
        active = [task for task in tasks if not getattr(task, "is_completed", False)]
        blocked = [task for task in active if getattr(task, "is_blocked", False)]
        unassigned = [
            task for task in active
            if not (
                getattr(task, "assignee_login", None)
                or getattr(task, "assignee_id", None)
                or getattr(task, "assignee", None)
            )
        ]
        completed = [task for task in tasks if getattr(task, "is_completed", False)]
        ranked = []
        for task in active:
            score, reasons = _score(task)
            if score:
                ranked.append((score, task, reasons))
        ranked.sort(key=lambda item: (-item[0], item[1].key))
        top = [
            {
                "task": _task_row(task),
                "attention_score": score,
                "reasons": reasons,
            }
            for score, task, reasons in ranked[:5]
        ]
        return CapabilityResult(
            answer=(
                f"Краткая сводка PO по текущим спринтам: {len(active)} активных задач, "
                f"{len(blocked)} заблокировано, {len(unassigned)} без исполнителя, "
                f"{len(completed)} завершено. Точек внимания: {len(ranked)}."
            ),
            data={
                "active": len(active),
                "blocked": len(blocked),
                "unassigned": len(unassigned),
                "completed": len(completed),
                "attention_count": len(ranked),
                "top_attention": top,
                "spaces": spaces,
                "scope": "approved_product_spaces_current_sprints",
                "source": "REAL_AS21",
                "synthesis_mode": "deterministic",
            },
            evidence=_evidence(tasks, "po_daily_brief_task"),
        )
    return execute


def build_po_status_report(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        spaces, tasks = await _current_sprint_portfolio(runtime)
        by_product: dict[str, dict[str, Any]] = {
            row["space"]: {
                "state": row["state"],
                "sprint_id": row["sprint_id"],
                "total": 0 if row["state"] == "SOURCE_BACKED" else None,
                "completed": 0 if row["state"] == "SOURCE_BACKED" else None,
                "blocked": 0 if row["state"] == "SOURCE_BACKED" else None,
            }
            for row in spaces
        }
        for task in tasks:
            space = str(getattr(task, "project_space", None) or task.key.split("-", 1)[0]).upper()
            row = by_product.setdefault(
                space,
                {"state": "SOURCE_BACKED", "sprint_id": getattr(task, "sprint_id", None), "total": 0, "completed": 0, "blocked": 0},
            )
            row["total"] += 1
            row["completed"] += int(bool(getattr(task, "is_completed", False)))
            row["blocked"] += int(bool(getattr(task, "is_blocked", False)))

        total = len(tasks)
        completed = sum(1 for task in tasks if getattr(task, "is_completed", False))
        active = total - completed
        blocked = sum(1 for task in tasks if getattr(task, "is_blocked", False))
        completion = round(completed / total * 100.0, 1) if total else None

        return CapabilityResult(
            answer=(
                f"Статус текущих спринтов: выполнено {completed}/{total}"
                + (f" ({completion:g}%)" if completion is not None else "")
                + f", активно {active}, заблокировано {blocked}."
            ),
            data={
                "total": total,
                "completed": completed,
                "active": active,
                "blocked": blocked,
                "completion_percent": completion,
                "by_product": by_product,
                "spaces": spaces,
                "scope": "approved_product_spaces_current_sprints",
                "source": "REAL_AS21",
                "synthesis_mode": "deterministic",
            },
            evidence=_evidence(tasks, "po_status_report_task"),
        )
    return execute


def _task_key(args: dict[str, str]) -> str:
    return str(args.get("task_key") or "").strip().upper()


def build_po_reminder_draft(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        key = _task_key(args)
        if not key:
            raise V4NeedsClarification(
                "Укажите задачу, по которой подготовить напоминание. Автовыбор задачи без явного контекста не выполняется."
            )
        task = await runtime.adapter.get_task(key)
        if task is None:
            return CapabilityResult(
                answer=f"Задача {key} не найдена; черновик напоминания не создан.",
                data={
                    "task_key": key,
                    "draft_created": False,
                    "write_performed": False,
                },
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=key, label="lookup", value="not_found")],
            )
        recipient = (
            getattr(task, "assignee_login", None)
            or getattr(task, "assignee_id", None)
            or getattr(task, "assignee", None)
            or "исполнитель задачи"
        )
        status = getattr(task, "status_raw", None) or getattr(getattr(task, "status", None), "value", None)
        text = (
            f"Коллега, напомню про {task.key} — {task.title}. "
            f"Текущий статус: {status or '—'}. Просьба обновить статус/следующий шаг "
            "и подсветить блокеры, если они есть."
        )
        return CapabilityResult(
            answer=f"Подготовлен черновик напоминания по {task.key}. Отправка не выполнялась.",
            data={
                "draft_created": True,
                "draft_type": "reminder",
                "task": _task_row(task),
                "recipient": recipient,
                "text": text,
                "write_performed": False,
                "requires_approval_for_send": True,
                "source": "REAL_AS21",
            },
            evidence=_evidence([task], "po_reminder_draft_task"),
            warnings=["draft_only_no_external_write"],
        )
    return execute


def build_po_local_task_draft(runtime: Any):
    async def execute(args: dict[str, str]) -> CapabilityResult:
        subject = str(args.get("subject") or "").strip()
        source_key = _task_key(args)
        source_task = await runtime.adapter.get_task(source_key) if source_key else None
        if source_key and source_task is None:
            return CapabilityResult(
                answer=f"Исходная задача {source_key} не найдена; локальный draft не создан.",
                data={
                    "draft_created": False,
                    "write_performed": False,
                    "task_key": source_key,
                },
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=source_key, label="lookup", value="not_found")],
            )
        if not subject and source_task is None:
            raise V4NeedsClarification("Укажите тему локальной задачи или исходную задачу AS21.")

        title = subject or f"Follow-up: {source_task.key} — {source_task.title}"
        description = (
            f"Локальный follow-up по {source_task.key}. Исходная задача: {source_task.title}."
            if source_task is not None
            else "Локальная задача PO. Уточните ожидаемый результат и критерии готовности перед публикацией."
        )
        draft = {
            "title": title,
            "description": description,
            "source_task_key": source_task.key if source_task is not None else None,
            "status": "draft",
            "write_performed": False,
            "requires_approval_for_external_write": True,
        }
        return CapabilityResult(
            answer="Подготовлен черновик локальной задачи. Запись в AS21 не выполнялась.",
            data={
                "draft_created": True,
                "draft": draft,
                "write_performed": False,
                "source": "REAL_AS21" if source_task is not None else "USER_INPUT_ONLY",
            },
            evidence=_evidence([source_task], "po_local_task_draft_source") if source_task is not None else [],
            warnings=["draft_only_no_external_write"],
        )
    return execute


CAPABILITIES = (
    CapabilitySpecV4("po.attention_queue", "Rank current-sprint tasks across approved product spaces that need PO attention.", {}),
    CapabilitySpecV4("po.daily_brief", "Generate a deterministic grounded daily PO brief from bounded current-sprint data.", {}),
    CapabilitySpecV4("po.status_report", "Generate a deterministic current-sprint portfolio status report.", {}),
    CapabilitySpecV4("po.reminder_draft", "Draft a reminder for one explicit AS21 task without sending it.", {"task_key": "required task key"}),
    CapabilitySpecV4("po.local_task_draft", "Prepare a local task draft without writing externally.", {"subject": "optional user-supplied title", "task_key": "optional source task key"}),
)

SKILLS = (
    SkillSpecV4(
        "po.attention_queue",
        "Show cross-product current-sprint tasks that need PO attention using deterministic task risk signals.",
        (
            "Call po.attention_queue.",
            "Use only bounded current-sprint membership for approved product spaces.",
            "Attention score prioritizes tasks, never employees.",
        ),
        ("po.attention_queue",),
        completion=(CompletionRequirement("po.attention_queue", data_keys=("count", "scoring_version")),),
    ),
    SkillSpecV4(
        "po.daily_brief",
        "Generate a grounded daily PO brief from current sprints of approved product spaces.",
        (
            "Call po.daily_brief.",
            "Do not tenant-scan historical/arbitrary tasks; this is a current-sprint operational brief.",
        ),
        ("po.daily_brief",),
        completion=(CompletionRequirement("po.daily_brief", data_keys=("active", "blocked", "attention_count")),),
    ),
    SkillSpecV4(
        "po.status_report",
        "Generate a bounded current-sprint status report across approved product spaces.",
        (
            "Call po.status_report.",
            "Preserve NO_CURRENT_SPRINT/CURRENT_SPRINT_WITHOUT_MEMBERSHIP states instead of inventing zeros for unavailable scope.",
        ),
        ("po.status_report",),
        completion=(CompletionRequirement("po.status_report", data_keys=("total", "by_product")),),
    ),
    SkillSpecV4(
        "po.reminder_draft",
        "Prepare, but never send, a contextual reminder for an explicit task.",
        (
            "Require a concrete task key and call po.reminder_draft.",
            "Never auto-select a task from a tenant-wide search.",
            "Never send or mutate AS21.",
        ),
        ("po.reminder_draft",),
        completion=(CompletionRequirement("po.reminder_draft", data_keys=("draft_created", "write_performed")),),
    ),
    SkillSpecV4(
        "po.local_task_draft",
        "Prepare a local task draft from user input and optionally one source task; never publish it automatically.",
        (
            "Call po.local_task_draft with a user-supplied subject and/or task key.",
            "If a task key is provided, source-ground it with a point read.",
            "Never perform an external write.",
        ),
        ("po.local_task_draft",),
        completion=(CompletionRequirement("po.local_task_draft", data_keys=("draft_created", "write_performed")),),
    ),
)

BINDINGS = (
    CapabilityBindingV4("po.attention_queue", handler_builder=build_po_attention_queue),
    CapabilityBindingV4("po.daily_brief", handler_builder=build_po_daily_brief),
    CapabilityBindingV4("po.status_report", handler_builder=build_po_status_report),
    CapabilityBindingV4("po.reminder_draft", handler_builder=build_po_reminder_draft),
    CapabilityBindingV4("po.local_task_draft", handler_builder=build_po_local_task_draft),
)

UI = {
    "po.attention_queue": UIContractV4("task_collection", preferred_widget="po_attention_queue", required_fields=("count", "queue")),
    "po.daily_brief": UIContractV4("analysis", preferred_widget="po_daily_brief", required_fields=("active", "blocked", "top_attention")),
    "po.status_report": UIContractV4("analysis", preferred_widget="po_status_report", required_fields=("by_product",)),
    "po.reminder_draft": UIContractV4("draft", preferred_widget="po_reminder_draft", required_fields=("draft_created", "write_performed")),
    "po.local_task_draft": UIContractV4("draft", preferred_widget="po_local_task_draft", required_fields=("draft_created", "write_performed")),
}

PLUGIN = V4SkillPlugin(
    plugin_id="builtin.batch5.po_workflow",
    skills=SKILLS,
    capabilities=CAPABILITIES,
    bindings=BINDINGS,
    ui=UI,
)
