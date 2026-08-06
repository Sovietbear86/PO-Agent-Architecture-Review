"""Скилл: Risk Analysis - Анализ рисков невыполнения задач."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members, get_member_full_name, get_member_short_name


class RiskAnalysisSkill:
    """Анализирует риски невыполнения задач сотрудников в спринте.
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
        sprint_id: str = None,
        team_members: List[str] = None,
        products: List[str] = None
    ) -> AnalysisResult:
        """Анализировать риски невыполнения задач"""
        
        if not sprint_id:
            return AnalysisResult(
                status="yellow",
                findings=["Не указан спринт"],
                risks=["Укажите ID спринта в запросе (например, OLP-SPRNT-5)"],
                recommendations=["Указать sprint_id в параметрах запроса"],
                sources=[],
                constraints=["Требуется указать sprint_id"],
                confidence=0.3,
                team_members=[],
                products=[]
            )

        if not team_members:
            # Load from config
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        if not team_members:
            return AnalysisResult(
                status="yellow",
                findings=["Не указаны участники команды"],
                risks=["Нет данных о сотрудниках для анализа"],
                recommendations=["Указать team_members в запросе или проверить config/team_members.yaml"],
                sources=[],
                constraints=["Требуется список участников команды"],
                confidence=0.3,
                team_members=[],
                products=[]
            )

        # Получить задачи спринта
        sprint_tasks = await self._fetch_sprint_tasks(sprint_id)

        if not sprint_tasks:
            return AnalysisResult(
                status="yellow",
                findings=[f"Нет задач в спринте {sprint_id}"],
                risks=["Проверьте, что спринт существует и у сотрудников есть задачи"],
                recommendations=["Проверить спринт в SWTR или синхронизировать задачи"],
                sources=[],
                constraints=[f"Спринт {sprint_id} не содержит задач"],
                confidence=0.4,
                team_members=team_members,
                products=[]
            )

        # Группировка задач по сотруднику - используем правильную фильтрацию через get_member_short_name
        member_tasks: Dict[str, List] = {}

        # For single member, directly filter using get_member_short_name
        if len(team_members) == 1:
            member_login = team_members[0]
            short_name = get_member_short_name(member_login)
            member_tasks[member_login] = []

            for task in sprint_tasks:
                task_assignee = task.assignee or ""
                # Check if task is assigned to this member
                if short_name and task_assignee.lower() == short_name.lower():
                    member_tasks[member_login].append(task)
                    continue

                # Also check responsible in source_data
                source_data = getattr(task, 'source_data', {}) or {}
                responsible = source_data.get('responsible', {})
                responsible_login = ''
                if isinstance(responsible, dict):
                    responsible_login = responsible.get('login', '')
                elif isinstance(responsible, str):
                    responsible_login = responsible

                if responsible_login.lower() == member_login.lower():
                    member_tasks[member_login].append(task)
        else:
            # Multiple members - filter each one
            for task in sprint_tasks:
                task_assignee = task.assignee or ""

                for member_login in team_members:
                    short_name = get_member_short_name(member_login)

                    # Check if task is assigned to this member
                    if short_name and task_assignee.lower() == short_name.lower():
                        if member_login not in member_tasks:
                            member_tasks[member_login] = []
                        member_tasks[member_login].append(task)
                        continue

                    # Also check responsible in source_data
                    source_data = getattr(task, 'source_data', {}) or {}
                    responsible = source_data.get('responsible', {})
                    responsible_login = ''
                    if isinstance(responsible, dict):
                        responsible_login = responsible.get('login', '')
                    elif isinstance(responsible, str):
                        responsible_login = responsible

                    if responsible_login.lower() == member_login.lower():
                        if member_login not in member_tasks:
                            member_tasks[member_login] = []
                        member_tasks[member_login].append(task)

        # Если еще не нашли, использовать все задачи спринта
        if not member_tasks:
            member_tasks = {"all": sprint_tasks}

        # Анализ рисков для каждого сотрудника
        high_risk_tasks = []
        medium_risk_tasks = []
        member_risk_scores = {}

        for member_login, tasks in member_tasks.items():
            full_name = get_member_full_name(member_login)
            
            # Расчет метрик
            total_effort = sum(self._task_service._estimate_effort(t) for t in tasks)
            done_effort = sum(self._task_service._estimate_effort(t) for t in tasks if t.status == "done")
            remaining_effort = total_effort - done_effort
            
            # Рассчитать прогресс
            progress = done_effort / total_effort if total_effort > 0 else 0
            
            # Проверить задачи на риски
            member_high_risk = []
            member_medium_risk = []
            
            for task in tasks:
                task_risk = self._assess_task_risk(task, sprint_id)
                if task_risk == "high":
                    member_high_risk.append(task)
                elif task_risk == "medium":
                    member_medium_risk.append(task)
            
            # Оценка общего риска сотрудника
            if len(member_high_risk) > 0:
                risk_score = 1.0
            elif len(member_medium_risk) > 0:
                risk_score = 0.7
            elif progress < 0.3 and total_effort > 10:
                risk_score = 0.8
            elif progress < 0.5 and total_effort > 20:
                risk_score = 0.6
            else:
                risk_score = 0.3
            
            member_risk_scores[member_login] = {
                "full_name": full_name,
                "risk_score": risk_score,
                "high_risk_count": len(member_high_risk),
                "medium_risk_count": len(member_medium_risk),
                "progress": progress,
                "remaining_effort": remaining_effort,
                "high_risk_tasks": member_high_risk,
                "medium_risk_tasks": member_medium_risk
            }
            
            high_risk_tasks.extend(member_high_risk)
            medium_risk_tasks.extend(member_medium_risk)

        # Определить статус на основе среднего риска
        avg_risk = sum(m.get('risk_score', 0) for m in member_risk_scores.values()) / len(member_risk_scores) if member_risk_scores else 0
        
        if avg_risk >= 0.7:
            status = "red"
        elif avg_risk >= 0.4:
            status = "yellow"
        else:
            status = "green"

        # Сформировать вывод
        self.findings = [
            f"Спринт: {sprint_id}",
            f"Высокорисковых задач: {len(high_risk_tasks)}",
            f"Задач со средним риском: {len(medium_risk_tasks)}",
        ]

        # Детальный анализ по каждому сотруднику
        for member_login, metrics in sorted(member_risk_scores.items(), key=lambda x: -x[1]['risk_score']):
            full_name = metrics.get('full_name', 'N/A')
            risk_score = metrics.get('risk_score', 0)
            high_count = metrics.get('high_risk_count', 0)
            medium_count = metrics.get('medium_risk_count', 0)
            progress = metrics.get('progress', 0)
            remaining_effort = metrics.get('remaining_effort', 0)
            
            risk_label = "КРИТИЧЕСКИЙ" if risk_score >= 0.8 else ("ВЫСОКИЙ" if risk_score >= 0.6 else ("СРЕДНИЙ" if risk_score >= 0.4 else "НИЗКИЙ"))
            
            self.findings.append(
                f"- {full_name}: риск {risk_label} ({risk_score*100:.0f}%), прогресс {progress*100:.0f}%, осталось {remaining_effort:.1f} sp, "
                f"высокий риск: {high_count}, средний риск: {medium_count}"
            )

        # Основные риски
        high_risk_members = [(m, metrics) for m, metrics in member_risk_scores.items() if metrics.get('risk_score', 0) >= 0.7]
        
        for member_login, metrics in high_risk_members:
            full_name = metrics.get('full_name', 'N/A')
            high_risk_count = metrics.get('high_risk_count', 0)
            progress = metrics.get('progress', 0)
            remaining_effort = metrics.get('remaining_effort', 0)
            
            self.risks.append(
                f"{full_name}: {high_risk_count} задач с высоким риском невыполнения. "
                f"Прогресс: {progress*100:.0f}%, осталось: {remaining_effort:.1f} sp."
            )
            
            # Список конкретных задач
            if high_risk_count > 0:
                task_titles = [t.title for t in metrics.get('high_risk_tasks', [])[:3]]
                self.risks.append(f"  Под риском: {', '.join(task_titles)}")

        # Рекомендации
        self.recommendations = [
            "Приоритизировать выполнение высокорисковых задач",
            "Назначить дополнительные ресурсы для сотрудников с высоким риском",
            "Уменьшить WIP лимиты и сконцентрироваться на завершении",
            "Провести синхронизацию с PO для пересмотра приоритетов",
            "Рассмотреть возможность перераспределения задач между сотрудниками",
        ]
        
        if len(high_risk_tasks) > 3:
            self.recommendations.append(
                "Требуется срочное вмешательство - больше 3 задач под риском"
            )

        self.sources = [
            f"SWTR: задачи спринта {sprint_id}",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Оценка риска основана на статусе задач и трудоемкости",
            "Не учитывается внешние блокеры (ожидание ревью, зависимостей)",
        ]

        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.75,
            team_members=team_members,
            products=[],
            sprint_id=sprint_id,
            tasks=[{"id": str(t.id), "source_id": t.source_id, "title": t.title, "status": t.status} for tasks in member_tasks.values() for t in tasks]
        )

    async def _fetch_sprint_tasks(self, sprint_id: str) -> List[Any]:
        """Получить все задачи спринта."""
        from app.repositories.task_repository import TaskRepository

        repository = TaskRepository()
        all_tasks = repository.find_all(limit=10000)

        # Filter by sprint_id
        sprint_tasks = [t for t in all_tasks if t.source_data.get("sprint_id") == sprint_id]

        return sprint_tasks

    def _assess_task_risk(self, task: Any, sprint_id: str) -> str:
        """Оценить риск задачи: high, medium, low."""
        source_data = getattr(task, 'source_data', {}) or {}
        effort = self._task_service._estimate_effort(task)
        
        # Проверить статус
        if task.status == "done":
            return "low"
        
        # Проверить оценку
        if effort > 20:
            return "high"
        elif effort > 10:
            return "medium"
        
        # Проверить наличие дедлайна
        deadline = source_data.get('due_date') or source_data.get('deadline')
        if deadline:
            try:
                deadline_dt = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                now = datetime.now(deadline_dt.tzinfo) if deadline_dt.tzinfo else datetime.now()
                days_remaining = (deadline_dt - now).days
                if days_remaining < 3:
                    return "high"
                elif days_remaining < 7:
                    return "medium"
            except:
                pass
        
        # Проверить наличие блокеров
        if task.status == "blocked" or task.status == "on_hold":
            return "high"
        
        # Проверить WIP задачи (много задач в работе)
        if task.status == "in_progress":
            return "medium"
        
        # Проверить todo задачи с высокой трудоемкостью
        if task.status == "todo" and effort > 15:
            return "high"
        
        return "low"
