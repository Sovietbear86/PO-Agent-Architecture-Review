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
        # Prefer the stable login for aggregation. Display names are not stable
        # identifiers and can merge/split one person when source formatting changes.
        return task.assignee_login or task.assignee or "unassigned"

    @staticmethod
    def _member_name(task: Task) -> str | None:
        return task.assignee

    @staticmethod
    def _evidence(tasks: list[Task], kind: str) -> list[Evidence]:
        return [Evidence(type=kind, source="as21", entity_id=t.key, label=t.title, value=t.assignee_login or t.assignee or "unassigned") for t in tasks]

    async def workload(self, args: dict[str, str]) -> CapabilityResult:
        """Return factual workload by assignee from the current real task corpus.

        Workload is deliberately task-count based. Estimate/capacity information is
        surfaced only when it is actually present in AS21 and is never invented.
        Completed tasks are reported separately from active/WIP so callers can audit
        the aggregation without confusing historical throughput with current load.
        """
        tasks = await self._tasks()
        by_member: dict[str, dict[str, object]] = {}

        for task in tasks:
            member = self._member(task)
            row = by_member.setdefault(
                member,
                {
                    "member": member,
                    "name": self._member_name(task),
                    "active_tasks": 0,
                    "wip": 0,
                    "in_progress": 0,
                    "blocked": 0,
                    "completed": 0,
                    "estimated_hours": 0.0,
                    "estimated_hours_available": False,
                },
            )
            # Preserve a real display name if an earlier row was created from a
            # task where the source exposed only the login.
            if not row["name"] and self._member_name(task):
                row["name"] = self._member_name(task)

            if task.is_completed:
                row["completed"] = int(row["completed"]) + 1
                continue

            row["active_tasks"] = int(row["active_tasks"]) + 1
            if task.status_category == StatusCategory.ACTIVE_WORK:
                row["wip"] = int(row["wip"]) + 1
                row["in_progress"] = int(row["in_progress"]) + 1
            if task.is_blocked:
                row["blocked"] = int(row["blocked"]) + 1
            if task.estimate_hours is not None:
                row["estimated_hours"] = float(row["estimated_hours"]) + task.estimate_hours
                row["estimated_hours_available"] = True

        rows = list(by_member.values())
        for row in rows:
            if row["estimated_hours_available"]:
                row["estimated_hours"] = round(float(row["estimated_hours"]), 2)
            else:
                # Missing estimates are unknown, not zero workload.
                row["estimated_hours"] = None

        rows.sort(key=lambda row: (-int(row["active_tasks"]), -int(row["wip"]), str(row["member"])))
        active_tasks = sum(int(row["active_tasks"]) for row in rows)
        completed_tasks = sum(int(row["completed"]) for row in rows)
        unassigned_active = next((int(row["active_tasks"]) for row in rows if row["member"] == "unassigned"), 0)

        warnings: list[str] = []
        if any(not bool(row["estimated_hours_available"]) for row in rows):
            warnings.append("estimate_hours_partially_or_fully_unavailable")
        if unassigned_active:
            warnings.append("unassigned_active_tasks_present")

        return CapabilityResult(
            answer=f"Текущая нагрузка команды: {active_tasks} активных задач у {len(rows)} исполнителей/очередей.",
            data={
                "source": "as21",
                "active_tasks": active_tasks,
                "completed_tasks": completed_tasks,
                "members_count": len(rows),
                "unassigned_active_tasks": unassigned_active,
                "workload": rows,
            },
            evidence=self._evidence(tasks, "team_workload_task"),
            warnings=warnings,
        )

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
            member = self._member(task)
            estimates[member] += task.estimate_hours or 0.0
            counts[member] += 1
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
