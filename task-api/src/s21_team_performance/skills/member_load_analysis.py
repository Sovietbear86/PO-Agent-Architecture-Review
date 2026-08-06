"""Скилл: Member Load Analysis - Анализ загрузки конкретного сотрудника в спринте."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members, get_member_full_name


class MemberLoadAnalysisSkill:
    """Анализирует загрузку конкретного сотрудника внутри спринта с оценкой трудоемкости.
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
        """Анализировать загрузку сотрудников в спринте"""

        # Extract sprint_id from team_members if not provided directly
        # Check if any member login contains sprint info or if sprint_id needs to be extracted from context
        if not sprint_id:
            # Try to extract sprint_id from team_members if any contain sprint pattern
            if team_members:
                for member in team_members:
                    member_lower = member.lower()
                    sprint_match = re.search(r'(dms|olp|wmb|sts)-sprnt-\d+', member_lower)
                    if sprint_match:
                        sprint_id = sprint_match.group(0).upper()
                        break
        
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
        sprint_tasks = await self._fetch_sprint_tasks(sprint_id, team_members)

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

        # Сгруппировать задачи по сотруднику
        member_tasks: Dict[str, List] = {}
        for task in sprint_tasks:
            task_assignee = task.assignee or ""
            for member_login in team_members:
                member_short_name = get_member_full_name(member_login).split()[-1]
                if member_short_name.lower() in task_assignee.lower():
                    if member_login not in member_tasks:
                        member_tasks[member_login] = []
                    member_tasks[member_login].append(task)
                    break

        # Если не нашли по short_name, попробовать по login
        if not member_tasks:
            for task in sprint_tasks:
                source_data = getattr(task, 'source_data', {}) or {}
                responsible = source_data.get('responsible', {})
                if isinstance(responsible, dict):
                    responsible_login = responsible.get('login', '')
                elif isinstance(responsible, str):
                    responsible_login = responsible
                else:
                    responsible_login = ''
                
                for member_login in team_members:
                    if member_login.lower() in responsible_login.lower() or responsible_login.lower() in member_login.lower():
                        if member_login not in member_tasks:
                            member_tasks[member_login] = []
                        member_tasks[member_login].append(task)
                        break

        # Если еще не нашли, использовать все задачи спринта
        if not member_tasks:
            member_tasks = {"all": sprint_tasks}

        # Вычислить метрики для каждого сотрудника
        member_metrics = []
        for member_login, tasks in member_tasks.items():
            full_name = get_member_full_name(member_login)
            
            # Рассчитать трудоемкость
            total_effort = sum(self._task_service._estimate_effort(t) for t in tasks)
            
            # Подсчет по статусам
            todo_tasks = [t for t in tasks if t.status == "todo"]
            in_progress_tasks = [t for t in tasks if t.status == "in_progress"]
            done_tasks = [t for t in tasks if t.status == "done"]
            
            todo_effort = sum(self._task_service._estimate_effort(t) for t in todo_tasks)
            in_progress_effort = sum(self._task_service._estimate_effort(t) for t in in_progress_tasks)
            done_effort = sum(self._task_service._estimate_effort(t) for t in done_tasks)
            
            # Расчет средней трудоемкости задач
            avg_effort = total_effort / len(tasks) if tasks else 0
            
            # Оценка загруженности
            workload_score = self._calculate_workload_score(tasks, total_effort)
            
            member_metrics.append({
                "login": member_login,
                "full_name": full_name,
                "total_tasks": len(tasks),
                "total_effort": round(total_effort, 2),
                "avg_effort_per_task": round(avg_effort, 2),
                "todo": len(todo_tasks),
                "todo_effort": round(todo_effort, 2),
                "in_progress": len(in_progress_tasks),
                "in_progress_effort": round(in_progress_effort, 2),
                "done": len(done_tasks),
                "done_effort": round(done_effort, 2),
                "workload_score": workload_score,
                "tasks": tasks
            })

        # Определить статус (средний по всем сотрудникам)
        avg_workload = sum(m.get('workload_score', 0) for m in member_metrics) / len(member_metrics) if member_metrics else 0
        
        if avg_workload >= 0.8:
            status = "red"
        elif avg_workload >= 0.5:
            status = "yellow"
        else:
            status = "green"

        # Сформировать вывод
        total_tasks = sum(m.get('total_tasks', 0) for m in member_metrics)
        total_effort = sum(m.get('total_effort', 0) for m in member_metrics)
        total_done = sum(m.get('done', 0) for m in member_metrics)
        
        self.findings = [
            f"Спринт: {sprint_id}",
            f"Всего задач: {total_tasks}",
            f"Общая трудоемкость: {total_effort:.1f} story points",
            f"Выполнено: {total_done} задач ({total_done/total_tasks*100:.1f}%)" if total_tasks > 0 else "Выполнено: 0 задач",
            f"Средняя трудоемкость задачи: {total_effort/total_tasks:.1f} sp" if total_tasks > 0 else "Нет задач",
        ]

        # Детальный анализ по каждому сотруднику
        for member in member_metrics:
            full_name = member.get('full_name', 'N/A')
            total = member.get('total_tasks', 0)
            effort = member.get('total_effort', 0)
            avg = member.get('avg_effort_per_task', 0)
            todo = member.get('todo', 0)
            in_progress = member.get('in_progress', 0)
            done = member.get('done', 0)
            workload = member.get('workload_score', 0)
            
            self.findings.append(
                f"- {full_name}: {total} задач ({effort:.1f} sp), средняя трудоемкость: {avg:.1f} sp, "
                f"В работе: {in_progress}, Выполнено: {done}, Загруженность: {workload*100:.0f}%"
            )

        # Риски
        for member in member_metrics:
            full_name = member.get('full_name', 'N/A')
            workload = member.get('workload_score', 0)
            todo_effort = member.get('todo_effort', 0)
            in_progress_effort = member.get('in_progress_effort', 0)
            done_effort = member.get('done_effort', 0)
            
            # Высокая загруженность
            if workload >= 0.8:
                self.risks.append(
                    f"{full_name}: высокая загруженность ({workload*100:.0f}%). "
                    "Риск перегрузки и невыполнения задач."
                )
            
            # Больше задач в работе чем выполнено
            if in_progress + todo > done * 2:
                self.risks.append(
                    f"{full_name}: много задач в работе ({in_progress + todo}) против {done} выполненных. "
                    "Риск несвоевременного завершения."
                )
            
            # Высокая средняя трудоемкость задач
            if avg > 5.0:
                self.risks.append(
                    f"{full_name}: высокая средняя трудоемкость задач ({avg:.1f} sp). "
                    "Риск недооценки или сложных задач."
                )

        self.recommendations = [
            "Распределить задачи между сотрудниками более равномерно",
            "Уменьшить WIP лимиты для сотрудников с высокой загруженностью",
            "Приоритизировать выполнение задач с высокой трудоемкостью",
            "Рассмотреть возможность назначения дополнительных ресурсов",
        ]

        self.sources = [
            f"SWTR: задачи спринта {sprint_id}",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Не учитывается сложность задач (используется эвристическая оценка)",
            "Трудоемкость основана на estimate_hours и story_points",
        ]

        # If specific members requested, return only their tasks; otherwise return all sprint tasks
        import logging
        logger = logging.getLogger(__name__)

        if team_members and len(team_members) == 1:
            # Single member query - return only that member's tasks
            member_key = team_members[0]
            member_tasks_list = member_tasks.get(member_key, [])
            logger.info(f"[member_load_analysis] member_key={member_key}, tasks_count={len(member_tasks_list)}")
            tasks_list = [{"id": str(t.id), "source_id": t.source_id, "title": t.title, "status": t.status} for t in member_tasks_list]
        else:
            # Multiple members or all members - return all sprint tasks
            tasks_list = [{"id": str(t.id), "source_id": t.source_id, "title": t.title, "status": t.status} for tasks in member_tasks.values() for t in tasks]

        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.8,
            team_members=team_members,
            products=[],
            sprint_id=sprint_id,
            tasks=tasks_list
        )

    async def _fetch_sprint_tasks(self, sprint_id: str, team_members: List[str]) -> List[Any]:
        """Получить все задачи спринта."""
        from app.repositories.task_repository import TaskRepository
        
        repository = TaskRepository()
        all_tasks = repository.find_all(limit=10000)
        
        # Filter by sprint_id
        sprint_tasks = [t for t in all_tasks if t.source_data.get("sprint_id") == sprint_id]
        
        return sprint_tasks

    def _calculate_workload_score(self, tasks: List[Any], total_effort: float) -> float:
        """Рассчитать индекс загруженности (0-1)."""
        if not tasks:
            return 0.0
        
        # Факторы:
        # 1. Всего задач (влияние: 0.3)
        task_count_factor = min(len(tasks) / 10.0, 1.0) * 0.3
        
        # 2. Общая трудоемкость (влияние: 0.4)
        effort_factor = min(total_effort / 40.0, 1.0) * 0.4
        
        # 3. Доля задач в работе (влияние: 0.3)
        in_progress = len([t for t in tasks if t.status == "in_progress"])
        wip_factor = (in_progress / len(tasks)) * 0.3 if tasks else 0
        
        return task_count_factor + effort_factor + wip_factor
