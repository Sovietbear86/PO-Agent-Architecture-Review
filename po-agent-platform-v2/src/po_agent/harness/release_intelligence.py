"""Deterministic Release Intelligence capabilities."""
from __future__ import annotations

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import Task, TaskPriority

from .contracts import CapabilityResult, Evidence


class ReleaseIntelligenceCapabilities:
    def __init__(self, adapter: AS21Adapter) -> None:
        self.a = adapter

    @staticmethod
    def _task(task: Task) -> dict[str, object]:
        return {
            "key": task.key,
            "title": task.title,
            "status": task.status.value,
            "status_category": task.status_category.value,
            "assignee": task.assignee,
            "priority": task.priority.value if task.priority else None,
            "estimate_hours": task.estimate_hours,
            "depends_on": task.depends_on,
        }

    @staticmethod
    def _evidence(tasks: list[Task], kind: str) -> list[Evidence]:
        return [Evidence(type=kind, source="as21", entity_id=t.key, label=t.title, value=t.status.value) for t in tasks]

    async def scope(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        return CapabilityResult(
            answer=f"В релизе {release_id} задач: {len(tasks)}.",
            data={"release_id": release_id, "count": len(tasks), "tasks": [self._task(t) for t in tasks]},
            evidence=self._evidence(tasks, "release_scope_task"),
        )

    async def progress(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        total = len(tasks)
        completed = sum(t.is_completed for t in tasks)
        blocked = sum(t.is_blocked for t in tasks)
        active = sum(t.status_category.value == "active_work" for t in tasks)
        estimate_total = sum(t.estimate_hours or 0.0 for t in tasks)
        estimate_completed = sum((t.estimate_hours or 0.0) for t in tasks if t.is_completed)
        task_percent = round(completed / total * 100, 1) if total else 0.0
        effort_percent = round(estimate_completed / estimate_total * 100, 1) if estimate_total else None
        return CapabilityResult(
            answer=f"{release_id}: выполнено {completed}/{total} ({task_percent}%), заблокировано {blocked}.",
            data={
                "release_id": release_id,
                "total": total,
                "completed": completed,
                "active": active,
                "blocked": blocked,
                "task_completion_percent": task_percent,
                "estimated_hours_total": round(estimate_total, 1),
                "estimated_hours_completed": round(estimate_completed, 1),
                "effort_completion_percent": effort_percent,
            },
            evidence=self._evidence(tasks, "release_progress_task"),
        )

    async def blockers(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        blocked = [t for t in tasks if t.is_blocked]
        return CapabilityResult(
            answer=f"В релизе {release_id} заблокировано задач: {len(blocked)}.",
            data={"release_id": release_id, "count": len(blocked), "tasks": [self._task(t) for t in blocked]},
            evidence=self._evidence(blocked, "release_blocker_task"),
        )

    async def dependencies(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
        release_keys = {t.key for t in tasks}
        edges = []
        external = []
        for task in tasks:
            for dependency in task.depends_on:
                edge = {"task": task.key, "depends_on": dependency}
                (edges if dependency in release_keys else external).append(edge)
        return CapabilityResult(
            answer=f"{release_id}: внутренних зависимостей {len(edges)}, внешних {len(external)}.",
            data={"release_id": release_id, "internal": edges, "external": external},
            evidence=self._evidence(tasks, "release_dependency_source"),
        )

    async def risk_queue(self, args: dict[str, str]) -> CapabilityResult:
        release_id = args["release_id"].upper()
        tasks = await self.a.get_release_tasks(release_id)
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
            if not task.assignee and not task.is_completed:
                score += 15
                reasons.append("unassigned")
            if task.age_days >= 14 and not task.is_completed:
                score += 10
                reasons.append("aging")
            if score:
                queue.append({"task": self._task(task), "risk_score": min(score, 100), "reasons": reasons})
        queue.sort(key=lambda item: (-item["risk_score"], item["task"]["key"]))
        return CapabilityResult(
            answer=f"В очереди рисков релиза {release_id}: {len(queue)} задач.",
            data={"release_id": release_id, "risk_queue": queue, "scoring_version": "release_risk_v1"},
            evidence=self._evidence([t for t in tasks if any(q["task"]["key"] == t.key for q in queue)], "release_risk_task"),
        )
