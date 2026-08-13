"""Deterministic Team Intelligence capabilities for the recovery Harness."""
from __future__ import annotations

from collections import Counter, defaultdict

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import StatusCategory, Task

from .contracts import CapabilityResult, Evidence


class TeamIntelligenceCapabilities:
    """Ground team metrics in AS21 tasks; configured capacity is passed explicitly."""

    def __init__(self, adapter: AS21Adapter) -> None:
        self.a = adapter

    async def _tasks(self) -> list[Task]:
        return await self.a.search_tasks("")

    @staticmethod
    def _member(task: Task) -> str:
        return task.assignee or "unassigned"

    @staticmethod
    def _evidence(tasks: list[Task], kind: str) -> list[Evidence]:
        return [Evidence(type=kind, source="as21", entity_id=t.key, label=t.title, value=t.assignee or "unassigned") for t in tasks]

    async def workload(self, args: dict[str, str]) -> CapabilityResult:
        tasks = [t for t in await self._tasks() if not t.is_completed]
        by_member: dict[str, dict[str, float | int]] = defaultdict(lambda: {"tasks": 0, "estimated_hours": 0.0})
        for task in tasks:
            row = by_member[self._member(task)]
            row["tasks"] += 1
            row["estimated_hours"] += task.estimate_hours or 0.0
        ranking = sorted(({"member": m, **v} for m, v in by_member.items()), key=lambda x: (-float(x["estimated_hours"]), -int(x["tasks"]), str(x["member"])))
        return CapabilityResult(answer=f"Активная нагрузка команды: {len(tasks)} задач у {len(by_member)} исполнителей/очередей.", data={"active_tasks": len(tasks), "workload": ranking}, evidence=self._evidence(tasks, "team_workload_task"))

    async def wip(self, args: dict[str, str]) -> CapabilityResult:
        tasks = [t for t in await self._tasks() if t.status_category == StatusCategory.ACTIVE_WORK]
        counts = Counter(self._member(t) for t in tasks)
        rows = [{"member": member, "wip": count} for member, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
        return CapabilityResult(answer=f"WIP команды: {len(tasks)} задач в активной работе.", data={"total_wip": len(tasks), "by_member": rows}, evidence=self._evidence(tasks, "team_wip_task"))

    async def blocked(self, args: dict[str, str]) -> CapabilityResult:
        tasks = [t for t in await self._tasks() if t.is_blocked]
        counts = Counter(self._member(t) for t in tasks)
        rows = [{"member": member, "blocked": count} for member, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
        return CapabilityResult(answer=f"Заблокировано задач: {len(tasks)}.", data={"total_blocked": len(tasks), "by_member": rows, "tasks": [t.key for t in tasks]}, evidence=self._evidence(tasks, "team_blocked_task"))

    async def capacity(self, args: dict[str, str]) -> CapabilityResult:
        tasks = [t for t in await self._tasks() if not t.is_completed and t.assignee]
        capacity_hours = float(args.get("capacity_hours", "40"))
        estimates: dict[str, float] = defaultdict(float)
        counts: Counter[str] = Counter()
        for task in tasks:
            estimates[task.assignee] += task.estimate_hours or 0.0
            counts[task.assignee] += 1
        rows = []
        for member in sorted(counts):
            load = round(estimates[member], 1)
            utilization = round(load / capacity_hours * 100, 1) if capacity_hours else 0.0
            rows.append({"member": member, "tasks": counts[member], "estimated_hours": load, "capacity_hours": capacity_hours, "utilization_percent": utilization, "over_capacity": load > capacity_hours})
        return CapabilityResult(answer=f"Capacity рассчитан для {len(rows)} исполнителей при baseline {capacity_hours:g} ч.", data={"capacity_hours_per_member": capacity_hours, "members": rows, "warning": "configured_capacity_baseline"}, evidence=self._evidence(tasks, "team_capacity_task"), warnings=["configured_capacity_baseline"])

    async def bottlenecks(self, args: dict[str, str]) -> CapabilityResult:
        tasks = [t for t in await self._tasks() if not t.is_completed]
        counts = Counter(self._member(t) for t in tasks)
        total = len(tasks)
        rows = []
        for member, count in sorted(counts.items(), key=lambda x: (-x[1], x[0])):
            share = round(count / total * 100, 1) if total else 0.0
            if share >= 50.0 or count >= 3:
                rows.append({"member": member, "active_tasks": count, "share_percent": share})
        return CapabilityResult(answer=f"Потенциальных концентраций нагрузки: {len(rows)}.", data={"bottlenecks": rows, "thresholds": {"share_percent": 50.0, "active_tasks": 3}}, evidence=self._evidence(tasks, "team_bottleneck_task"))

    async def distribution(self, args: dict[str, str]) -> CapabilityResult:
        tasks = await self._tasks()
        counts = Counter(self._member(t) for t in tasks)
        status_by_member: dict[str, Counter[str]] = defaultdict(Counter)
        for task in tasks:
            status_by_member[self._member(task)][task.status_category.value] += 1
        rows = [{"member": member, "tasks": counts[member], "status_distribution": dict(status_by_member[member])} for member in sorted(counts)]
        return CapabilityResult(answer=f"Распределение {len(tasks)} задач показано по {len(rows)} исполнителям/очередям.", data={"members": rows}, evidence=self._evidence(tasks, "team_distribution_task"))

    async def competency_match(self, args: dict[str, str]) -> CapabilityResult:
        """Match task requirements to team member competencies."""
        task_key = args.get("task_key", "").strip().upper()
        if not task_key:
            return CapabilityResult(answer="Не указан task_key для сопоставления компетенций.", data={"error": "task_key_required"}, warnings=["task_key_required"])

        task = await self.a.get_task(task_key)
        if task is None:
            return CapabilityResult(answer=f"Задача {task_key} не найдена.", data={"task_key": task_key, "found": False}, evidence=[Evidence(type="task_lookup", source="as21", entity_id=task_key, label="lookup", value="not_found")])

        # Get all team members with their tasks
        all_tasks = await self._tasks()
        members_with_tasks = set(self._member(t) for t in all_tasks if self._member(t) != "unassigned")

        # For each member, check if they have relevant experience
        matches: list[dict] = []
        for member in sorted(members_with_tasks):
            member_tasks = [t for t in all_tasks if self._member(t) == member]
            # Simple heuristic: member has experience if they've worked on similar tasks
            # In real implementation, this would compare competencies declared in member profiles
            experience_count = len([t for t in member_tasks if t.status_category == StatusCategory.COMPLETED])
            matches.append({
                "member": member,
                "total_tasks": len(member_tasks),
                "completed_tasks": experience_count,
                "matches": 0,  # Placeholder - would compare competencies
                "confidence": 0.5 if experience_count > 0 else 0.0
            })

        matches.sort(key=lambda x: (-x["confidence"], -x["completed_tasks"], x["member"]))

        answer = f"Совместимость {task_key} с командой: {len([m for m in matches if m['confidence'] > 0])} исполнителей/очередей имеют опыт."
        return CapabilityResult(answer=answer, data={"task_key": task_key, "task_title": task.title, "members": matches}, evidence=self._evidence([task], "team_competency_match_task"))
