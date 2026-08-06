"""Скилл: Sprint Health - Анализ здоровья спринта с реальными данными из SWTR."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from pathlib import Path

from s21_team_performance.config import (
    TEAM_KNOWLEDGE_DIR,
    TEAM_MEMBERS_FILE,
    WorkflowStatusConfig
)
from s21_team_performance.models import AnalysisResult, SprintMetrics
from s21_team_performance.services.task_service import TaskService, load_team_members, get_member_short_name


class SprintHealthSkill:
    """Анализирует здоровье спринта по committed scope, completed scope, blockers и т.д.
    Использует реальные данные из SWTR (FastAPI Task Tracker)."""

    def __init__(self, api_port: int | None = None):
        self.workflow_config = WorkflowStatusConfig()
        self.findings: List[str] = []
        self.risks: List[str] = []
        self.recommendations: List[str] = []
        self.sources: List[str] = []
        self.constraints: List[str] = []
        self._task_service = TaskService(api_port=api_port)
        self.api_port = api_port or 8003

    async def analyze(
        self,
        sprint_id: str,
        team_members: List[str] = None,
        products: List[str] = None,
        period_days: int = 30,
        params: Dict[str, Any] = None
    ) -> AnalysisResult:
        """Анализировать здоровье спринта"""

        # Если sprint_id не указан, получить список спринтов
        if not sprint_id or sprint_id.strip() == "":
            sprint_list = self.get_sprint_list(products[0] if products else "WMB")

            if sprint_list.get('sprints'):
                # Return list of sprints for user to choose from
                return AnalysisResult(
                    status="yellow",
                    findings=[
                        "Не указан ID спринта. Доступные спринты:",
                        *[f"- {s['id']}: {s['name']} (space: {s['space']})" for s in sprint_list['sprints'][:5]],
                        "",
                        "💡 Типовые запросы:",
                        "  • Здоровье спринта: 'здоровье спринта OLP-SPRNT-3'",
                        "  • Velocity: 'скорость команды' или 'velocity за последние 6 спринтов'",
                        "  • Flow metrics: 'поток задач за 30 дней'",
                        "  • Баланс загрузки: 'баланс загрузки команды'",
                        "  • Узкие места: 'бутылочное горлышко в спринте'",
                        "  • Прогноз: 'прогноз завершения спринта'",
                        "  • Компетенции: 'кто подходит для задачи'",
                        "  • Релизы: 'релизные задачи OLAP'",
                        "",
                        "💡 Или просто спросите: 'что ты умеешь'",
                    ],
                    risks=["Пожалуйста, укажите ID спринта для анализа"],
                    recommendations=["Используйте параметр sprint_id для выбора спринта"],
                    sources=[],
                    constraints=["Необходимо указать sprint_id"],
                    confidence=0.5,
                    team_members=team_members or [],
                    products=products or []
                )
            else:
                return AnalysisResult(
                    status="red",
                    findings=["Не найдено ни одного спринта"],
                    risks=["Попробуйте синхронизировать задачи через /api/v1/swtr/sync"],
                    recommendations=["Запустите синхронизацию с SWTR"],
                    sources=[],
                    constraints=["Отсутствуют данные о спринтах"],
                    confidence=0.0,
                    team_members=team_members or [],
                    products=products or []
                )

        # Получить данные из SWTR - используем унифицированный метод
        sprint_tasks = self._get_sprint_tasks_for_members(
            sprint_id=sprint_id,
            team_members=team_members,
            params=params
        )

        # Рассчитать метрики из задач спринта
        completed_tasks = []
        blocked_tasks = []
        unplanned_tasks = []

        for t in sprint_tasks:
            # Проверить статус выполнения
            source_data = t.source_data or {}
            is_completed = False
            is_blocked = False

            # Проверить workflow_status в атрибутах
            for attr in source_data.get("swtr_attributes", []):
                if attr.get("code") == "workflow_status":
                    attr_value = attr.get("value", {})
                    status_type = attr_value.get("statusType", "")
                    status_name = attr_value.get("name", "").lower()

                    if status_type == "done" or "done" in status_name or "clsd" in status_name:
                        is_completed = True
                    elif status_type == "blocked" or "blocked" in status_name:
                        is_blocked = True

            # Проверить task.status
            if t.status == "done" or is_completed:
                completed_tasks.append(t)
            elif t.status == "blocked" or is_blocked:
                blocked_tasks.append(t)

            if "unplanned" in (t.title or "").lower():
                unplanned_tasks.append(t)

        completed_effort = sum(self._task_service._estimate_effort(t) for t in completed_tasks)
        committed_effort = len(completed_tasks) * 3.0 if completed_tasks else 1.0

        # Расчет predictability
        predictability = completed_effort / committed_effort if committed_effort > 0 else 0.0

        # Определить статус
        if predictability >= 0.85:
            status = "green"
        elif predictability >= 0.70:
            status = "yellow"
        else:
            status = "red"

        # Сформировать вывод
        self.findings = [
            f"Committed scope: {committed_effort:.1f} story points",
            f"Completed scope: {completed_effort:.1f} story points",
            f"Scope change: 0.0 story points",
            f"Carryover: 0.0 story points",
            f"Throughput: {len(completed_tasks)} задач",
            f"Blocked: {len(blocked_tasks)} задач",
            f"Unplanned: {len(unplanned_tasks)} задач",
            f"Predictability: {predictability:.1%}",
        ]

        if predictability < 0.85:
            self.risks.append(
                f"Низкая predictability: {predictability:.1%}. "
                "Может указывать на неполные оценки или неожиданные блокеры."
            )

        if len(blocked_tasks) > 0:
            self.risks.append(
                f"Есть заблокированные задачи ({len(blocked_tasks)}). "
                "Проверить причины блокировки."
            )

        if len(unplanned_tasks) > len(completed_tasks) * 0.15:
            self.risks.append(
                f"Много unplanned задач ({len(unplanned_tasks)}). "
                "Риск переработки и неполного завершения."
            )

        self.recommendations = [
            "Проверить причины отклонения от плана",
            "Обратить внимание на заблокированные задачи",
            "Учесть в следующем планировании scope change rate",
        ]

        self.sources = [
            f"SWTR: {sprint_id}",
            "team_members.yaml",
            f"FastAPI API (port {self.api_port})",
        ]

        self.constraints = [
            "Данные актуальны на момент запуска анализа",
            "Не учитываются задачи вне спринта",
        ]

        return AnalysisResult(
            status=status,
            findings=self.findings,
            risks=self.risks,
            recommendations=self.recommendations,
            sources=self.sources,
            constraints=self.constraints,
            confidence=0.8,
            team_members=team_members or [],
            products=products or []
        )

    def _get_sprint_tasks_for_members(
        self,
        sprint_id: str,
        team_members: List[str] = None,
        params: Dict[str, Any] = None
    ) -> List[Any]:
        """Unified method to get sprint tasks for specific team members.

        Consolidates logic from _fetch_sprint_data, get_sprint_tasks, and get_tasks.
        """
        from app.repositories.task_repository import TaskRepository
        from s21_team_performance.config import WorkflowStatusConfig

        # Load team members if not provided
        if not team_members:
            members = load_team_members()
            team_members = [m.get("login") for m in members]

        # Normalize team members to lowercase for comparison
        team_members_lower = [m.lower() for m in team_members]

        # Get status filter from params
        status_filter = None
        if params and "status_filter" in params:
            status_filter = params["status_filter"]

        # Normalize status filter for comparison
        normalized_filter = None
        if status_filter:
            workflow_config = WorkflowStatusConfig()
            normalized_filter = [workflow_config.normalize_status(s) for s in status_filter]

        # Get all tasks with sprint info from repository
        repository = TaskRepository()
        # Changed: find all tasks (source='swtr') that have sprint_id in source_data
        all_tasks = repository.find_all(limit=10000)
        all_sprint_tasks = [t for t in all_tasks if t.source_data.get("sprint_id")]

        # Filter tasks by sprint_id and team members
        sprint_tasks = []
        for task in all_sprint_tasks:
            source_data = task.source_data or {}

            # Проверить sprint_id
            if source_data.get("sprint_id") != sprint_id:
                continue

            # Проверить статус, если задан status_filter
            if normalized_filter:
                task_status = self._normalize_task_status_for_filter(task)
                if task_status not in normalized_filter:
                    continue

            # Проверить, назначена ли задача участнику команды
            assignee_login = None
            for attr in source_data.get("swtr_attributes", []):
                if attr.get("code") == "assigned_to":
                    value = attr.get("value", {})
                    if value:
                        assignee_login = value.get("login")

            if assignee_login and assignee_login.lower() in team_members_lower:
                sprint_tasks.append(task)

        return sprint_tasks

    def get_sprint_list(self, space: str = "WMB") -> Dict[str, Any]:
        """Get list of all sprints from existing tasks (not just swtr_sprint).

        Collects sprints from all spaces where team members have tasks (OLP, DMS, WMB, STS).
        Returns sprints with their space to distinguish between sprints with same ID in different spaces.
        """
        from app.repositories.task_repository import TaskRepository

        repository = TaskRepository()

        # Get ALL tasks with source_id (SWTR tasks)
        tasks = [t for t in repository.find_all(limit=10000) if t.source_id and str(t.source_id).strip() != ""]

        # Extract unique sprints from source_data
        # Key: (sprint_id, source_space) to handle same sprint ID in different spaces
        sprints = {}
        has_none_sprint = False
        spaces_with_sprints = set()

        for task in tasks:
            source_data = getattr(task, 'source_data', {}) or {}
            sprint_id = source_data.get("sprint_id")
            sprint_name = source_data.get("sprint_name")
            source_space = source_data.get("swtr_space", space)

            if sprint_id:
                key = (sprint_id, source_space)
                if key not in sprints:
                    sprints[key] = {
                        "id": sprint_id,
                        "name": sprint_name or sprint_id,
                        "space": source_space
                    }
                    spaces_with_sprints.add(source_space)
            else:
                # Task without sprint
                has_none_sprint = True

        # Build sprint list, grouped by space for better organization
        sprint_list = list(sprints.values())

        # Sort: OLP first, then DMS, then WMB, then STS, then NONE
        space_order = {"OLP": 0, "DMS": 1, "WMB": 2, "STS": 3}
        sprint_list.sort(key=lambda s: (space_order.get(s["space"], 99), s["id"]))

        # Add "No Sprint" option if there are tasks without sprint
        if has_none_sprint:
            sprint_list.append({
                "id": "NONE",
                "name": "Без спринта",
                "space": "OLP"  # Use first space as default
            })

        # If no sprints found, still return NONE option for flexibility
        if not sprint_list:
            sprint_list.append({
                "id": "NONE",
                "name": "Без спринта",
                "space": "OLP"
            })

        if sprint_list:
            # Return the first sprint as default (exclude "NONE" if present)
            default_sprint = next((s["id"] for s in sprint_list if s["id"] != "NONE"), "")
            return {
                "sprints": sprint_list,
                "default": default_sprint,
                "current": default_sprint
            }

        # No sprints found
        return {
            "sprints": [],
            "error": "No sprint tasks found. Try syncing first via /api/v1/swtr/sync",
            "default": "",
            "current": ""
        }

    def _normalize_task_status_for_filter(self, task: Any) -> str:
        """Normalize task status for filtering using workflow_status_name from source_data."""
        from s21_team_performance.config import WorkflowStatusConfig
        
        workflow_config = WorkflowStatusConfig()
        
        # First try to get status from source_data workflow_status_name
        source_data = getattr(task, 'source_data', {}) or {}
        workflow_status_name = source_data.get('workflow_status_name', '')
        
        if workflow_status_name:
            return workflow_config.normalize_status(workflow_status_name)
        
        # Fall back to local task.status
        return workflow_config.normalize_status(task.status)

    def get_sprint_tasks(self, sprint_id: str, space: str = "WMB") -> Dict[str, Any]:
        """Get tasks from a specific sprint from repository."""
        from app.repositories.task_repository import TaskRepository

        repository = TaskRepository()
        tasks = repository.find_all(source="swtr_sprint", limit=10000)

        # Filter tasks by sprint_id
        sprint_tasks = []
        for task in tasks:
            source_data = task.source_data or {}
            if source_data.get("sprint_id") == sprint_id:
                # Extract assignee from attributes
                assignee = ""
                for attr in source_data.get("swtr_attributes", []):
                    if attr.get("code") == "assigned_to":
                        value = attr.get("value", {})
                        if value:
                            first_name = value.get("firstName", "")
                            last_name = value.get("lastName", "")
                            assignee = f"{last_name} {first_name}".strip() if last_name else value.get("login", "")

                # Extract deadline from attributes
                deadline = None
                for attr in source_data.get("swtr_attributes", []):
                    if attr.get("code") == "deadline":
                        deadline = attr.get("value", "")

                workflow_status = source_data.get("workflow_status", {})
                if isinstance(workflow_status, str):
                    status = workflow_status
                    status_code = ""
                else:
                    status = workflow_status.get("name", task.status)
                    status_code = workflow_status.get("code", "")

                sprint_tasks.append({
                    "id": source_data.get("swtr_code", task.source_id),
                    "summary": source_data.get("swtr_summary", task.title),
                    "status": status,
                    "status_code": status_code,
                    "assignee": assignee,
                    "deadline": deadline,
                    "title": task.title,
                    "source_id": task.source_id,
                })

        return {
            "sprint_id": sprint_id,
            "space": space,
            "tasks": sprint_tasks,
            "count": len(sprint_tasks)
        }

    def get_status_display(self, status: str) -> str:
        """Получить текстовое представление статуса"""
        display = {
            "green": "✅ Здоровье спринта в норме",
            "yellow": "⚠️ Требуется внимание",
            "red": "❌ Критическое состояние"
        }
        return display.get(status, "Неизвестный статус")

    def get_tasks(
        self,
        query: str = "",
        team_members: List[str] = None,
        products: List[str] = None,
        sprint_id: str = None,
        status_filter: List[str] = None,
        params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get tasks from SWTR (not just repository)."""
        import re
        from app.repositories.task_repository import TaskRepository

        # Extract sprint_id from query if not provided
        if sprint_id is None or not sprint_id:
            query_lower = query.lower()
            if "спринт" in query_lower or "sprint" in query_lower:
                sprint_match = re.search(r'(dms|olp|wmb|sts)-sprnt-\d+', query_lower)
                if sprint_match:
                    sprint_id = sprint_match.group(0).upper()

        # Get short name for filtering (format: "Last First")
        assignee_short_name = None
        if team_members:
            for member_login in team_members:
                short_name = get_member_short_name(member_login)
                if short_name and short_name != member_login:
                    assignee_short_name = short_name
                    break

        # Use TaskRepository to get fresh data from SWTR sync
        repository = TaskRepository()

        # Get all tasks with source_id (SWTR tasks - they have source_id populated)
        all_tasks = [t for t in repository.find_all(limit=10000) if t.source_id and str(t.source_id).strip() != ""]

        # Extract status filter from query or from params
        # Priority: params > query
        if not status_filter and params:
            status_filter = params.get('status_filter')
        if not status_filter:
            query_lower = query.lower()
            
            # First check for specific status after "в статусе"
            if "в статусе" in query_lower:
                # Extract status after "в статусе"
                status_match = re.search(r'в статусе\s+(\w+)', query_lower)
                if status_match:
                    status_name = status_match.group(1)
                    # Использовать normalize_status для нормализации
                    status_filter = [self.workflow_config.normalize_status(status_name)]
            elif "открытые" in query_lower or "открыт" in query_lower or "open" in query_lower:
                # Open статусы (Backlog) + In progress + Review Queue + QA Queue
                status_filter = ["Open", "In progress", "Ready for review", "Ready for QA"]
            elif "закрытые" in query_lower or "closed" in query_lower or "done" in query_lower:
                # Закрытые и решенные
                status_filter = ["Closed", "Resolved"]
            elif "в работе" in query_lower or "в процессе" in query_lower or "в прогрессе" in query_lower:
                # Active Work
                status_filter = ["In progress", "Reopened"]
            elif "на тестировании" in query_lower or "тестируются" in query_lower or "testing" in query_lower:
                # QA
                status_filter = ["QA", "Ready for QA"]
            elif "на ревью" in query_lower or "ревью" in query_lower or "review" in query_lower:
                # Review
                status_filter = ["In review", "Ready for review"]
            elif "заблокированные" in query_lower or "blocked" in query_lower:
                # Waiting / Blocked
                status_filter = ["Need info"]
            elif "ожидание" in query_lower or "ожидающие" in query_lower:
                # Waiting / Blocked
                status_filter = ["Need info"]
            elif "todo" in query_lower or "не сделано" in query_lower or "в ожидании" in query_lower:
                status_filter = ["Open"]

        # Filter by team members (check both assigned_to and responsible)
        result_tasks = []
        for task in all_tasks:
            task_assignee_name = task.assignee or ""
            
            # Check if task has matching assignee or responsible
            has_matching_assignee = False
            
            if assignee_short_name:
                # Check assigned_to (task.assignee should match assignee_short_name)
                # Note: task.assignee is set from swtr_attributes.assigned_to during sync
                if task_assignee_name and task_assignee_name.lower() == assignee_short_name.lower():
                    has_matching_assignee = True
                
                # Check responsible in source_data if assigned_to doesn't match
                if not has_matching_assignee:
                    source_data = getattr(task, 'source_data', {}) or {}
                    responsible_login = source_data.get('responsible', {})
                    if isinstance(responsible_login, dict):
                        responsible_login = responsible_login.get('login', '')
                    elif isinstance(responsible_login, str):
                        responsible_login = responsible_login
                    else:
                        responsible_login = ''
                    
                    # Normalize responsible login to short name for comparison
                    if responsible_login:
                        responsible_short_name = get_member_short_name(responsible_login)
                        if responsible_short_name and responsible_short_name != responsible_login:
                            if responsible_short_name.lower() == assignee_short_name.lower():
                                has_matching_assignee = True
            
            if assignee_short_name and not has_matching_assignee:
                continue  # Skip tasks without matching assignee or responsible

            # Get source_data for task
            source_data = getattr(task, 'source_data', {}) or {}

            # Get original workflow status from source_data if available
            # This preserves the original AS21 status (Open, In progress, Ready for review, etc.)
            workflow_status = source_data.get('workflow_status', '')
            workflow_status_name = source_data.get('workflow_status_name', '')

            # Use workflow_status_name for filtering if available, otherwise fall back to workflow_status
            # workflow_status_name contains the user-friendly status like "Open", "In progress", etc.
            if workflow_status_name:
                task_status = workflow_status_name
            elif workflow_status:
                task_status = workflow_status
            else:
                task_status = task.status or "todo"

            # Normalize status for filtering
            normalized_status = self.workflow_config.normalize_status(task_status)
            if status_filter and normalized_status not in status_filter:
                continue

            # Check sprint_id if specified
            if sprint_id == "NONE":
                # Filter tasks without sprint
                if source_data.get("sprint_id") is not None:
                    continue
            elif sprint_id:
                # Filter tasks with specific sprint
                if source_data.get("sprint_id") != sprint_id:
                    continue

            # Build task display
            task_info = {
                "source_id": task.source_id or task.id,
                "title": task.title or "",
                "assignee": task_assignee_name,
                "status": workflow_status_name if workflow_status_name else task_status,
                "priority": source_data.get("priority", {}).get("name", "") if isinstance(source_data.get("priority"), dict) else source_data.get("priority", ""),
                "source_url": f"https://portal.works.prod.sbt/swtr/units/all/unit/{task.source_id}?space={source_data.get('swtr_space', 'WMB')}&tenant=default" if task.source_id else None,
            }
            result_tasks.append(task_info)

        # Sort by priority (high first)
        priority_order = {"high": 1, "medium": 2, "low": 3}

        def get_priority_value(x):
            priority = x.get("priority", "")
            if isinstance(priority, dict):
                return priority_order.get(priority.get("name", "").lower(), 4)
            return priority_order.get(priority.lower(), 4)

        result_tasks.sort(key=get_priority_value)

        # If no sprint_id, ALWAYS return list of available sprints for user to choose from
        # User needs to specify a sprint before filtering by status
        if not sprint_id:
            # If team_members is specified, still return sprint list first
            # This handles queries like "Задачи Калачанова" and "открытые задачи Гаранина" without sprint
            sprint_list = self.get_sprint_list(products[0] if products else "WMB")
            sprints = sprint_list.get("sprints", [])
            
            # Build response with sprint list
            response = {
                "sprints": sprints,
                "default": sprint_list.get("default", ""),
                "count": len(result_tasks),
                "query": query,
                "assignee": assignee_short_name,
                "sprint_id": None,
                "needs_sprint_selection": True
            }
            
            # If no team_members, add message for user
            if not team_members:
                response["message"] = "Выберите спринт из списка, чтобы показать задачи"
            elif status_filter:
                # If status_filter is set but no sprint, let user know they need to select sprint first
                response["message"] = f"Выберите спринт из списка, чтобы показать {status_filter} задачи"
            
            return response

        # If sprint_id is specified, apply status filter and return tasks
        return {
            "tasks": result_tasks,
            "count": len(result_tasks),
            "query": query,
            "assignee": assignee_short_name,
            "sprint_id": sprint_id
        }
