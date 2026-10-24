"""Workflow engine for PO Agent Platform v2.

This module provides workflow analysis capabilities including:
- Status timeline calculation
- Time in status metrics
- Blocked time analysis
- Cycle time calculation
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from po_agent.domain.models import (
    StatusCategory,
    StatusTransition,
    Task,
)
from po_agent.workflow.status import (
    is_active,
    is_blocked,
    is_terminal,
    is_waiting,
)


class WorkflowEngine:
    """Engine for analyzing task workflow metrics.

    Provides calculations for:
    - Status timeline (history of status changes)
    - Time in each status
    - Blocked time (time spent in waiting/blocked states)
    - Cycle time (time from in_progress to resolved/closed)
    """

    def __init__(self):
        """Initialize workflow engine."""
        self._status_transitions: list[StatusTransition] = []

    def calculate_status_timeline(self, task: Task) -> list[dict]:
        """Calculate status timeline for a task.

        Args:
            task: Task to analyze

        Returns:
            List of status changes with timestamps and categories
        """
        timeline = []

        # Add initial status
        if task.status_transitions:
            for transition in task.status_transitions:
                timeline.append({
                    "status": transition.to_status.value,
                    "status_category": transition.to_status.value,
                    "timestamp": transition.timestamp,
                    "author": transition.author,
                    "days_in_status": None,  # Calculated below
                })
        else:
            # No transitions, just initial status
            timeline.append({
                "status": task.status.value,
                "status_category": task.status_category.value,
                "timestamp": task.created_at,
                "author": "initial",
                "days_in_status": None,
            })

        # Sort by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        # Calculate days in each status
        for i, entry in enumerate(timeline):
            if i < len(timeline) - 1:
                next_timestamp = timeline[i + 1]["timestamp"]
                days = (next_timestamp - entry["timestamp"]).days
                entry["days_in_status"] = max(0, days)
            else:
                # Last status - calculate days from last change to now (handle timezone-aware)
                now = datetime.now(timezone.utc) if entry["timestamp"].tzinfo else datetime.now()
                days = (now - entry["timestamp"]).days
                entry["days_in_status"] = max(0, days)

        return timeline

    def calculate_time_in_status(
        self,
        task: Task,
        status: Optional[str] = None,
    ) -> dict[str, float]:
        """Calculate time spent in each status.

        Args:
            task: Task to analyze
            status: Optional specific status to analyze

        Returns:
            Dictionary mapping status to days spent
        """
        times: dict[str, float] = {}

        if task.status_transitions:
            transitions = task.status_transitions
            now = datetime.now()

            for i, transition in enumerate(transitions):
                current_status = transition.to_status.value.lower()

                if status and current_status != status.lower():
                    continue

                # Calculate duration
                if i < len(transitions) - 1:
                    next_transition = transitions[i + 1]
                    duration = next_transition.timestamp - transition.timestamp
                else:
                    # Last transition to current status
                    duration = now - transition.timestamp

                days = max(0, duration.total_seconds() / 86400)
                # Use lowercase status key for consistency
                times[current_status.lower()] = round(days, 2)

        # If no transitions, task is in initial status since creation
        if not times:
            current_status_lower = task.status.value.lower()
            duration = datetime.now() - task.created_at
            days = max(0, duration.total_seconds() / 86400)
            times[current_status_lower] = round(days, 2)

        return times

    def calculate_blocked_time(self, task: Task) -> float:
        """Calculate total blocked time for a task.

        Blocked time is time spent in waiting/blocked states.

        Args:
            task: Task to analyze

        Returns:
            Total blocked time in days
        """
        blocked_days = 0.0

        if task.status_transitions:
            transitions = task.status_transitions

            for i, transition in enumerate(transitions):
                current_status = transition.to_status.value.lower()

                # Check if status is blocked or waiting
                if is_blocked(current_status) or is_waiting(current_status):
                    # Calculate duration in this status
                    if i < len(transitions) - 1:
                        next_transition = transitions[i + 1]
                        duration = next_transition.timestamp - transition.timestamp
                    else:
                        duration = datetime.now() - transition.timestamp

                    days = max(0, duration.total_seconds() / 86400)
                    blocked_days += days

        # Also check initial status
        if is_blocked(task.status.value) or is_waiting(task.status.value):
            duration = datetime.now() - task.created_at
            days = max(0, duration.total_seconds() / 86400)
            blocked_days += days

        return round(blocked_days, 2)

    def calculate_cycle_time(self, task: Task) -> Optional[float]:
        """Calculate cycle time for a task.

        Cycle time is the duration from when work starts (in_progress)
        until the task is completed (resolved/closed).

        Args:
            task: Task to analyze

        Returns:
            Cycle time in days, or None if not applicable
        """
        # Find when work started (first transition to in_progress)
        work_start = None
        work_end = None

        for transition in task.status_transitions:
            to_status = transition.to_status.value.lower()
            if "in progress" in to_status:
                work_start = transition.timestamp
                break

        # Find when work ended (transition to resolved/closed)
        for transition in task.status_transitions:
            to_status = transition.to_status.value.lower()
            if to_status in ("resolved", "closed"):
                work_end = transition.timestamp
                break

        # If no transitions, check if task is in_progress
        if not work_start and "in progress" in task.status.value.lower():
            work_start = task.created_at
            work_end = datetime.now()

        if work_start and work_end:
            duration = work_end - work_start
            days = max(0, duration.total_seconds() / 86400)
            return round(days, 2)

        return None

    def calculate_lead_time(self, task: Task) -> Optional[float]:
        """Calculate lead time for a task.

        Lead time is from task creation until completion.

        Args:
            task: Task to analyze

        Returns:
            Lead time in days, or None if not completed
        """
        if not is_terminal(task.status):
            return None

        # Find completion timestamp
        completion_time = task.created_at

        for transition in task.status_transitions:
            if transition.to_status.value in ("resolved", "closed"):
                completion_time = transition.timestamp
                break

        duration = completion_time - task.created_at
        days = max(0, duration.total_seconds() / 86400)
        return round(days, 2)

    def calculate_throughput(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate throughput metrics.

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
        total_days = 0
        max_days = 0

        for task in tasks:
            # Check if task was completed in period
            completed = False
            for transition in task.status_transitions:
                if transition.to_status.value in ("resolved", "closed"):
                    if transition.timestamp >= cutoff:
                        completed = True
                        completed_count += 1
                        # Calculate cycle time for this task
                        cycle_days = (transition.timestamp - task.created_at).days
                        if cycle_days > 0:
                            total_days += cycle_days
                            max_days = max(max_days, cycle_days)
                        break

        # Calculate metrics
        throughput = completed_count / max(period_days, 1) * 30  # Normalize to monthly
        avg_cycle_time = total_days / completed_count if completed_count > 0 else 0

        return {
            "period_days": period_days,
            "completed_count": completed_count,
            "throughput": round(throughput, 2),  # tasks per month
            "avg_cycle_time": round(avg_cycle_time, 2),  # days
            "max_cycle_time": max_days,
            "completed_tasks": [t.key for t in tasks if any(
                tr.to_status.value in ("resolved", "closed") and tr.timestamp >= cutoff
                for tr in t.status_transitions
            )],
        }

    def calculate_wip(
        self,
        tasks: list[Task],
        period_days: int = 30,
    ) -> dict:
        """Calculate Work In Progress metrics.

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

        for task in tasks:
            # Check if task was created in period and is still active
            if task.created_at >= cutoff:
                if is_active(task.status):
                    active_tasks += 1
                    if task.status.value == "in_progress":
                        in_progress_tasks += 1
                    elif is_waiting(task.status):
                        waiting_tasks += 1

        return {
            "period_days": period_days,
            "active_tasks": active_tasks,
            "in_progress": in_progress_tasks,
            "waiting": waiting_tasks,
            "wip_limit_recommendation": max(3, active_tasks // 3),  # Typical limit
        }

    def get_workflow_health(
        self,
        task: Task,
    ) -> dict:
        """Get overall workflow health for a task.

        Args:
            task: Task to analyze

        Returns:
            Dictionary with health metrics and recommendations
        """
        timeline = self.calculate_status_timeline(task)
        blocked_time = self.calculate_blocked_time(task)
        cycle_time = self.calculate_cycle_time(task)

        # Calculate health score
        score = 100
        issues = []

        # Check for excessive blocked time (> 20% of cycle time)
        if cycle_time and blocked_time > cycle_time * 0.2:
            score -= 30
            issues.append({
                "type": "blocked_time",
                "severity": "high",
                "message": f"Blocked time ({blocked_time} days) is >20% of cycle time",
            })

        # Check for long waiting times
        waiting_status = task.status.value.lower()
        if is_waiting(task.status):
            waiting_days = self.calculate_time_in_status(task).get(waiting_status, 0)
            if waiting_days > 7:
                score -= 20
                issues.append({
                    "type": "waiting_time",
                    "severity": "medium",
                    "message": f"Task waiting for {waiting_days} days",
                })

        # Check for too many transitions (possible rework)
        if len(task.status_transitions) > 10:
            score -= 15
            issues.append({
                "type": "too_many_transitions",
                "severity": "medium",
                "message": f"Task has {len(task.status_transitions)} transitions (possible rework)",
            })

        # Determine status
        if score >= 80:
            status = "healthy"
        elif score >= 60:
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "score": score,
            "metrics": {
                "blocked_time_days": blocked_time,
                "cycle_time_days": cycle_time,
                "transitions_count": len(task.status_transitions),
            },
            "issues": issues,
            "recommendations": self._get_recommendations(issues),
        }

    def _get_recommendations(self, issues: list) -> list[str]:
        """Generate recommendations based on issues.

        Args:
            issues: List of issues from workflow health analysis

        Returns:
            List of recommendation strings
        """
        recommendations = []

        for issue in issues:
            if issue["type"] == "blocked_time":
                recommendations.append(
                    "Investigate blockers and unblock tasks as soon as possible"
                )
            elif issue["type"] == "waiting_time":
                recommendations.append(
                    "Follow up on tasks waiting for information or approvals"
                )
            elif issue["type"] == "too_many_transitions":
                recommendations.append(
                    "Review task for scope changes or rework patterns"
                )

        if not recommendations:
            recommendations.append("Task workflow is healthy, continue monitoring")

        return recommendations
