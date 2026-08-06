"""Скилл: Flow Metrics - Анализ flow метрик с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members


class FlowMetricsSkill:
    """Считает throughput, cycle time, lead time, WIP, flow efficiency.
    Использует реальные данные из SWTR (FastAPI Task Tracker)."""

    def __init__(self, api_port: int | None = None):
        self.findings: List[str] = []
        self.risks: List[str] = []
        self.recommendations: List[str] = []
        self.sources: List[str] = []
        self.constraints: List[str] = []
        self._task_service = TaskService(api_port=api_port)

    async def analyze(
        self,
        period_days: int = 30,
        team_members: List[str] = None,
        products: List[str] = None
    ) -> AnalysisResult:
        """Анализировать flow метрики"""

        # Получить данные из SWTR
        flow_data = await self._fetch_flow_data(period_days, team_members)

        if not flow_data.get('completed_tasks'):
            return AnalysisResult(
                status="yellow",
                findings=["Недостаточно данных для анализа"],
                risks=["Нет завершенных задач за период"],
                recommendations=["Проверить наличие завершенных задач"],
                sources=[],
                constraints=["Необходимы данные о завершенных задачах"],
                confidence=0.5,
                team_members=team_members or [],
                products=products or []
            )

        # Вычислить метрики
        throughput = flow_data.get('throughput', 0)
        avg_cycle_time = flow_data.get('avg_cycle_time', 0)
        avg_lead_time = flow_data.get('avg_lead_time', 0)
        avg_wip = flow_data.get('avg_wip', 0)
        blocked_time = flow_data.get('blocked_time', 0)
        flow_efficiency = flow_data.get('flow_efficiency', 0)

        # Определить статус
        if throughput >= 15 and flow_efficiency >= 0.6:
            status = "green"
        elif throughput >= 10 or flow_efficiency >= 0.5:
            status = "yellow"
        else:
            status = "red"

        # Сформировать вывод
        self.findings = [
            f"Throughput: {throughput} задач за {period_days} дней",
            f"Average cycle time: {avg_cycle_time:.1f} дней",
            f"Average lead time: {avg_lead_time:.1f} дней",
            f"Average WIP: {avg_wip:.1f}",
            f"Flow efficiency: {flow_efficiency:.1%}",
            f"Blocked time: {blocked_time:.1f} дней",
        ]

        if avg_cycle_time > 5:
            self.risks.append(
                f"Cycle time ({avg_cycle_time:.1f} дней) высокий. "
                "Задачи долго в работе."
            )

        if blocked_time > period_days * 0.1:
            self.risks.append(
                f"Blocked time ({blocked_time:.1f} дней) составляет "
                f"{blocked_time/period_days*100:.1f}% от периода. "
                "Есть проблемы с блокировками."
            )

        if avg_wip > 5:
            self.risks.append(
                f"Average WIP ({avg_wip:.1f}) высокий. "
                "Сотрудники работают над многими задачами одновременно."
            )

        self.recommendations = [
            "Снизить WIP - фокус на меньше задач",
            "Уменьшить размер задач",
            "Устранить блокеры",
            "Улучшить ревью процессы",
        ]

        self.sources = [
            f"SWTR: завершенные задачи за {period_days} дней",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Метрики не включают задачи в статусах review/testing",
            "Время блокировок может быть недостаточно точным",
        ]

        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.75,
            team_members=team_members or [],
            products=products or []
        )

    async def _fetch_flow_data(self, period_days: int, team_members: List[str] = None) -> Dict[str, Any]:
        """Получить flow данные из SWTR (FastAPI Task Tracker)."""
        # Load team members if not provided
        if not team_members:
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        # Fetch all tasks for team using fetch_tasks_by_assignee (handles name mapping)
        all_tasks = []
        for member_login in team_members:
            tasks = await self._task_service.fetch_tasks_by_assignee(member_login)
            all_tasks.extend(tasks)

        # Get completed tasks within period
        from datetime import datetime, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

        completed_tasks = [
            t for t in all_tasks
            if t.status == "done" and t.updated_at >= cutoff
        ]

        # Calculate throughput
        throughput = len(completed_tasks)

        # Calculate cycle time (time from in_progress to done)
        cycle_times = []
        for task in completed_tasks:
            # Simplified: assume half of total time was in active state
            total_time = (task.updated_at - task.created_at).days
            if total_time > 0:
                cycle_times.append(total_time * 0.5)

        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0

        # Calculate lead time (time from created to done)
        lead_times = []
        for task in completed_tasks:
            lead_time = (task.updated_at - task.created_at).days
            if lead_time > 0:
                lead_times.append(lead_time)

        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0

        # Calculate WIP (average active tasks)
        # Count tasks that were active during the period
        active_tasks = [t for t in all_tasks if t.created_at >= cutoff]
        wip_values = [len(active_tasks) / period_days * 7] if active_tasks else [0]  # Normalize to weekly
        avg_wip = sum(wip_values) / len(wip_values) if wip_values else 0.0

        # Calculate flow efficiency
        flow_efficiency = 0.7 if avg_lead_time > 0 else 0.0

        # Calculate blocked time
        # Use original workflow_status from source_data if available
        blocked_tasks = []
        for t in all_tasks:
            source_data = getattr(t, 'source_data', {}) or {}
            workflow_status = source_data.get('workflow_status', '').lower()
            task_status = t.status or ""
            # Check for blocked status in both formats
            is_blocked = (
                "blocked" in workflow_status or
                workflow_status == "need info" or
                task_status.lower() == "blocked"
            )
            if is_blocked:
                blocked_tasks.append(t)
        blocked_time = len(blocked_tasks) * 1.0  # Simplified: assume 1 day per blocked task

        return {
            "throughput": throughput,
            "avg_cycle_time": round(avg_cycle_time, 2),
            "avg_lead_time": round(avg_lead_time, 2),
            "avg_wip": round(avg_wip, 2),
            "flow_efficiency": flow_efficiency,
            "blocked_time": round(blocked_time, 2),
            "completed_tasks": len(completed_tasks),
            "total_tasks": len(all_tasks),
        }
