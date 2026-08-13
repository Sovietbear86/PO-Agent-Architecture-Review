"""Grounded Product Owner assistant capabilities.

These capabilities aggregate already canonical task facts into PO-facing views.
The deterministic fallback is intentionally complete; an LLM may later improve
wording, but cannot change rankings, counts, scores or evidence.
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
