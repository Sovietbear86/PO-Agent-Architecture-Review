"""Grounded Product Owner assistant capabilities.

These capabilities aggregate canonical task facts into PO-facing views and
produce drafts only. Draft capabilities never perform external writes; later
action execution must cross a separate approval/write boundary.
"""
from __future__ import annotations

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task

from .contracts import CapabilityResult, Evidence


class POAssistantCapabilities:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.a = adapter

    @staticmethod
    def _task(t: Task) -> dict[str, object]:
        return {
            "key": t.key,
            "title": t.title,
            "status": t.status.value,
            "status_category": t.status_category.value,
            "assignee": t.assignee,
            "priority": t.priority.value if t.priority else None,
            "age_days": t.age_days,
            "sprint_id": t.sprint_id,
            "release_id": t.release_id,
            "blocked": t.is_blocked,
        }

    @staticmethod
    def _evidence(tasks: list[Task], kind: str) -> list[Evidence]:
        return [
            Evidence(type=kind, source="as21", entity_id=t.key, label=t.title, value=t.status.value)
            for t in tasks
        ]

    @staticmethod
    def _score(t: Task) -> tuple[int, list[str]]:
        score = 0
        reasons: list[str] = []
        if t.is_blocked:
            score += 50
            reasons.append("blocked")
        if t.priority and t.priority.value in ("Critical", "Urgent") and not t.is_completed:
            score += 35
            reasons.append("high_priority")
        if not t.is_completed and t.age_days >= 14:
            score += 20
            reasons.append("aging_14d")
        elif not t.is_completed and t.age_days >= 7:
            score += 10
            reasons.append("aging_7d")
        if not t.assignee and not t.is_completed:
            score += 10
            reasons.append("unassigned")
        return score, reasons

    async def attention_queue(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.a.search_tasks("")
        ranked = []
        selected: list[Task] = []
        for task in tasks:
            if task.is_completed:
                continue
            score, reasons = self._score(task)
            if score <= 0:
                continue
            selected.append(task)
            ranked.append({"task": self._task(task), "attention_score": score, "reasons": reasons})
        ranked.sort(key=lambda row: (-int(row["attention_score"]), str(row["task"]["key"])))
        return CapabilityResult(
            answer=f"В очереди внимания PO: {len(ranked)} элементов.",
            data={"count": len(ranked), "queue": ranked, "scoring_version": "po_attention_v1"},
            evidence=self._evidence(selected, "po_attention_task"),
        )

    async def daily_brief(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.a.search_tasks("")
        active = [t for t in tasks if not t.is_completed]
        blocked = [t for t in active if t.is_blocked]
        unassigned = [t for t in active if not t.assignee]
        completed = [t for t in tasks if t.is_completed]
        ranked = []
        for task in active:
            score, reasons = self._score(task)
            if score:
                ranked.append((score, task, reasons))
        ranked.sort(key=lambda x: (-x[0], x[1].key))
        top = [{"task": self._task(t), "attention_score": score, "reasons": reasons} for score, t, reasons in ranked[:5]]
        answer = (
            f"Краткая сводка PO: {len(active)} активных задач, {len(blocked)} заблокировано, "
            f"{len(unassigned)} без исполнителя, {len(completed)} завершено. "
            f"Точек внимания: {len(ranked)}."
        )
        return CapabilityResult(
            answer=answer,
            data={
                "active": len(active),
                "blocked": len(blocked),
                "unassigned": len(unassigned),
                "completed": len(completed),
                "top_attention": top,
                "synthesis_mode": "deterministic_fallback",
            },
            evidence=self._evidence(tasks, "po_daily_brief_task"),
            warnings=["llm_unavailable_deterministic_daily_brief"],
        )

    async def status_report(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self.a.search_tasks("")
        total = len(tasks)
        completed = sum(t.is_completed for t in tasks)
        active = [t for t in tasks if not t.is_completed]
        blocked = [t for t in active if t.is_blocked]
        by_product: dict[str, dict[str, int]] = {}
        for t in tasks:
            product = t.key.split("-", 1)[0]
            row = by_product.setdefault(product, {"total": 0, "completed": 0, "blocked": 0})
            row["total"] += 1
            row["completed"] += int(t.is_completed)
            row["blocked"] += int(t.is_blocked)
        completion = round(completed / total * 100, 1) if total else 0.0
        answer = (
            f"Статус портфеля: выполнено {completed}/{total} ({completion}%), "
            f"активно {len(active)}, заблокировано {len(blocked)}."
        )
        return CapabilityResult(
            answer=answer,
            data={
                "total": total,
                "completed": completed,
                "active": len(active),
                "blocked": len(blocked),
                "completion_percent": completion,
                "by_product": by_product,
                "synthesis_mode": "deterministic_fallback",
            },
            evidence=self._evidence(tasks, "po_status_report_task"),
            warnings=["llm_unavailable_deterministic_status_report"],
        )

    async def reminder_draft(self, args: dict[str, str]) -> CapabilityResult:
        key = args.get("task_key", "").upper().strip()
        task = await self.a.get_task(key) if key else None
        if task is None and key:
            return CapabilityResult(
                answer=f"Задача {key} не найдена; черновик напоминания не создан.",
                data={"task_key": key, "draft_created": False, "write_performed": False},
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=key, label="lookup", value="not_found")],
            )
        if task is None:
            tasks = [t for t in await self.a.search_tasks("") if not t.is_completed]
            ranked = sorted(((self._score(t)[0], t) for t in tasks), key=lambda item: (-item[0], item[1].key))
            task = ranked[0][1] if ranked else None
        if task is None:
            return CapabilityResult(
                answer="Нет активной задачи, для которой можно подготовить напоминание.",
                data={"draft_created": False, "write_performed": False},
                evidence=[],
            )
        recipient = task.assignee or "исполнитель задачи"
        text = (
            f"Коллега, напомню про {task.key} — {task.title}. "
            f"Текущий статус: {task.status.value}. Просьба обновить статус/следующий шаг и подсветить блокеры, если они есть."
        )
        return CapabilityResult(
            answer=f"Подготовлен черновик напоминания по {task.key}. Отправка не выполнялась.",
            data={
                "draft_created": True,
                "draft_type": "reminder",
                "task": self._task(task),
                "recipient": recipient,
                "text": text,
                "write_performed": False,
                "requires_approval_for_send": True,
            },
            evidence=self._evidence([task], "po_reminder_draft_task"),
            warnings=["draft_only_no_external_write"],
        )

    async def local_task_draft(self, args: dict[str, str]) -> CapabilityResult:
        subject = args.get("subject", "").strip()
        source_key = args.get("task_key", "").upper().strip()
        source_task = await self.a.get_task(source_key) if source_key else None
        if source_key and source_task is None:
            return CapabilityResult(
                answer=f"Исходная задача {source_key} не найдена; локальный draft не создан.",
                data={"draft_created": False, "write_performed": False, "task_key": source_key},
                evidence=[Evidence(type="task_lookup", source="as21", entity_id=source_key, label="lookup", value="not_found")],
            )
        title = subject or (f"Follow-up: {source_task.key} — {source_task.title}" if source_task else "Новая локальная задача")
        description = (
            f"Локальный follow-up по {source_task.key}. Исходная задача: {source_task.title}."
            if source_task else "Локальная задача PO. Уточните ожидаемый результат и критерии готовности перед публикацией."
        )
        draft = {
            "title": title,
            "description": description,
            "source_task_key": source_task.key if source_task else None,
            "status": "draft",
            "write_performed": False,
            "requires_approval_for_external_write": True,
        }
        return CapabilityResult(
            answer="Подготовлен черновик локальной задачи. Запись в AS21 не выполнялась.",
            data={"draft_created": True, "draft": draft},
            evidence=self._evidence([source_task], "po_local_task_draft_source") if source_task else [],
            warnings=["draft_only_no_external_write"],
        )
