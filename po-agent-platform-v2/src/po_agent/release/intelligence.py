"""Release Intelligence service for PO Agent Platform v2.

Analyzes release scope and provides insights:
- Release scope calculation
- Completed/remaining tasks
- Blocked tasks analysis
- Release risk analysis
- Delivery timeline prediction
"""

from datetime import datetime
from typing import Optional

from po_agent.domain.models import Task
from po_agent.llm.client import LLMClient, LLMMessage
from po_agent.llm.real import RealLLMClient
from po_agent.search.intelligence import TaskIntelligenceSearch
from po_agent.workflow.status import is_blocked as is_task_blocked


class ReleaseIntelligence:
    """Service for release intelligence and analysis."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
    ):
        """Initialize release intelligence service.

        Args:
            llm_client: LLM client for AI-based analysis (optional)
        """
        self.llm_client = llm_client
        self._search = TaskIntelligenceSearch()

    def calculate_release_scope(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate release scope based on tasks.

        Args:
            tasks: List of tasks in the release

        Returns:
            Dictionary with scope metrics
        """
        if not tasks:
            return {
                "total_tasks": 0,
                "features": 0,
                "bugs": 0,
                "improvements": 0,
                "total_estimate_hours": 0,
                "spaces": [],
            }

        # Categorize tasks by type
        features = 0
        bugs = 0
        improvements = 0
        spaces = set()

        for task in tasks:
            title_lower = (task.title or "").lower()
            desc_lower = (task.description or "").lower()
            combined = title_lower + " " + desc_lower

            # Categorization based on keywords
            if any(kw in combined for kw in ["bug", "fix", "error", "issue"]):
                bugs += 1
            elif any(kw in combined for kw in ["feat", "feature", "new", "implement"]):
                features += 1
            else:
                improvements += 1

            # Collect spaces
            if task.key:
                space = task.key.split("-")[0]
                spaces.add(space)

        total_estimate = sum(
            (task.estimate_hours or 0) for task in tasks if task.estimate_hours
        )

        return {
            "total_tasks": len(tasks),
            "features": features,
            "bugs": bugs,
            "improvements": improvements,
            "total_estimate_hours": total_estimate,
            "spaces": list(spaces),
        }

    def calculate_completion_status(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate completed vs remaining tasks.

        Args:
            tasks: List of tasks in the release

        Returns:
            Dictionary with completion metrics
        """
        if not tasks:
            return {
                "total": 0,
                "completed": 0,
                "remaining": 0,
                "percentage": 0,
            }

        total = len(tasks)
        completed = len(
            [t for t in tasks if t.status.value in ("Resolved", "Closed")]
        )
        remaining = total - completed
        percentage = (completed / total * 100) if total > 0 else 0

        return {
            "total": total,
            "completed": completed,
            "remaining": remaining,
            "percentage": round(percentage, 1),
            "completed_tasks": [t.key for t in tasks if t.status.value in ("Resolved", "Closed")],
            "remaining_tasks": [t.key for t in tasks if t.status.value not in ("Resolved", "Closed")],
        }

    def analyze_blocked_tasks(
        self,
        tasks: list[Task],
    ) -> dict:
        """Analyze blocked tasks in release.

        Args:
            tasks: List of tasks in the release

        Returns:
            Dictionary with blocked task analysis
        """
        if not tasks:
            return {
                "total_blocked": 0,
                "blocked_tasks": [],
                "blocking_reasons": [],
            }

        blocked_tasks = []
        blocking_reasons = set()

        for task in tasks:
            if is_task_blocked(task.status.value):
                blocked_tasks.append({
                    "key": task.key,
                    "title": task.title,
                    "status": task.status.value,
                    "assignee": task.assignee,
                })
                blocking_reasons.add(task.status.value)

        return {
            "total_blocked": len(blocked_tasks),
            "blocked_tasks": blocked_tasks,
            "blocking_reasons": list(blocking_reasons),
            "percentage": round(len(blocked_tasks) / len(tasks) * 100, 1) if tasks else 0,
        }

    def calculate_delivery_risk(
        self,
        tasks: list[Task],
    ) -> dict:
        """Calculate delivery risk for release.

        Args:
            tasks: List of tasks in the release

        Returns:
            Dictionary with risk analysis
        """
        if not tasks:
            return {
                "overall_risk": "none",
                "risk_score": 0,
                "risks": [],
                "recommendations": [],
            }

        risks = []
        risk_score = 0
        recommendations = []

        # Calculate metrics
        total = len(tasks)
        completed = len([t for t in tasks if t.status.value in ("Resolved", "Closed")])
        blocked = len([t for t in tasks if is_task_blocked(t.status.value)])
        critical = len([t for t in tasks if t.priority and t.priority.value == "Critical"])

        # Risk factors
        completion_rate = completed / total if total > 0 else 0

        # Low completion rate risk
        if completion_rate < 0.3:
            risk_score += 30
            risks.append({
                "type": "low_completion_rate",
                "value": round(completion_rate * 100, 1),
                "severity": "high",
            })
            recommendations.append("Review scope and prioritize critical tasks")
        elif completion_rate < 0.5:
            risk_score += 15
            risks.append({
                "type": "moderate_completion_rate",
                "value": round(completion_rate * 100, 1),
                "severity": "medium",
            })

        # Blocked tasks risk
        if blocked > 0:
            risk_score += 20
            risks.append({
                "type": "blocked_tasks",
                "count": blocked,
                "severity": "high",
            })
            recommendations.append("Identify and remove blockers")

        # Critical tasks risk
        if critical > 0:
            not_completed_critical = len(
                [
                    t
                    for t in tasks
                    if t.priority and t.priority.value == "Critical" and t.status.value not in ("Resolved", "Closed")
                ]
            )
            if not_completed_critical > 0:
                risk_score += 25
                risks.append({
                    "type": "uncompleted_critical",
                    "count": not_completed_critical,
                    "severity": "high",
                })
                recommendations.append("Prioritize critical tasks for completion")

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

    async def generate_release_report_with_llm(
        self,
        tasks: list[Task],
    ) -> dict:
        """Generate comprehensive release report with LLM insights.

        Args:
            tasks: List of tasks in the release

        Returns:
            Dictionary with full release report
        """
        scope = self.calculate_release_scope(tasks)
        completion = self.calculate_completion_status(tasks)
        blocked = self.analyze_blocked_tasks(tasks)
        risk = self.calculate_delivery_risk(tasks)

        result = {
            "release_summary": {
                "total_tasks": scope["total_tasks"],
                "completed_tasks": completion["completed"],
                "scope": scope,
                "completion": completion,
                "blocked": blocked,
                "risk": risk,
            },
        }

        # Add LLM analysis if available
        if self.llm_client:
            llm_insights = await self._generate_llm_insights(
                tasks, scope, completion, risk
            )
            result["llm_insights"] = llm_insights

        return result

    async def _generate_llm_insights(
        self,
        tasks: list[Task],
        scope: dict,
        completion: dict,
        risk: dict,
    ) -> str:
        """Generate LLM-based insights for the release.

        Args:
            tasks: List of tasks in the release
            scope: Release scope data
            completion: Completion status data
            risk: Risk analysis data

        Returns:
            Natural language insights
        """
        if not self.llm_client:
            return "LLM insights not available"

        system_prompt = """You are a product owner assistant analyzing release progress for SberWorks Task Tracker (SWTR).

Provide release insights including:
1. Overall release health and completion status
2. Key risks and blockers
3. Recommendations for timely delivery
4. Scope optimization suggestions

Keep insights concise (3-5 sentences).
Use Russian language for the response.
"""

        user_prompt = f"""Release Analysis Request:
Please analyze the current release progress and provide actionable insights.

Scope:
- Total tasks: {scope["total_tasks"]}
- Features: {scope["features"]}
- Bugs: {scope["bugs"]}
- Improvements: {scope["improvements"]}
- Estimate: {scope["total_estimate_hours"]} hours

Completion:
- Completed: {completion["completed"]} ({completion["percentage"]}%)

Risk:
- Overall: {risk["overall_risk"]} (score: {risk["risk_score"]})
- Blocked tasks: N/A
- High priority risks: {len([r for r in risk["risks"] if r.get("severity") == "high"])}

Please provide release insights in Russian."""

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
