"""Deterministic Sprint Intelligence capabilities for the recovery Harness.

All numeric metrics are calculated from canonical AS21 task/history data. LLMs
may explain these values later, but never calculate or mutate them.
"""
from __future__ import annotations

import re
from statistics import mean, median

from po_agent.adapters.as21 import AS21Adapter
from po_agent.adapters.task_api import AS21CapabilityUnavailable
from po_agent.domain.models import Task, TaskStatus

from .contracts import CapabilityResult, Evidence


class SprintIntelligenceCapabilities:
    STALLED_STATUS_HOURS = 7 * 24

    def __init__(self, adapter: AS21Adapter) -> None:
        self.adapter = adapter

    async def current(self, args: dict[str, str]) -> CapabilityResult:
        product = args["product"].upper()
        tasks = await self.adapter.search_tasks(f"project = {product}")
        sprint_ids = sorted(
            {task.sprint_id for task in tasks if task.sprint_id},
            key=self._sprint_sort_key,
            reverse=True,
        )
        current = sprint_ids[0] if sprint_ids else None
        return CapabilityResult(
            answer=(f"Текущий доступный спринт {product}: {current}." if current else f"Для {product} не найден спринт в доступных данных."),
            data={"product": product, "sprint_id": current, "candidate_sprints": sprint_ids},
            evidence=[Evidence(type="sprint_resolution", source="as21", entity_id=product, label="sprint_id", value=current)],
            warnings=[] if current else ["current_sprint_not_found"],
        )

    async def scope(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        return CapabilityResult(
            answer=f"В scope {sprint_id}: {len(tasks)} задач.",
            data={"sprint_id": sprint_id, "count": len(tasks), "tasks": [self._task_data(task) for task in tasks]},
            evidence=self._task_evidence(sprint_id, tasks, "sprint_scope_task"),
        )

    async def velocity(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        completed = [task for task in tasks if task.is_completed]
        unit, committed, delivered = self._effort(tasks, completed)
        return CapabilityResult(
            answer=f"Velocity {sprint_id}: {delivered:g} {unit} завершено из {committed:g} {unit} в доступном scope.",
            data={"sprint_id": sprint_id, "unit": unit, "committed": committed, "velocity": delivered, "completed_tasks": len(completed), "total_tasks": len(tasks)},
            evidence=self._task_evidence(sprint_id, tasks, "velocity_input"),
        )

    async def throughput(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        completed = [task for task in tasks if task.is_completed]
        return CapabilityResult(
            answer=f"Throughput {sprint_id}: {len(completed)} завершённых задач из {len(tasks)}.",
            data={"sprint_id": sprint_id, "throughput_tasks": len(completed), "total_tasks": len(tasks), "unit": "tasks"},
            evidence=self._task_evidence(sprint_id, completed, "throughput_task"),
        )

    async def wip(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        wip_tasks = [task for task in tasks if not task.is_completed and task.status not in (TaskStatus.OPEN, TaskStatus.CANCELLED)]
        by_status: dict[str, int] = {}
        for task in wip_tasks:
            by_status[task.status.value] = by_status.get(task.status.value, 0) + 1
        return CapabilityResult(
            answer=f"WIP {sprint_id}: {len(wip_tasks)} задач.",
            data={"sprint_id": sprint_id, "wip": len(wip_tasks), "unit": "tasks", "by_status": by_status, "tasks": [self._task_data(task) for task in wip_tasks]},
            evidence=self._task_evidence(sprint_id, wip_tasks, "wip_task"),
        )

    async def cycle_time(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        tasks = await self._hydrate_completed_history(tasks)
        values = [value for task in tasks if (value := self._cycle_hours(task)) is not None]
        return self._duration_result(sprint_id, "cycle_time", values, tasks)

    async def lead_time(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        tasks = await self._hydrate_completed_history(tasks)
        values = [value for task in tasks if (value := self._lead_hours(task)) is not None]
        return self._duration_result(sprint_id, "lead_time", values, tasks)

    async def predictability(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        completed = [task for task in tasks if task.is_completed]
        unit, committed, delivered = self._effort(tasks, completed)
        percent = round(delivered / committed * 100, 1) if committed else 0.0
        return CapabilityResult(
            answer=f"Predictability {sprint_id}: {percent}% ({delivered:g}/{committed:g} {unit}).",
            data={"sprint_id": sprint_id, "predictability_percent": percent, "delivered": delivered, "committed": committed, "unit": unit},
            evidence=self._task_evidence(sprint_id, tasks, "predictability_input"),
            warnings=["current_scope_used_as_commitment_baseline"],
        )

    async def risk_queue(self, args: dict[str, str]) -> CapabilityResult:
        sprint_id, tasks = await self._tasks(args)
        tasks = await self._hydrate_active_history(tasks)
        risks: list[dict[str, object]] = []
        for task in tasks:
            if task.is_completed:
                continue
            reasons: list[str] = []
            score = 0
            if task.is_blocked:
                reasons.append("blocked")
                score += 100
            if task.priority and task.priority.value in ("Critical", "Urgent"):
                reasons.append(task.priority.value.lower())
                score += 50
            if task.age_days >= 7:
                reasons.append(f"aging_{task.age_days}d")
                score += min(task.age_days, 30)
            current_status_hours = self._current_status_hours(task)
            if current_status_hours is not None and current_status_hours >= self.STALLED_STATUS_HOURS:
                reasons.append(f"stalled_status_{round(current_status_hours, 1)}h")
                score += min(int(current_status_hours // 24), 30)
            if reasons:
                risks.append({**self._task_data(task), "risk_score": score, "reasons": reasons, "current_status_hours": round(current_status_hours, 2) if current_status_hours is not None else None})
        risks.sort(key=lambda item: (-int(item["risk_score"]), str(item["key"])))
        return CapabilityResult(
            answer=f"В risk queue {sprint_id}: {len(risks)} задач.",
            data={
                "sprint_id": sprint_id,
                "count": len(risks),
                "risks": risks,
                "scoring": {
                    "blocked": 100,
                    "critical_or_urgent": 50,
                    "aging_days": "min(age_days,30)",
                    "stalled_status": f">={self.STALLED_STATUS_HOURS}h; +min(full_status_days,30)",
                },
            },
            evidence=[Evidence(type="sprint_risk", source="deterministic", entity_id=str(item["key"]), label="risk_score", value=item["risk_score"]) for item in risks],
        )

    async def _tasks(self, args: dict[str, str]) -> tuple[str, list[Task]]:
        sprint_id = (args.get("sprint_id") or "").strip().upper()
        if not sprint_id:
            raise AS21CapabilityUnavailable("sprint_id is required for sprint intelligence")
        return sprint_id, await self.adapter.get_sprint_tasks(sprint_id)

    async def _hydrate_completed_history(self, tasks: list[Task]) -> list[Task]:
        """Load history only when a duration metric actually needs it.

        Sprint scope reads stay lightweight. Completed tasks that already carry
        transitions are reused as-is; missing histories are fetched sequentially
        through the certified adapter path to avoid burst load on AS21/SWTR.
        """
        hydrated: list[Task] = []
        for task in tasks:
            if not task.is_completed or task.status_transitions:
                hydrated.append(task)
                continue
            history = await self.adapter.get_task_history(task.key)
            hydrated.append(task.model_copy(update={"status_transitions": history}))
        return hydrated

    async def _hydrate_active_history(self, tasks: list[Task]) -> list[Task]:
        """Hydrate active-task history sequentially for grounded stalled detection."""
        hydrated: list[Task] = []
        for task in tasks:
            if task.is_completed or task.status_transitions:
                hydrated.append(task)
                continue
            history = await self.adapter.get_task_history(task.key)
            hydrated.append(task.model_copy(update={"status_transitions": history}))
        return hydrated

    @staticmethod
    def _effort(tasks: list[Task], completed: list[Task]) -> tuple[str, float, float]:
        if tasks and all(task.estimate_hours is not None for task in tasks):
            return "hours", round(sum(task.estimate_hours or 0 for task in tasks), 2), round(sum(task.estimate_hours or 0 for task in completed), 2)
        return "tasks", float(len(tasks)), float(len(completed))

    def _duration_result(self, sprint_id: str, metric: str, values: list[float], tasks: list[Task]) -> CapabilityResult:
        data = {
            "sprint_id": sprint_id,
            "metric": metric,
            "unit": "hours",
            "sample_size": len(values),
            "average_hours": round(mean(values), 2) if values else None,
            "median_hours": round(median(values), 2) if values else None,
            "values_hours": [round(value, 2) for value in values],
        }
        label = "Cycle time" if metric == "cycle_time" else "Lead time"
        answer = f"{label} {sprint_id}: недостаточно завершённых задач с историей." if not values else f"{label} {sprint_id}: avg {data['average_hours']} ч, median {data['median_hours']} ч, n={len(values)}."
        return CapabilityResult(
            answer=answer,
            data=data,
            evidence=self._task_evidence(sprint_id, tasks, f"{metric}_input"),
            warnings=[] if values else [f"{metric}_insufficient_history"],
        )

    @staticmethod
    def _completion_time(task: Task):
        completed = [t.timestamp for t in task.status_transitions if t.to_status in (TaskStatus.RESOLVED, TaskStatus.CLOSED, TaskStatus.CANCELLED)]
        return min(completed) if completed else None

    @classmethod
    def _cycle_hours(cls, task: Task) -> float | None:
        end = cls._completion_time(task)
        starts = [t.timestamp for t in task.status_transitions if t.to_status == TaskStatus.IN_PROGRESS]
        if not end or not starts:
            return None
        start = min(starts)
        return max(0.0, (end - start).total_seconds() / 3600)

    @classmethod
    def _lead_hours(cls, task: Task) -> float | None:
        end = cls._completion_time(task)
        if not end:
            return None
        return max(0.0, (end - task.created_at).total_seconds() / 3600)

    @staticmethod
    def _current_status_hours(task: Task) -> float | None:
        if not task.status_transitions:
            return None
        latest = max(task.status_transitions, key=lambda transition: transition.timestamp)
        from datetime import datetime
        return max(0.0, (datetime.now(tz=latest.timestamp.tzinfo) - latest.timestamp).total_seconds() / 3600)

    @staticmethod
    def _task_data(task: Task) -> dict[str, object]:
        return {"key": task.key, "title": task.title, "status": task.status.value, "assignee": task.assignee, "priority": task.priority.value if task.priority else None, "estimate_hours": task.estimate_hours, "age_days": task.age_days}

    @staticmethod
    def _task_evidence(sprint_id: str, tasks: list[Task], kind: str) -> list[Evidence]:
        return [Evidence(type=kind, source="as21", entity_id=task.key, label=sprint_id, value=task.status.value) for task in tasks]

    @staticmethod
    def _sprint_sort_key(sprint_id: str) -> tuple[str, int]:
        match = re.search(r"^(.*?)-SPRNT-(\d+)$", sprint_id, re.I)
        return (match.group(1).upper(), int(match.group(2))) if match else (sprint_id.upper(), 0)
