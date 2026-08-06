"""Скилл: Velocity Analysis - Анализ velocity команды с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members


class VelocityAnalysisSkill:
    """Анализирует velocity команды, объясняет изменения.
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
        period_sprints: int = 6,
        team_members: List[str] = None,
        products: List[str] = None,
        period_days: int = 90
    ) -> AnalysisResult:
        """Анализировать velocity"""

        # Получить историю velocity из SWTR
        velocity_history = await self._fetch_velocity_history(period_days, team_members)

        if not velocity_history:
            return AnalysisResult(
                status="yellow",
                findings=["Недостаточно данных для анализа"],
                risks=["Нет истории завершенных задач для расчета velocity"],
                recommendations=["Проверить наличие завершенных задач"],
                sources=[],
                constraints=["Необходимо минимум 2 точки данных для анализа"],
                confidence=0.5,
                team_members=team_members or [],
                products=products or []
            )

        # Вычислить среднюю velocity
        velocities = [v['completed_effort'] for v in velocity_history if v.get('completed_effort', 0) > 0]
        avg_velocity = sum(v for v in velocities) / len(velocities) if velocities else 0

        # Найти тренд
        if len(velocities) >= 2:
            first_half_avg = sum(velocities[:len(velocities)//2]) / (len(velocities)//2 or 1)
            second_half_avg = sum(velocities[len(velocities)//2:]) / (len(velocities) - len(velocities)//2 or 1)

            if second_half_avg > first_half_avg * 1.1:
                trend = "вверх"
                trend_change = "+"
            elif second_half_avg < first_half_avg * 0.9:
                trend = "вниз"
                trend_change = "-"
            else:
                trend = "стабильная"
                trend_change = "±"
        else:
            trend = "недостаточно данных"
            trend_change = "?"

        # Определить статус
        if trend == "стабильная" or trend == "вверх":
            status = "green"
        else:
            status = "yellow"

        # Сформировать вывод
        self.findings = [
            f"Средняя velocity за {period_days} дней: {avg_velocity:.1f} story points",
            f"Последний период: {velocities[-1] if velocities else 'N/A'} story points",
            f"Тренд: {trend} {trend_change}",
            f"Диапазон: {min(velocities):.1f} - {max(velocities):.1f} story points",
            f"Количество периодов: {len(velocities)}",
        ]

        # Объяснить изменения
        if trend == "вниз":
            self.risks = [
                "Velocity снизилась - проверить состав команды",
                "Возможны изменения в методике оценки",
                "Есть рост внеспринтовой нагрузки",
            ]
            self.recommendations = [
                "Проверить состав команды - были ли изменения?",
                "Уточнить методику оценки - не менялась ли?",
                "Учесть внеспринтовую нагрузку в планировании",
                "Изучить причины снижения продуктивности",
            ]
        elif trend == "вверх":
            self.findings.append("Velocity выросла - возможно за счет сверхусилий")
            self.risks = [
                "Высокая velocity может быть временной",
                "Проверить на наличие сверхусилий",
            ]
            self.recommendations = [
                "Уточнить у команды, не было ли сверхусилий",
                "Не полагаться на временный рост в прогнозах",
                "Рассмотреть возможность устойчивого роста продуктивности",
            ]
        else:
            self.recommendations = [
                "Velocity стабильна - это good baseline для прогнозов",
                "Продолжать мониторинг",
            ]

        self.sources = [
            f"SWTR: завершенные задачи за {period_days} дней",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Сравниваем только сопоставимые периоды",
            "Учитываем изменения в составе команды",
            "Не используем как персональный KPI",
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

    async def _fetch_velocity_history(self, period_days: int, team_members: List[str] = None) -> List[Dict[str, Any]]:
        """Получить историю velocity из SWTR (FastAPI Task Tracker)."""
        from s21_team_performance.services.task_service import get_member_short_name

        # Load team members if not provided
        if not team_members:
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        # Fetch all completed tasks for team using task_service
        all_completed = []
        for member_login in team_members:
            # Use task_service.fetch_tasks_by_assignee which handles name mapping
            tasks = await self._task_service.fetch_tasks_by_assignee(member_login, status_filter=["done"])
            all_completed.extend(tasks)

        if not all_completed:
            return []

        # Group by sprint_id (from task.source_data.sprint_id)
        from datetime import datetime, timedelta
        sprints: Dict[str, List] = {}

        for task in all_completed:
            # Try to get sprint_id from source_data
            source_data = getattr(task, 'source_data', {}) or {}
            sprint_id = source_data.get("sprint_id")
            
            # Fallback to week-based grouping if no sprint_id
            if not sprint_id:
                week_num = task.updated_at.isocalendar()[:2]
                sprint_id = f"W{week_num[0]}-{week_num[1]:02d}"

            if sprint_id not in sprints:
                sprints[sprint_id] = []
            sprints[sprint_id].append(task)

        # Calculate effort per sprint
        velocity_history = []
        for sprint_id, tasks in sorted(sprints.items(), reverse=True)[:period_days//7]:  # Last ~period_days days
            effort = sum(self._task_service._estimate_effort(t) for t in tasks)
            velocity_history.append({
                "sprint_id": sprint_id,
                "completed_effort": effort,
                "task_count": len(tasks),
            })

        return velocity_history
