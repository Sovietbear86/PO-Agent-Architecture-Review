"""Sprint Intelligence service for PO Agent Platform v2.

Analyzes sprint health and provides insights:
- Sprint health score
- Completion ratio
- Velocity prediction
- Risk analysis
- Team capacity
"""

from datetime import datetime, timedelta
from typing import Optional

from po_agent.domain.models import Task
from po_agent.llm.client import LLMClient, LLMMessage
from po_agent.llm.real import RealLLMClient
from po_agent.search.intelligence import TaskIntelligenceSearch
from po_agent.workflow.engine import WorkflowEngine
from po_agent.metrics.engine import MetricsEngine
from po_agent.workflow.status import is_blocked as is_task_blocked


class SprintIntelligence:
    """Service for sprint intelligence and analysis."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
    ):
        """Initialize sprint intelligence service.

        Args:
            llm_client: LLM client for AI-based analysis (optional)
        """
        self.llm_client = llm_client
        self._search = TaskIntelligenceSearch()
        self._workflow = WorkflowEngine()
        self._metrics = MetricsEngine()

    def calculate_sprint_health(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate overall sprint health score.

        Args:
            tasks: List of tasks in the sprint

        Returns:
            Dictionary with health score and breakdown
        """
        if not tasks:
            return {
                "score": 0,
                "status": "no_tasks",
                "breakdown": {},
                "issues": [],
            }

        total = len(tasks)
        completed = len([t for t in tasks if t.status.value in ("Resolved", "Closed")])
        in_progress = len([t for t in tasks if t.status.value == "In progress"])
        open_tasks = len([t for t in tasks if t.status.value == "Open"])
        blocked = len([t for t in tasks if is_task_blocked(t.status.value)])

        # Calculate score (0-100)
        score = 0
        issues = []

        # Completion ratio contribution (max 40 points)
        completion_ratio = completed / total if total > 0 else 0
        score += completion_ratio * 40

        # Velocity contribution (max 30 points) - based on in_progress
        velocity_ratio = in_progress / total if total > 0 else 0
        score += velocity_ratio * 30

        # Blocked tasks penalty (max -20 points)
        blocked_ratio = blocked / total if total > 0 else 0
        score -= blocked_ratio * 20

        # Open tasks penalty (max -10 points)
        open_ratio = open_tasks / total if total > 0 else 0
        score -= open_ratio * 10

        # Clamp to valid range
        score = max(0, min(100, score))

        # Determine health status
        if score >= 80:
            status = "healthy"
        elif score >= 60:
            status = "watching"
        elif score >= 40:
            status = "at_risk"
        else:
            status = "in_danger"

        # Generate issues if any
        if blocked > 0:
            issues.append({
                "type": "blocked",
                "count": blocked,
                "message": f"{blocked} task(s) are blocked",
            })

        if open_ratio > 0.5:
            issues.append({
                "type": "low_velocity",
                "count": int(open_ratio * 100),
                "message": f"High percentage of open tasks ({int(open_ratio * 100)}%)",
            })

        return {
            "score": round(score, 1),
            "status": status,
            "breakdown": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "open": open_tasks,
                "blocked": blocked,
                "completion_ratio": round(completion_ratio * 100, 1),
            },
            "issues": issues,
        }

    def calculate_completion_ratio(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate completion ratio for a sprint.

        Args:
            tasks: List of tasks in the sprint

        Returns:
            Dictionary with completion ratio data
        """
        if not tasks:
            return {
                "total": 0,
                "completed": 0,
                "remaining": 0,
                "ratio": 0,
                "percentage": 0,
            }

        total = len(tasks)
        completed = len([t for t in tasks if t.status.value in ("Resolved", "Closed")])
        remaining = total - completed
        ratio = completed / total if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "ratio": round(ratio, 4),
            "percentage": round(ratio * 100, 1),
        }

    def predict_velocity(
        self,
        tasks: list[Task],
        historical_sprints: Optional[list[list[Task]]] = None,
    ) -> dict:
        """Predict sprint velocity based on historical data.

        Args:
            tasks: Current sprint tasks
            historical_sprints: Previous sprints with tasks (optional)

        Returns:
            Dictionary with velocity predictions
        """
        current_sprint_total = len(tasks)
        current_sprint_completed = len([t for t in tasks if t.status.value in ("Resolved", "Closed")])

        result = {
            "current_sprint": {
                "total": current_sprint_total,
                "completed": current_sprint_completed,
                "velocity": current_sprint_completed,  # Velocity = completed tasks
            },
            "predictions": {},
        }

        if historical_sprints and len(historical_sprints) > 0:
            # Calculate historical velocities
            historical_velocities = []
            for sprint_tasks in historical_sprints:
                completed = len([t for t in sprint_tasks if t.status.value in ("Resolved", "Closed")])
                if completed > 0:
                    historical_velocities.append(completed)

            if historical_velocities:
                avg_velocity = sum(historical_velocities) / len(historical_velocities)
                min_velocity = min(historical_velocities)
                max_velocity = max(historical_velocities)

                # Simple prediction (same as average)
                predicted_velocity = avg_velocity

                result["historical"] = {
                    "sprints_count": len(historical_sprints),
                    "average_velocity": round(avg_velocity, 2),
                    "min_velocity": min_velocity,
                    "max_velocity": max_velocity,
                    "velocity_std": round(
                        (sum((v - avg_velocity) ** 2 for v in historical_velocities) / len(historical_velocities)) ** 0.5,
                        2,
                    ),
                }
                result["predictions"] = {
                    "predicted_velocity": round(predicted_velocity, 2),
                    "confidence": "medium" if len(historical_velocities) >= 3 else "low",
                }

        return result

    def analyze_sprint_risks(
        self,
        tasks: list[Task],
    ) -> dict:
        """Analyze sprint risks and provide recommendations.

        Args:
            tasks: List of tasks in the sprint

        Returns:
            Dictionary with risk analysis and recommendations
        """
        if not tasks:
            return {
                "overall_risk": "none",
                "risks": [],
                "recommendations": [],
            }

        total = len(tasks)
        high_priority = len([t for t in tasks if t.priority and t.priority.value == "Critical"])
        blocked = len([t for t in tasks if is_task_blocked(t.status.value)])
        high_estimate = len([t for t in tasks if t.estimate_hours and t.estimate_hours > 20])
        missing_assignee = len([t for t in tasks if not t.assignee])

        risks = []
        recommendations = []

        # Risk scoring
        risk_score = 0

        # Critical priority risk
        if high_priority > 0:
            risk_score += 20
            risks.append({
                "type": "high_priority",
                "count": high_priority,
                "severity": "high" if high_priority > 3 else "medium",
            })
            recommendations.append("Review high-priority tasks for resource allocation")

        # Blocked tasks risk
        if blocked > 0:
            risk_score += 30
            risks.append({
                "type": "blocked_tasks",
                "count": blocked,
                "severity": "high",
            })
            recommendations.append("Identify blockers and remove impediments")

        # Estimate risk
        if high_estimate > 0:
            risk_score += 15
            risks.append({
                "type": "large_estimates",
                "count": high_estimate,
                "severity": "medium",
            })
            recommendations.append("Break down large tasks into smaller units")

        # Assignee risk
        if missing_assignee > 0:
            risk_score += 15
            risks.append({
                "type": "unassigned_tasks",
                "count": missing_assignee,
                "severity": "medium",
            })
            recommendations.append("Assign tasks to team members")

        # Determine overall risk
        if risk_score >= 60:
            overall_risk = "high"
        elif risk_score >= 30:
            overall_risk = "medium"
        elif risk_score > 0:
            overall_risk = "low"
        else:
            overall_risk = "none"

        return {
            "overall_risk": overall_risk,
            "risk_score": risk_score,
            "risks": risks,
            "recommendations": recommendations,
        }

    async def generate_sprint_report_with_llm(
        self,
        tasks: list[Task],
        historical_sprints: Optional[list[list[Task]]] = None,
    ) -> dict:
        """Generate comprehensive sprint report with LLM insights.

        Args:
            tasks: List of tasks in the sprint
            historical_sprints: Previous sprints with tasks (optional)

        Returns:
            Dictionary with full sprint report
        """
        # Calculate deterministic metrics
        health = self.calculate_sprint_health(tasks)
        completion = self.calculate_completion_ratio(tasks)
        velocity = self.predict_velocity(tasks, historical_sprints)
        risks = self.analyze_sprint_risks(tasks)

        result = {
            "sprint_summary": {
                "total_tasks": len(tasks),
                "completed_tasks": completion["completed"],
                "health_score": health["score"],
                "health_status": health["status"],
                "completion_percentage": completion["percentage"],
                "overall_risk": risks["overall_risk"],
            },
            "detailed_metrics": {
                "health": health,
                "completion": completion,
                "velocity": velocity,
                "risks": risks,
            },
        }

        # Add LLM analysis if available
        if self.llm_client:
            llm_insights = await self._generate_llm_insights(tasks, health, velocity)
            result["llm_insights"] = llm_insights

        return result

    async def _generate_llm_insights(
        self,
        tasks: list[Task],
        health: dict,
        velocity: dict,
    ) -> str:
        """Generate LLM-based insights for the sprint.

        Args:
            tasks: List of tasks in the sprint
            health: Sprint health data
            velocity: Velocity prediction data

        Returns:
            Natural language insights
        """
        if not self.llm_client:
            return "LLM insights not available"

        system_prompt = """You are a product owner assistant analyzing sprint performance for SberWorks Task Tracker (SWTR).

Provide sprint insights including:
1. Overall sprint health assessment
2. Key successes and challenges
3. Recommendations for improvement
4. Velocity trends and predictions

Keep insights concise (3-5 sentences).
Use Russian language for the response.
"""

        user_prompt = f"""Sprint Analysis Request:
Please analyze the current sprint performance and provide actionable insights.

Health Status: {health['status']} (score: {health['score']}/100)
Completion: {health['breakdown']['completion_ratio']}%
Velocity: {velocity['current_sprint']['velocity']} tasks completed

Blocked Tasks: {health['breakdown']['blocked']}
Issues: {health['issues']}

Please provide sprint insights in Russian."""

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self.llm_client.complete(messages)
            return response.choices[0].message.content if response.choices else "Analysis failed"
        except Exception as e:
            print(f"LLM insight generation error: {e}")
            return "Unable to generate LLM insights"
