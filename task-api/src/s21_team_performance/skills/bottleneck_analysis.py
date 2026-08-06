"""Скилл: Bottleneck Analysis - Анализ узких мест с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members


class BottleneckAnalysisSkill:
    """Ищет узкие места в процессе: ожидание ревью, очередь тестирования и т.д.
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
        """Анализировать узкие места"""

        # Получить данные из SWTR
        bottleneck_data = await self._fetch_bottleneck_data(period_days, team_members)

        if not bottleneck_data.get('tasks'):
            return AnalysisResult(
                status="yellow",
                findings=["Недостаточно данных для анализа"],
                risks=["Нет задач для анализа"],
                recommendations=["Проверить наличие задач за период в SWTR"],
                sources=[],
                constraints=["Требуются задачи для анализа"],
                confidence=0.4,
                team_members=team_members or [],
                products=products or []
            )

        # Анализировать узкие места
        review_queue = bottleneck_data.get('review_queue', [])
        testing_queue = bottleneck_data.get('testing_queue', [])
        blocked_tasks = bottleneck_data.get('blocked_tasks', [])
        waiting_architecture = bottleneck_data.get('waiting_architecture', [])
        waiting_expert = bottleneck_data.get('waiting_expert', [])

        # Сформировать вывод
        self.findings = [
            f"Всего проанализировано задач: {bottleneck_data.get('tasks', 0)}",
            f"Задач в очереди на ревью: {len(review_queue)}",
            f"Задач в очереди на тестирование: {len(testing_queue)}",
            f"Заблокированных задач: {len(blocked_tasks)}",
            f"Ожидают архитектурных согласований: {len(waiting_architecture)}",
            f"Ожидают эксперта (bus factor 1): {len(waiting_expert)}",
        ]

        # Риски
        if len(review_queue) > 5:
            self.risks.append(
                f"Большая очередь на ревью ({len(review_queue)} задач). "
                "Риск задержек в выпуске."
            )

        if len(testing_queue) > 3:
            self.risks.append(
                f"Большая очередь на тестирование ({len(testing_queue)} задач). "
                "Тестирование может быть узким местом."
            )

        if len(waiting_architecture) > 2:
            self.risks.append(
                f"Множество задач ждут архитектурных согласований ({len(waiting_architecture)}). "
                "Архитектор может быть узким местом."
            )

        if len(waiting_expert) > 0:
            self.risks.append(
                f"{len(waiting_expert)} задач ждут конкретного эксперта. "
                "Высокий bus factor risk."
            )

        # Рекомендации
        self.recommendations = []

        if review_queue:
            task_ids = [t['id'] for t in review_queue[:3]]
            self.recommendations.append(
                f"Распределить ревью задач: {', '.join(task_ids) if task_ids else 'Нет задач'}"
            )

        if waiting_architecture:
            self.recommendations.append(
                "Ускорить процесс архитектурных согласований"
            )

        if waiting_expert:
            self.recommendations.append(
                "Рассмотреть создание backup по направлению эксперта"
            )

        self.recommendations.append(
            "Провести эксперимент: ограничить WIP для узких мест"
        )

        self.sources = [
            f"SWTR: задачи за {period_days} дней",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Автоматическое определение стадий может быть неточным",
            "Не учитываются внешние зависимости",
        ]

        return AnalysisResult(
            status="yellow" if self.risks else "green",
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.7,
            team_members=team_members or [],
            products=products or []
        )

    async def _fetch_bottleneck_data(self, period_days: int, team_members: List[str] = None) -> Dict[str, Any]:
        """Получить данные об узких местах из SWTR (FastAPI Task Tracker)."""
        # Load team members if not provided
        if not team_members:
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        # Fetch all tasks for team using fetch_tasks_by_assignee (handles name mapping)
        all_tasks = []
        for member_login in team_members:
            tasks = await self._task_service.fetch_tasks_by_assignee(member_login)
            all_tasks.extend(tasks)

        # Categorize tasks by bottleneck indicators
        review_queue = []
        testing_queue = []
        blocked_tasks = []
        waiting_architecture = []
        waiting_expert = []

        for task in all_tasks:
            title_lower = task.title.lower()
            desc_lower = task.description.lower()

            # Get original workflow status from source_data if available
            source_data = getattr(task, 'source_data', {}) or {}
            workflow_status = source_data.get('workflow_status', '').lower()
            
            # Review queue indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["review", "peer review", "code review"]):
                if workflow_status == "in progress" or workflow_status == "ready for review":
                    review_queue.append({
                        "id": task.source_id or task.id,
                        "title": task.title,
                        "status": workflow_status or task.status,
                    })

            # Testing queue indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["test", "qa", "testing"]):
                if workflow_status == "in progress" or workflow_status == "ready for qa":
                    testing_queue.append({
                        "id": task.source_id or task.id,
                        "title": task.title,
                        "status": workflow_status or task.status,
                    })

            # Blocked tasks (Need info or blocked status)
            if workflow_status == "need info" or workflow_status == "blocked":
                blocked_tasks.append({
                    "id": task.source_id or task.id,
                    "title": task.title,
                    "status": workflow_status or task.status,
                })

            # Architecture indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["arch", "architecture", "design"]):
                if workflow_status == "in progress":
                    waiting_architecture.append({
                        "id": task.source_id or task.id,
                        "title": task.title,
                        "status": workflow_status or task.status,
                    })

            # Expert-dependent tasks
            if any(kw in title_lower or kw in desc_lower for kw in ["expert", "bus factor", "key person"]):
                waiting_expert.append({
                    "id": task.source_id or task.id,
                    "title": task.title,
                    "status": workflow_status or task.status,
                })

        return {
            "tasks": len(all_tasks),
            "review_queue": review_queue[:20],
            "testing_queue": testing_queue[:20],
            "blocked_tasks": blocked_tasks[:20],
            "waiting_architecture": waiting_architecture[:20],
            "waiting_expert": waiting_expert[:20],
        }
