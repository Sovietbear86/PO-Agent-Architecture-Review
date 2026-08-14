"""Metrics Engine Core for PO Agent Platform v2.

This module provides comprehensive metrics calculation for team performance analysis.
Implements standard Lean/Agile metrics:
- Throughput
- Work In Progress (WIP)
- Cycle Time
- Lead Time
- Flow Efficiency
- Velocity
"""

from datetime import datetime, timedelta
from typing import Optional

from po_agent.domain.models import (
    StatusCategory,
    StatusTransition,
    Task,
    TaskStatus,
)


class MetricsEngine:
    """Engine for calculating team performance metrics.

    Implements metrics from the DORA framework and Lean/Agile practices:
    - Throughput: Number of completed tasks per period
    - WIP: Number of tasks in progress
    - Cycle Time: Time from start to completion
    - Lead Time: Time from request to delivery
    - Flow Efficiency: Value-adding time vs total time
    - Velocity: Points completed per sprint
    """

    def __init__(self):
        """Initialize metrics engine."""
        self._metrics_cache: dict = {}

    def calculate_throughput(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate throughput metrics.

        Throughput measures the rate at which tasks are completed.
        Formula: completed_tasks / period_days * 30 (monthly rate)

        Args:
            tasks: List of tasks to analyze
            period_days: Analysis period in days

        Returns:
            Dictionary with throughput metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(days=period_days)

        # Count completed tasks in period
        completed_count = 0
        total_cycle_days = 0
        max_cycle_days = 0
        completed_tasks = []

        for task in tasks:
            # Check if task was completed in period
            completion_time = None

            # Find completion transition
            for transition in task.status_transitions:
                if transition.to_status.value in ("Resolved", "Closed"):
                    if transition.timestamp >= cutoff:
                        completion_time = transition.timestamp
                        break

            # Also check task status
            if not completion_time and task.status.value in ("Resolved", "Closed"):
                completion_time = task.updated_at

            if completion_time:
                completed_count += 1
                completed_tasks.append({
                    "key": task.key,
                    "completed_at": completion_time,
                })

                # Calculate cycle time for this task
                cycle_days = (completion_time - task.created_at).days
                if cycle_days > 0:
                    total_cycle_days += cycle_days
                    max_cycle_days = max(max_cycle_days, cycle_days)

        # Calculate metrics
        throughput = completed_count / max(period_days, 1) * 30  # Normalize to monthly
        avg_cycle_time = total_cycle_days / completed_count if completed_count > 0 else 0

        return {
            "period_days": period_days,
            "completed_count": completed_count,
            "throughput": round(throughput, 2),  # tasks per month
            "avg_cycle_time": round(avg_cycle_time, 2),  # days
            "max_cycle_time": max_cycle_days,
            "completed_tasks": completed_tasks,
        }

    def calculate_wip(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate Work In Progress metrics.

        WIP measures the number of tasks currently in progress.
        Helps identify bottlenecks and overloading.

        Args:
            tasks: List of tasks to analyze
            period_days: Analysis period in days

        Returns:
            Dictionary with WIP metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(days=period_days)

        active_tasks = 0
        in_progress_tasks = 0
        waiting_tasks = 0
        review_tasks = 0

        for task in tasks:
            # Check if task is active (created in period or still open)
            if task.created_at >= cutoff or is_active_status(task.status):
                active_tasks += 1

                if task.status.value == "In progress":
                    in_progress_tasks += 1
                elif is_waiting(task.status):
                    waiting_tasks += 1
                elif task.status.value in ("In review", "Ready for review"):
                    review_tasks += 1

        return {
            "period_days": period_days,
            "active_tasks": active_tasks,
            "in_progress": in_progress_tasks,
            "waiting": waiting_tasks,
            "review": review_tasks,
            "wip_limit_recommendation": max(3, active_tasks // 3),  # Typical limit
        }

    def calculate_cycle_time(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate cycle time metrics.

        Cycle time measures time from when work starts to completion.
        Only counts tasks that are in progress or completed.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary with cycle time metrics
        """
        cycle_times = []

        for task in tasks:
            cycle_time = self._calculate_single_cycle_time(task)
            if cycle_time is not None:
                cycle_times.append({
                    "key": task.key,
                    "cycle_time": cycle_time,
                })

        if not cycle_times:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p75": 0,
                "p95": 0,
            }

        times = [t["cycle_time"] for t in cycle_times]
        avg = sum(times) / len(times)
        sorted_times = sorted(times)

        return {
            "count": len(cycle_times),
            "avg": round(avg, 2),
            "min": round(min(times), 2),
            "max": round(max(times), 2),
            "p50": round(sorted_times[len(sorted_times) // 2], 2),
            "p75": round(sorted_times[int(len(sorted_times) * 0.75)], 2),
            "p95": round(sorted_times[int(len(sorted_times) * 0.95)], 2),
        }

    def calculate_lead_time(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate lead time metrics.

        Lead time measures time from task creation to completion.
        Includes time spent in backlog and waiting states.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary with lead time metrics
        """
        lead_times = []

        for task in tasks:
            lead_time = self._calculate_single_lead_time(task)
            if lead_time is not None:
                lead_times.append({
                    "key": task.key,
                    "lead_time": lead_time,
                })

        if not lead_times:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
                "p50": 0,
                "p75": 0,
                "p95": 0,
            }

        times = [t["lead_time"] for t in lead_times]
        avg = sum(times) / len(times)
        sorted_times = sorted(times)

        return {
            "count": len(lead_times),
            "avg": round(avg, 2),
            "min": round(min(times), 2),
            "max": round(max(times), 2),
            "p50": round(sorted_times[len(sorted_times) // 2], 2),
            "p75": round(sorted_times[int(len(sorted_times) * 0.75)], 2),
            "p95": round(sorted_times[int(len(sorted_times) * 0.95)], 2),
        }

    def calculate_flow_efficiency(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate flow efficiency metrics.

        Flow efficiency measures the percentage of time spent on value-adding work.
        Formula: cycle_time / lead_time

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary with flow efficiency metrics
        """
        efficiencies = []

        for task in tasks:
            lead_time = self._calculate_single_lead_time(task)
            cycle_time = self._calculate_single_cycle_time(task)

            if lead_time and cycle_time and lead_time > 0:
                efficiency = cycle_time / lead_time
                efficiencies.append({
                    "key": task.key,
                    "efficiency": round(efficiency, 4),
                })

        if not efficiencies:
            return {
                "count": 0,
                "avg": 0,
                "min": 0,
                "max": 0,
            }

        values = [e["efficiency"] for e in efficiencies]
        avg = sum(values) / len(values)

        return {
            "count": len(efficiencies),
            "avg": round(avg, 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    def calculate_velocity(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate velocity metrics.

        Velocity measures story points or complexity units completed per period.

        Args:
            tasks: List of tasks to analyze
            period_days: Analysis period in days

        Returns:
            Dictionary with velocity metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(days=period_days)

        velocities = []
        completed_points = 0
        completed_count = 0

        for task in tasks:
            # Check if completed in period
            completion_time = None
            for transition in task.status_transitions:
                if transition.to_status.value in ("Resolved", "Closed"):
                    if transition.timestamp >= cutoff:
                        completion_time = transition.timestamp
                        break

            if not completion_time and task.status.value in ("Resolved", "Closed"):
                completion_time = task.updated_at

            if completion_time:
                # Estimate points (simplified: count as 1 point, could be extracted from story points)
                points = self._estimate_task_points(task)
                completed_points += points
                completed_count += 1
                velocities.append(points)

        if not velocities:
            return {
                "period_days": period_days,
                "completed_tasks": completed_count,
                "total_points": completed_points,
                "avg_velocity": 0,
                "min_velocity": 0,
                "max_velocity": 0,
            }

        avg_velocity = completed_points / max(period_days, 1) * 30  # Monthly rate

        return {
            "period_days": period_days,
            "completed_tasks": completed_count,
            "total_points": completed_points,
            "avg_velocity": round(avg_velocity, 2),
            "min_velocity": min(velocities),
            "max_velocity": max(velocities),
            "velocities": velocities,
        }

    def calculate_blocked_time(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate blocked time metrics.

        Blocked time measures time spent in waiting/blocked states.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary with blocked time metrics
        """
        total_blocked = 0.0
        blocked_tasks = []

        for task in tasks:
            blocked_time = self._calculate_single_blocked_time(task)
            if blocked_time > 0:
                total_blocked += blocked_time
                blocked_tasks.append({
                    "key": task.key,
                    "blocked_time": round(blocked_time, 2),
                })

        return {
            "total_blocked_days": round(total_blocked, 2),
            "blocked_tasks": blocked_tasks,
            "avg_blocked_per_task": round(total_blocked / len(tasks), 2) if tasks else 0,
        }

    def calculate_completion_ratio(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate task completion ratio.

        Ratio of completed tasks vs total active tasks.

        Args:
            tasks: List of tasks to analyze
            period_days: Analysis period in days

        Returns:
            Dictionary with completion ratio metrics
        """
        now = datetime.now()
        cutoff = now - timedelta(days=period_days)

        completed = 0
        total = 0

        for task in tasks:
            if task.created_at >= cutoff:
                total += 1
                if task.status.value in ("Resolved", "Closed"):
                    completed += 1

        ratio = completed / total if total > 0 else 0

        return {
            "period_days": period_days,
            "completed": completed,
            "total": total,
            "ratio": round(ratio, 4),
        }

    def get_all_metrics(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Get all metrics in one call.

        Args:
            tasks: List of tasks to analyze
            period_days: Analysis period in days

        Returns:
            Dictionary with all metrics
        """
        return {
            "throughput": self.calculate_throughput(tasks, period_days),
            "wip": self.calculate_wip(tasks, period_days),
            "cycle_time": self.calculate_cycle_time(tasks),
            "lead_time": self.calculate_lead_time(tasks),
            "flow_efficiency": self.calculate_flow_efficiency(tasks),
            "velocity": self.calculate_velocity(tasks, period_days),
            "blocked_time": self.calculate_blocked_time(tasks),
            "completion_ratio": self.calculate_completion_ratio(tasks, period_days),
        }

    def _calculate_single_cycle_time(self, task: Task) -> Optional[float]:
        """Calculate cycle time for a single task."""
        # Find when work started (transition to in progress)
        work_start = None
        for transition in task.status_transitions:
            if "In progress" in transition.to_status.value:
                work_start = transition.timestamp
                break

        if not work_start:
            # Check if task is currently in progress
            if task.status.value == "In progress":
                work_start = task.created_at
            else:
                return None

        # Find when work ended
        work_end = None
        for transition in task.status_transitions:
            if transition.to_status.value in ("Resolved", "Closed"):
                work_end = transition.timestamp
                break

        if not work_end:
            # Task not completed yet
            return None

        return max(0, (work_end - work_start).days)

    def _calculate_single_lead_time(self, task: Task) -> Optional[float]:
        """Calculate lead time for a single task."""
        # Lead time is from creation to completion
        if task.status.value not in ("Resolved", "Closed"):
            return None

        # Find completion time
        completion_time = task.created_at
        for transition in task.status_transitions:
            if transition.to_status.value in ("Resolved", "Closed"):
                completion_time = transition.timestamp
                break

        return max(0, (completion_time - task.created_at).days)

    def _calculate_single_blocked_time(self, task: Task) -> float:
        """Calculate blocked time for a single task."""
        blocked_days = 0.0

        if task.status_transitions:
            transitions = task.status_transitions

            for i, transition in enumerate(transitions):
                current_status = transition.to_status.value.lower()

                # Check if status is blocked or waiting
                if "need info" in current_status or "blocked" in current_status:
                    if i < len(transitions) - 1:
                        next_transition = transitions[i + 1]
                        duration = next_transition.timestamp - transition.timestamp
                    else:
                        duration = datetime.now() - transition.timestamp

                    days = max(0, duration.total_seconds() / 86400)
                    blocked_days += days

        return blocked_days

    def _estimate_task_points(self, task: Task) -> int:
        """Estimate task points (simplified: returns 1)."""
        # In real implementation, extract from story points field
        # For now, return 1 as default
        return 1


def is_active_status(status: TaskStatus) -> bool:
    """Check if status is considered active."""
    active_categories = [
        StatusCategory.ACTIVE_WORK,
        StatusCategory.REVIEW,
        StatusCategory.REVIEW_QUEUE,
        StatusCategory.QA_QUEUE,
        StatusCategory.TESTING,
    ]
    return status.value in (
        "In progress",
        "In review",
        "Ready for review",
        "Ready for QA",
        "QA",
        "Reopened",
    )


def is_waiting(status: TaskStatus) -> bool:
    """Check if status is waiting."""
    return status.value in (
        "Need info",
        "Waiting",
        "On hold",
    )
