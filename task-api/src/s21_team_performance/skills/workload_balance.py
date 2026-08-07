"""Скилл: Workload Balance - Анализ загрузки команды с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any

from s21_team_performance.models import AnalysisResult
from s21_team_performance.services.task_service import TaskService, load_team_members, get_member_full_name


class WorkloadBalanceSkill:
    """Анализирует распределение нагрузки между сотрудниками.
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
        products: List[str] = None,
        sprint_id: str = None
    ) -> AnalysisResult:
        """Анализировать распределение нагрузки"""

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
                products=products or []
            )

        # Получить данные о задачах каждого сотрудника из SWTR (filtered by sprint if specified)
        member_loads = await self._fetch_member_loads(team_members, period_days, sprint_id)

        if not member_loads:
            return AnalysisResult(
                status="yellow",
                findings=["Нет данных о задачах за период"],
                risks=["Нет завершенных или активных задач"],
                recommendations=["Проверить наличие задач у участников в SWTR"],
                sources=[],
                constraints=["Требуются задачи у участников"],
                confidence=0.4,
                team_members=team_members,
                products=products or []
            )

        # Вычислить метрики нагрузки
        total_tasks = sum(m.get('total_tasks', 0) for m in member_loads)
        avg_tasks = total_tasks / len(member_loads) if member_loads else 0

        max_tasks_member = max(member_loads, key=lambda x: x.get('total_tasks', 0)) if member_loads else None
        min_tasks_member = min(member_loads, key=lambda x: x.get('total_tasks', 0)) if member_loads else None

        # Определить дисбаланс
        if max_tasks_member and min_tasks_member and max_tasks_member.get('total_tasks', 0) > min_tasks_member.get('total_tasks', 0) * 2:
            imbalance = True
        else:
            imbalance = False

        # Определить статус
        if not imbalance and avg_tasks >= 3:
            status = "green"
        elif not imbalance:
            status = "yellow"
        else:
            status = "red"

        # Сформировать вывод
        self.findings = [
            f"Всего задач за период: {total_tasks}",
            f"Среднее количество задач на человека: {avg_tasks:.1f}",
            f"Максимум: {max_tasks_member.get('full_name', 'N/A')} ({max_tasks_member.get('total_tasks', 0)} задач)",
            f"Минимум: {min_tasks_member.get('full_name', 'N/A')} ({min_tasks_member.get('total_tasks', 0)} задач)",
        ]

        # Детальный анализ по каждому сотруднику
        for member in member_loads:
            login = member.get('login', 'N/A')
            full_name = member.get('full_name', 'N/A')
            tasks = member.get('total_tasks', 0)
            wip = member.get('wip', 0)
            completed = member.get('completed', 0)

            self.findings.append(
                f"- {full_name} ({login}): {tasks} задач (WIP: {wip}, завершено: {completed})"
            )

            if wip > 5:
                self.risks.append(
                    f"{full_name} ({login}): высокий WIP ({wip}). Риск перегрузки."
                )

            if tasks < 2:
                self.risks.append(
                    f"{full_name} ({login}): мало задач ({tasks}). Возможен дефицит нагрузки."
                )

        if imbalance:
            ratio = max_tasks_member.get('total_tasks', 1) / max(min_tasks_member.get('total_tasks', 1), 1)
            self.risks.append(
                f"Значительный дисбаланс нагрузки. "
                f"Максимум в {ratio:.1f} раза больше минимума."
            )

        self.recommendations = [
            "Перераспределить задачи между участниками",
            "Проверить WIP лимиты каждого сотрудника",
            "Учесть внеспринтовую нагрузку при планировании",
            "Обратить внимание на сотрудника с низкой загрузкой",
        ]

        self.sources = [
            f"SWTR: задачи за {period_days} дней",
            "config/team_members.yaml",
        ]

        self.constraints = [
            "Не учитывается сложность задач",
            "Не учитывается внеспринтовая нагрузка (ревью, сопровождение)",
            "Количество задач не эквивалентно эффективности",
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
            products=products or []
        )

    async def _fetch_member_loads(self, members: List[str], period_days: int, sprint_id: str = None) -> List[Dict[str, Any]]:
        """Получить нагрузку по каждому сотруднику из SWTR (FastAPI Task Tracker).
        
        Args:
            members: List of member logins
            period_days: Number of days to look back
            sprint_id: Optional sprint ID to filter tasks by sprint
        """
        from s21_team_performance.services.task_service import get_member_short_name

        loads = []

        for login in members:
            # Fetch all tasks for the member (handles name mapping)
            all_tasks = await self._task_service.fetch_tasks_by_assignee(login)

            # Filter by sprint_id if specified
            if sprint_id:
                filtered_tasks = []
                for task in all_tasks:
                    source_data = getattr(task, 'source_data', {}) or {}
                    if source_data.get("sprint_id") == sprint_id:
                        filtered_tasks.append(task)
                tasks = filtered_tasks
            else:
                tasks = all_tasks

            # Filter by period_days if specified
            if period_days and period_days > 0:
                from datetime import datetime, timedelta, timezone
                cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)
                tasks = [
                    t for t in tasks
                    if t.created_at and t.created_at >= cutoff
                ]

            total_tasks = len(tasks)
            completed = len([t for t in tasks if t.status == "done"])
            wip = len([t for t in tasks if t.status == "in_progress"])
            blocked = len([t for t in tasks if t.status == "blocked"])
            on_hold = len([t for t in tasks if t.status == "on_hold"])

            # Get full name
            full_name = get_member_full_name(login)

            loads.append({
                "login": login,
                "full_name": full_name,
                "total_tasks": total_tasks,
                "completed": completed,
                "wip": wip,
                "blocked": blocked,
                "on_hold": on_hold,
            })

        return loads
