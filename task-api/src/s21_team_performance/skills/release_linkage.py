"""Скилл: Release Linkage - Анализ связи с релизом с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members


class ReleaseLinkageSkill:
    """Проверяет состав релиза, прогресс, критический путь и соответствие прогноза дате.
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
        release_id: str,
        team_members: List[str] = None,
        products: List[str] = None,
        period_days: int = 60
    ) -> AnalysisResult:
        """Анализировать связь с релизом"""

        # Получить данные о релизе из SWTR
        release_data = await self._fetch_release_data(release_id, team_members, period_days)

        if not release_data.get('features'):
            return AnalysisResult(
                status="yellow",
                findings=["Нет данных о релизе"],
                risks=["Нет задач, привязанных к релизу"],
                recommendations=["Проверить привязку задач к релизу в SWTR"],
                sources=[],
                constraints=["Требуются данные о релизе"],
                confidence=0.3,
                team_members=team_members or [],
                products=products or []
            )

        # Анализировать состав релиза
        features = release_data.get('features', [])
        planned_features = len([f for f in features if f.get('status') == 'planned'])
        in_progress_features = len([f for f in features if f.get('status') == 'in_progress'])
        done_features = len([f for f in features if f.get('status') == 'done'])
        critical_tasks = [f for f in features if f.get('is_critical', False)]

        progress = done_features / len(features) if features else 0

        # Проверить критический путь
        critical_path_tasks = [f for f in critical_tasks if f.get('status') != 'done']

        # Определить статус
        if progress >= 0.9:
            status = "green"
        elif progress >= 0.7:
            status = "yellow"
        else:
            status = "red"

        # Сформировать вывод
        self.findings = [
            f"Релиз: {release_id}",
            f"Всего задач: {len(features)}",
            f"Запланировано: {planned_features}",
            f"В работе: {in_progress_features}",
            f"Завершено: {done_features}",
            f"Прогресс: {progress:.1%}",
        ]

        if critical_path_tasks:
            task_ids = [t.get('id', 'N/A') for t in critical_path_tasks[:3]]
            self.findings.append(
                f"Критические задачи: {len(critical_path_tasks)} ({', '.join(task_ids) if task_ids else 'N/A'})"
            )

        # Риски
        if critical_path_tasks:
            task_ids = [t.get('id', 'N/A') for t in critical_path_tasks[:3]]
            self.risks.append(
                f"{len(critical_path_tasks)} критических задач еще не завершены. "
                f"({', '.join(task_ids) if task_ids else 'N/A'}) "
                "Риск задержки релиза."
            )

        if progress < 0.5:
            self.risks.append(
                f"Прогресс релиза ({progress:.1%}) ниже 50%. "
                "Риск невыхода по срокам."
            )

        if len(critical_tasks) == 1:
            self.risks.append(
                f"Релиз зависит от одного критического элемента ({critical_tasks[0].get('id', 'N/A')}). "
                "Bus factor = 1."
            )

        # Рекомендации
        self.recommendations = []

        if critical_path_tasks:
            task_ids = [t.get('id', 'N/A') for t in critical_path_tasks[:2]]
            self.recommendations.append(
                f"Фокус на критические задачи: {', '.join(task_ids) if task_ids else 'N/A'}"
            )

        if progress < 0.5:
            self.recommendations.append(
                "Рассмотреть пересмотр объема релиза или сроки"
            )

        self.recommendations.append(
            "Учитывать переносы и carryover в прогнозе"
        )

        self.sources = [
            f"SWTR: релиз {release_id}",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Статусы задач могут быть не актуальны",
            "Критичность задач может быть оценена субъективно",
        ]

        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.7,
            team_members=team_members or [],
            products=products or []
        )

    async def _fetch_release_data(
        self,
        release_id: str,
        team_members: List[str] = None,
        period_days: int = 60
    ) -> Dict[str, Any]:
        """Получить данные о релизе из SWTR (FastAPI Task Tracker)."""
        # Load team members if not provided
        if not team_members:
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        # Fetch all tasks for team
        all_tasks = []
        for member_login in team_members:
            tasks = self._task_service.adapter.search_tasks(release_id, {"assignee": member_login})
            all_tasks.extend(tasks)

        # If no tasks found, try fetching all tasks and filter by title
        if not all_tasks:
            for member_login in team_members:
                tasks = self._task_service.adapter.search_tasks("", {"assignee": member_login})
                all_tasks.extend([t for t in tasks if release_id.lower() in t.title.lower()])

        # Map to release features
        features = []
        for task in all_tasks:
            features.append({
                "id": task.source_id or task.id,
                "name": task.title,
                "status": task.status,
                "is_critical": self._task_service._is_critical_task(task),
                "deadline": task.deadline.isoformat() if task.deadline else None,
            })

        # Extract release date
        planned_date = self._task_service._extract_release_date(all_tasks)

        return {
            "release_id": release_id,
            "planned_date": planned_date,
            "features": features,
        }
