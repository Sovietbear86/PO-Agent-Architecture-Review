"""Task Quality Analysis service for PO Agent Platform v2.

Analyzes task quality based on:
1. Deterministic rules (length, completeness, etc.)
2. LLM-based insights with explanations
3. Scoring system (0-100)
"""

from typing import Optional

from po_agent.domain.models import Task
from po_agent.llm.client import LLMClient, LLMMessage
from po_agent.llm.real import RealLLMClient


class TaskQualityAnalysis:
    """Service for analyzing task quality."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
    ):
        """Initialize quality analysis service.

        Args:
            llm_client: LLM client for AI-based analysis (optional)
        """
        self.llm_client = llm_client

    def analyze_deterministic(self, task: Task) -> dict:
        """Analyze task quality using deterministic rules.

        Returns metrics without LLM.

        Args:
            task: Task to analyze

        Returns:
            Dictionary with deterministic analysis results
        """
        score = 100
        issues = []
        recommendations = []

        # Check title length
        title_length = len(task.title)
        if title_length < 10:
            score -= 20
            issues.append("Title is too short (less than 10 characters)")
            recommendations.append("Add more details to the title")
        elif title_length > 200:
            score -= 10
            issues.append("Title is too long (more than 200 characters)")

        # Check description length
        desc_length = len(task.description or "")
        if desc_length < 50:
            score -= 15
            issues.append("Description is too short (less than 50 characters)")
            recommendations.append("Add more context to the description")
        elif desc_length > 5000:
            score -= 5
            issues.append("Description is very long (more than 5000 characters)")

        # Check for required fields
        if not task.title:
            score -= 30
            issues.append("Title is missing")

        if not task.description:
            score -= 20
            issues.append("Description is missing")

        if not task.assignee:
            score -= 10
            issues.append("No assignee specified")
            recommendations.append("Assign the task to a team member")

        # Check status completeness
        if task.status.value == "Open" or task.status.value == "Open":
            # Check if there are any transitions
            if not task.status_transitions:
                score -= 10
                issues.append("Task has no status transitions")
                recommendations.append("Update the task status to reflect current state")

        # Check for attachments
        if not task.attachments:
            score -= 5
            issues.append("No attachments")
            recommendations.append("Add relevant attachments (documents, screenshots, etc.)")

        # Check for labels
        if not task.labels:
            score -= 5
            issues.append("No labels")

        # Determine quality level
        if score >= 80:
            quality_level = "good"
        elif score >= 60:
            quality_level = "fair"
        elif score >= 40:
            quality_level = "poor"
        else:
            quality_level = "very poor"

        return {
            "score": score,
            "quality_level": quality_level,
            "issues": issues,
            "recommendations": recommendations,
            "metrics": {
                "title_length": title_length,
                "description_length": desc_length,
                "has_title": bool(task.title),
                "has_description": bool(task.description),
                "has_assignee": bool(task.assignee),
                "has_attachments": len(task.attachments) > 0,
                "has_labels": len(task.labels) > 0,
            },
        }

    async def analyze_with_llm(
        self,
        task: Task,
        deterministic_result: Optional[dict] = None,
    ) -> dict:
        """Analyze task quality with LLM insights.

        Args:
            task: Task to analyze
            deterministic_result: Pre-computed deterministic analysis (optional)

        Returns:
            Dictionary with LLM-based analysis and explanation
        """
        if not self.llm_client:
            # Fallback to deterministic only
            if deterministic_result:
                return {
                    "deterministic": deterministic_result,
                    "llm": None,
                }
            return {
                "deterministic": self.analyze_deterministic(task),
                "llm": None,
            }

        # Get deterministic analysis if not provided
        if not deterministic_result:
            deterministic_result = self.analyze_deterministic(task)

        # Build prompt for LLM
        system_prompt = """You are a product owner assistant analyzing task quality for SberWorks Task Tracker (SWTR).

Analyze task quality and provide:
1. Overall quality score (0-100)
2. List of quality issues with severity (high/medium/low)
3. Specific recommendations for improvement
4. Brief explanation for the quality assessment

Keep your analysis concise but actionable.
Use Russian language for the response.
"""

        user_prompt = f"""Task Analysis Request:
Please analyze the quality of this task and provide actionable insights.

Task Details:
- Key: {task.key}
- Title: {task.title}
- Description: {task.description or "Not provided"}
- Status: {task.status.value}
- Assignee: {task.assignee or "Not assigned"}
- Priority: {task.priority.value if task.priority else "Not specified"}
- Labels: {", ".join(task.labels) if task.labels else "None"}
- Attachments: {len(task.attachments)}

Deterministic Analysis Results:
{deterministic_result}

Please provide your quality assessment in Russian."""
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self.llm_client.complete(messages)
            llm_analysis = response.choices[0].message.content if response.choices else "Analysis failed"
        except Exception as e:
            print(f"LLM quality analysis error: {e}")
            llm_analysis = "Unable to generate LLM analysis"

        return {
            "deterministic": deterministic_result,
            "llm": {
                "analysis": llm_analysis,
                "model": self.llm_client.default_model if hasattr(self.llm_client, 'default_model') else "unknown",
            },
        }

    def calculate_quality_score(self, task: Task) -> int:
        """Calculate overall quality score for a task.

        Args:
            task: Task to score

        Returns:
            Quality score from 0 to 100
        """
        analysis = self.analyze_deterministic(task)
        return analysis["score"]

    def get_quality_level(self, score: int) -> str:
        """Convert score to quality level.

        Args:
            score: Quality score (0-100)

        Returns:
            Quality level string
        """
        if score >= 80:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "very poor"

    def generate_quality_report(self, task: Task) -> dict:
        """Generate complete quality report for a task.

        Args:
            task: Task to report on

        Returns:
            Complete quality report dictionary
        """
        deterministic = self.analyze_deterministic(task)

        return {
            "task_key": task.key,
            "task_title": task.title,
            "analysis_timestamp": __import__("datetime").datetime.now().isoformat(),
            "deterministic_analysis": deterministic,
            "quality_level": deterministic["quality_level"],
            "score": deterministic["score"],
            "summary": self._generate_summary(deterministic),
        }

    async def generate_quality_report_with_llm(
        self,
        task: Task,
    ) -> dict:
        """Generate complete quality report with LLM insights.

        Args:
            task: Task to report on

        Returns:
            Complete quality report dictionary
        """
        deterministic = self.analyze_deterministic(task)
        llm_result = await self.analyze_with_llm(task, deterministic)

        return {
            "task_key": task.key,
            "task_title": task.title,
            "analysis_timestamp": __import__("datetime").datetime.now().isoformat(),
            "deterministic_analysis": deterministic,
            "llm_analysis": llm_result.get("llm"),
            "quality_level": deterministic["quality_level"],
            "score": deterministic["score"],
            "summary": self._generate_summary(deterministic),
        }

    def _generate_summary(self, analysis: dict) -> str:
        """Generate a summary from analysis results.

        Args:
            analysis: Analysis result dictionary

        Returns:
            Summary string
        """
        score = analysis["score"]
        issues = analysis["issues"]
        quality_level = analysis["quality_level"]

        if not issues:
            return f"Task quality is {quality_level} (score: {score}/100). All quality checks passed."

        return f"Task quality is {quality_level} (score: {score}/100). {len(issues)} issue(s) detected. See details for recommendations."
