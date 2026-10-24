"""Task Summary service for PO Agent Platform v2.

Generates structured summaries for tasks including:
- Basic information (title, status, assignee)
- Metrics (cycle time, lead time)
- Context (priority, priority, related items)
- Analysis (health, risks, recommendations)
"""

from datetime import datetime
from typing import Optional

from po_agent.domain.models import Task
from po_agent.metrics.engine import MetricsEngine
from po_agent.workflow.engine import WorkflowEngine
from po_agent.llm.client import LLMClient, LLMMessage
from po_agent.llm.real import RealLLMClient


class TaskSummaryService:
    """Service for generating task summaries.

    Supports multiple summary types:
    1. Structured (deterministic, no LLM)
    2. LLM-based (natural language, with insights)
    3. Fallback (basic fields only)
    """

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        api_port: Optional[int] = None,
    ):
        """Initialize task summary service.

        Args:
            llm_client: LLM client for AI-based summaries (optional)
            api_port: Port of task-api server for workflow data (optional)
        """
        self.llm_client = llm_client
        self.api_port = api_port or 8003
        self._metrics_engine = MetricsEngine()
        self._workflow_engine = WorkflowEngine()

    def generate_structured_summary(self, task: Task) -> dict:
        """Generate structured summary for a task.

        Deterministic summary with metrics and context.

        Args:
            task: Task to summarize

        Returns:
            Dictionary with structured summary data
        """
        cycle_time = self._workflow_engine.calculate_cycle_time(task)
        lead_time = self._workflow_engine.calculate_lead_time(task)
        timeline = self._workflow_engine.calculate_status_timeline(task)
        blocked_time = self._workflow_engine.calculate_blocked_time(task)

        return {
            "key": task.key,
            "title": task.title,
            "status": {
                "value": task.status.value,
                "category": task.status_category.value,
            },
            "description": task.description,
            "assignee": task.assignee,
            "priority": task.priority.value if task.priority else None,
            "dates": {
                "created": task.created_at.isoformat(),
                "updated": task.updated_at.isoformat(),
                "deadline": task.due_date.isoformat() if task.due_date else None,
            },
            "metrics": {
                "cycle_time_days": cycle_time,
                "lead_time_days": lead_time,
                "blocked_time_days": blocked_time,
            },
            "workflow_timeline": timeline,
            "labels": task.labels,
            "source": task.source,
            "source_url": task.source_url,
        }

    async def generate_llm_summary(
        self,
        task: Task,
        context: Optional[dict] = None,
    ) -> str:
        """Generate LLM-based natural language summary.

        Uses real LLM for insights and analysis.

        Args:
            task: Task to summarize
            context: Additional context for analysis (optional)

        Returns:
            Natural language summary
        """
        if not self.llm_client:
            return self.generate_fallback_summary(task)

        structured = self.generate_structured_summary(task)

        system_prompt = """You are a helpful product owner assistant for SberWorks Task Tracker (SWTR).

Generate a natural language summary of a task that includes:
1. Brief description of what the task is about
2. Current status and priority
3. Key metrics (cycle time, lead time)
4. Any risks or issues detected
5. Recommendations if applicable

Keep the summary concise but informative (3-5 sentences).
Use Russian language for the response.
"""

        user_prompt = f"""Task Summary:
{structured}

Additional Context:
{context or "No additional context provided"}

Please generate a concise summary in Russian."""
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]

        try:
            response = await self.llm_client.complete(messages)
            if response.choices:
                return response.choices[0].message.content
        except Exception as e:
            print(f"LLM summary generation error: {e}")

        return self.generate_fallback_summary(task)

    def generate_fallback_summary(self, task: Task) -> str:
        """Generate fallback summary without LLM.

        Uses only task data and deterministic analysis.

        Args:
            task: Task to summarize

        Returns:
            Fallback summary string
        """
        cycle_time = self._workflow_engine.calculate_cycle_time(task)
        lead_time = self._workflow_engine.calculate_lead_time(task)
        blocked_time = self._workflow_engine.calculate_blocked_time(task)

        lines = [
            f"**{task.key}**: {task.title}",
            f"Статус: {task.status.value}",
            f"Приоритет: {task.priority.value if task.priority else 'Не указан'}",
            f"Исполнитель: {task.assignee or 'Не назначен'}",
        ]

        if cycle_time:
            lines.append(f"Время цикла: {cycle_time} дней")
        if lead_time:
            lines.append(f"Время от создания: {lead_time} дней")
        if blocked_time > 0:
            lines.append(f"Время в ожидании: {blocked_time} дней")

        # Add risk assessment based on workflow health
        health = self._workflow_engine.get_workflow_health(task)
        if health["status"] != "healthy":
            lines.append(f"⚠️ Риск: {health['issues'][0]['message'] if health['issues'] else 'Внимание к задаче'}")

        return "\n".join(lines)

    def generate_batch_summaries(
        self,
        tasks: list[Task],
        summary_type: str = "structured",
        context: Optional[dict] = None,
    ) -> list[dict]:
        """Generate summaries for multiple tasks.

        Args:
            tasks: List of tasks to summarize
            summary_type: Type of summary ("structured", "llm", "fallback")
            context: Additional context for analysis

        Returns:
            List of summary dictionaries
        """
        results = []

        for task in tasks:
            if summary_type == "structured":
                summary = self.generate_structured_summary(task)
            elif summary_type == "fallback":
                summary = {"key": task.key, "summary": self.generate_fallback_summary(task)}
            else:
                summary = {"key": task.key, "summary": "LLM summary requires async call"}

            results.append(summary)

        return results

    async def generate_batch_llm_summaries(
        self,
        tasks: list[Task],
        context: Optional[dict] = None,
    ) -> list[str]:
        """Generate LLM-based summaries for multiple tasks.

        Args:
            tasks: List of tasks to summarize
            context: Additional context for analysis

        Returns:
            List of natural language summaries
        """
        if not self.llm_client:
            return [self.generate_fallback_summary(t) for t in tasks]

        summaries = []
        for task in tasks:
            summary = await self.generate_llm_summary(task, context)
            summaries.append(summary)

        return summaries
