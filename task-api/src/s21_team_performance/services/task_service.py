"""Task service for Team Performance Agent using SWTRAdapter and local repository."""

from __future__ import annotations

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import yaml

from s21_agent.connectors.s21_swtr_adapter import SWTRAdapter
from s21_agent.models.task import Task
from s21_team_performance.services.metrics import (
    SprintMetrics,
    FlowMetrics,
    MemberLoad,
    TaskStatusCounts,
    ThroughputMetrics,
)
from app.repositories.task_repository import TaskRepository
from app.services.swtr_sync_service import SWTRSyncService


# Team members configuration
TEAM_MEMBERS_CONFIG = Path(__file__).parent.parent.parent.parent / "config" / "team_members.yaml"


def load_team_members() -> List[Dict[str, Any]]:
    """Load team members from YAML configuration."""
    try:
        with open(TEAM_MEMBERS_CONFIG, "r") as f:
            config = yaml.safe_load(f)
            return config.get("members", [])
    except Exception:
        return []


def get_member_by_login(login: str) -> Optional[Dict[str, Any]]:
    """Get team member info by login."""
    # First try login mappings
    login_lower = login.lower()
    if login_lower in LOGIN_MAPPINGS:
        login = LOGIN_MAPPINGS[login_lower]
        login_lower = login.lower()  # Reset login_lower after mapping

    members = load_team_members()
    for member in members:
        if member.get("login", "").lower() == login_lower:
            return member
    return None


# Login mappings: alternate login -> standard login (from config)
# Some systems may use different login formats
LOGIN_MAPPINGS: Dict[str, str] = {
    # Format: alternate_login -> standard_login
    "garanin.r.v": "Garanin.R.V",
    "garanin.r": "Garanin.R.V",
    "garanin": "Garanin.R.V",
}

# Name mappings: short_name (from tasks) -> login (from config)
# Tasks use format "Last Name First Name" (e.g., "Гаранин Родион")
# Config uses format "First Name Patronymic Last Name" (e.g., "Калачанов Виктор Вячеславович")
NAME_MAPPINGS: Dict[str, str] = {
    # Format: "Last Name First Name" (from tasks) -> login (from config)
    "Гаранин Родион": "Garanin.R.V",
    "Кондратчикова Полина": "Kondratchikova.P.I",
    "Семавин Михаил": "Semavin.M.M",
    "Долговской Евгений": "Dolgovskoy.E.N",
    "Гончаров Александр": "Goncharov.A.O",
    "Решетник Александр": "Reshetnik.A",
    "Калачанов Виктор": "Kalachanov.V.V",
    "Агатаева Айна": "Agataeva.A.Z",
    "Жданов Александр": "Zhdanov.A.Ni",
    "Макошина Верея": "Makoshina.V.V",
    "Моисеев Андрей": "Moiseev.A.N",
    "Кузнецов Матвей": "Kuznetsov.M.Se",
    "Гальцов Александр": "Galtsov.A.A",
    "Шалдунов Александр": "Shaldunov.A.V",
    "Безруков Павел": "Bezrukov.P.S",
}


def get_member_full_name(login: str) -> str:
    """Get full name of team member by login."""
    member = get_member_by_login(login)
    if member:
        return member.get("full_name", login)
    return login


def get_member_short_name(login: str) -> str:
    """Get short name (Last First) for task filtering from login.

    Tasks use format "Last Name First Name" (e.g., "Гаранин Родион")
    Config uses format "Last Name First Name Patronymic" (e.g., "Гаранин Родион Владимирович")

    We extract just "Last First" from the full name.
    """
    login_lower = login.lower()
    
    # Check name mappings first (most reliable)
    for short_name, member_login in NAME_MAPPINGS.items():
        if member_login.lower() == login_lower:
            return short_name

    # Fallback: get from config and convert
    member = get_member_by_login(login)
    if member:
        full_name = member.get("full_name", login)
        # Config format: "Last First Patronymic" -> extract Last and First
        parts = full_name.split()
        if len(parts) >= 2:
            # Get last name (first word) and first name (second word)
            last_name = parts[0]
            first_name = parts[1] if len(parts) >= 2 else parts[0]
            return f"{last_name} {first_name}"
        return full_name

    return login


def get_login_by_full_name(full_name: str) -> Optional[str]:
    """Get login by full name."""
    members = load_team_members()
    for member in members:
        if member.get("full_name") == full_name:
            return member.get("login")
    return None


class TaskService:
    """Service for fetching and analyzing task data from SWTR."""

    def __init__(self, api_port: int | None = None):
        """Initialize with SWTRAdapter."""
        self.adapter = SWTRAdapter(api_port=api_port)
        self.repository = TaskRepository()

    async def fetch_tasks_by_assignee(
        self,
        login: str,
        status_filter: Optional[List[str]] = None
    ) -> List[Task]:
        """Fetch tasks for a specific assignee by login.

        The API may filter by full name or login depending on configuration.
        We try multiple approaches to maximize task retrieval.

        Note: API assignees are in format "Last Name First Name" (e.g., "Калачанов Виктор")
        while config full names are in format "First Name Patronymic Last Name" (e.g., "Калачанов Виктор Вячеславович")
        """
        all_tasks: List[Task] = []

        # Get short name (Last First) for API filtering
        short_name = get_member_short_name(login)

        # Normalize status filter for API (convert Open->Open, todo->Open, etc.)
        # Note: For API filtering, we need to use the API's status values (todo, in_progress, done)
        # But the status_filter from user input uses AS21 values (Open, In progress, Closed)
        # So we need to map: Open->Open (which becomes Open), In progress->In progress, etc.
        # Actually, the API expects todo, in_progress, done for status filter
        # So we need to map: Open->todo, In progress->in_progress, Closed->done
        from s21_team_performance.config import WorkflowStatusConfig
        workflow_config = WorkflowStatusConfig()
        api_status_filter = None
        if status_filter:
            # Map AS21 statuses to local status enum values for API
            api_status_filter = []
            for s in status_filter:
                normalized = workflow_config.normalize_status(s)
                # Convert Open->todo, In progress->in_progress, Closed->done, etc.
                if normalized == "Open":
                    api_status_filter.append("todo")
                elif normalized == "In progress":
                    api_status_filter.append("in_progress")
                elif normalized == "Closed":
                    api_status_filter.append("done")
                elif normalized == "Need info":
                    api_status_filter.append("todo")  # Blocked tasks in todo
                else:
                    api_status_filter.append(normalized.lower().replace(" ", "_"))

        # Try filtering by short name first using TaskRepository for full data
        # Use TaskRepository to get tasks with full source_data
        all_tasks_from_repo = self.repository.find_all(limit=10000)
        
        for task in all_tasks_from_repo:
            task_assignee = task.assignee or ""
            
            # Check if the task's assignee field matches
            if short_name.lower() in task_assignee.lower() or login.lower() in task_assignee.lower():
                # Check status filter - use normalized task status
                task_status = self._normalize_task_status(task)
                if status_filter is None or task_status in status_filter:
                    all_tasks.append(task)
        
        # If no tasks found, try adapter as fallback
        if not all_tasks:
            filters: Dict[str, Any] = {"assignee": short_name}
            if api_status_filter:
                filters["status"] = api_status_filter
            
            tasks_by_shortname = self.adapter.search_tasks("", filters)
            if tasks_by_shortname:
                all_tasks = tasks_by_shortname

        return all_tasks

    async def fetch_all_team_tasks(
        self,
        team_members: List[str],
        period_days: int = 30
    ) -> List[Task]:
        """Fetch all tasks for team members within a period."""
        all_tasks: List[Task] = []

        for member_login in team_members:
            tasks = await self.fetch_tasks_by_assignee(member_login)
            all_tasks.extend(tasks)

        return all_tasks

    async def get_sprint_metrics(self, sprint_id: str) -> SprintMetrics:
        """Calculate sprint metrics from actual task data."""
        # Note: This is a simplified implementation.
        # In real scenarios, sprint data would come from Jira sprint board.
        # For now, we calculate based on tasks marked with sprint info.

        # Get all tasks in the sprint (simplified: filter by title or label)
        # In real implementation, use Jira sprint API
        tasks = self.adapter.search_tasks(sprint_id, {"status": "done"})

        # Calculate metrics from completed tasks
        completed_effort = sum(self._estimate_effort(t) for t in tasks)
        committed_effort = completed_effort * 1.2  # Placeholder: assume 80% completion rate

        return SprintMetrics(
            sprint_id=sprint_id,
            committed_effort=committed_effort,
            completed_effort=completed_effort,
            throughput=len(tasks),
            blocked_count=self._count_blocked_tasks(tasks),
        )

    def _estimate_effort(self, task: Task) -> float:
        """Estimate story points for a task based on various factors.
        
        Priority order:
        1. story_points attribute (if set)
        2. estimate attribute (hours - convert to story points)
        3. Custom field customfield_16700 (planned_end - calculate duration)
        4. Heuristic based on task characteristics
        """
        # Get source_data for attribute lookup
        source_data = getattr(task, 'source_data', {}) or {}
        attrs = source_data.get('swtr_attributes', [])
        
        # 1. Check story_points attribute
        for attr in attrs:
            if attr.get('code') == 'story_points':
                value = attr.get('value')
                if value is not None and value > 0:
                    return float(value)
        
        # 2. Check estimate attribute (hours)
        for attr in attrs:
            if attr.get('code') == 'estimate':
                value = attr.get('value')
                if value is not None:
                    # Convert hours to story points (assuming 8h = 1 story point, max 10h = 1.25 sp)
                    hours = float(value) if isinstance(value, (int, float)) else 0
                    if hours > 0:
                        return min(hours / 8.0, 10.0)  # Cap at 10 story points
        
        # 3. Check customfield_16700 (planned_end) for duration-based estimation
        planned_end = None
        for attr in attrs:
            if attr.get('code') == 'customfield_16700':
                value = attr.get('value')
                if value:
                    try:
                        from datetime import datetime
                        end_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        planned_end = end_dt
                    except:
                        pass
            if attr.get('code') == 'customfield_16701':
                value = attr.get('value')
                if value:
                    try:
                        from datetime import datetime
                        start_dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        if planned_end:
                            # Calculate working days (8h/day)
                            duration_days = (planned_end - start_dt).days
                            if duration_days > 0:
                                return min(duration_days * 0.5, 10.0)  # 0.5 sp per working day
                    except:
                        pass
        
        # 4. Heuristic based on task characteristics
        title = task.title.lower()
        desc = task.description.lower()

        effort = 1.0

        # Size indicators
        if any(word in title or word in desc for word in ["epic", "large", "complex"]):
            effort = 8.0
        elif any(word in title or word in desc for word in ["medium", "module"]):
            effort = 5.0
        elif any(word in title or word in desc for word in ["small", "fix", "task"]):
            effort = 2.0

        return effort

    def _count_blocked_tasks(self, tasks: List[Task]) -> int:
        """Count tasks with blocked status or indicators."""
        blocked_keywords = ["blocked", "blocker", "阻塞"]
        count = 0

        for task in tasks:
            if task.status.lower() == "blocked":
                count += 1
            elif any(kw in task.title.lower() for kw in blocked_keywords):
                count += 1

        return count

    def _normalize_task_status(self, task: Task) -> str:
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

    async def calculate_flow_metrics(self, period_days: int = 30) -> FlowMetrics:
        """Calculate flow metrics for the team."""
        # Get team members
        members = load_team_members()
        member_logins = [m.get("login") for m in members]

        # Fetch all tasks
        all_tasks = await self.fetch_all_team_tasks(member_logins, period_days)

        if not all_tasks:
            return FlowMetrics(
                throughput=0,
                avg_cycle_time=0.0,
                avg_lead_time=0.0,
                avg_wip=0.0,
                flow_efficiency=0.0,
            )

        # Calculate throughput (completed tasks in period)
        completed_tasks = [
            t for t in all_tasks
            if t.status == "done" and self._is_within_period(t, period_days)
        ]
        throughput = len(completed_tasks)

        # Calculate cycle time (time from in_progress to done)
        cycle_times = []
        for task in completed_tasks:
            cycle_time = self._calculate_cycle_time(task)
            if cycle_time:
                cycle_times.append(cycle_time)

        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0.0

        # Calculate lead time (time from created to done)
        lead_times = []
        for task in completed_tasks:
            lead_time = (task.updated_at - task.created_at).days
            if lead_time > 0:
                lead_times.append(lead_time)

        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0.0

        # Calculate WIP (average active tasks)
        wip_values = self._calculate_wip_over_period(all_tasks, period_days)
        avg_wip = sum(wip_values) / len(wip_values) if wip_values else 0.0

        # Flow efficiency (value-adding time / total time)
        # Assume 70% efficiency as default
        flow_efficiency = 0.7 if avg_lead_time > 0 else 0.0

        return FlowMetrics(
            throughput=throughput,
            avg_cycle_time=round(avg_cycle_time, 2),
            avg_lead_time=round(avg_lead_time, 2),
            avg_wip=round(avg_wip, 2),
            flow_efficiency=flow_efficiency,
            blocked_time=self._calculate_blocked_time(all_tasks),
        )

    def _is_within_period(self, task: Task, days: int) -> bool:
        """Check if task was completed within the period."""
        cutoff = datetime.now() - timedelta(days=days)
        # Handle both offset-naive and offset-aware datetimes
        task_updated = task.updated_at
        if task_updated.tzinfo is not None:
            # Make cutoff offset-aware if task is
            cutoff = cutoff.replace(tzinfo=task_updated.tzinfo)
        return task_updated >= cutoff

    def _calculate_cycle_time(self, task: Task) -> Optional[float]:
        """Calculate cycle time for a task (time in in_progress)."""
        # Simplified: assume task was in_progress for half of its total time
        # In real implementation, track status changes
        total_time = (task.updated_at - task.created_at).days
        return total_time * 0.5 if total_time > 0 else None

    def _calculate_wip_over_period(self, tasks: List[Task], days: int) -> List[float]:
        """Calculate WIP values over the period."""
        # Simplified: count active tasks per day
        wip_values = []
        cutoff = datetime.now() - timedelta(days=days)
        now = datetime.now()

        for task in tasks:
            # Handle timezone awareness
            task_created = task.created_at
            if task_created.tzinfo is not None:
                cutoff = cutoff.replace(tzinfo=task_created.tzinfo)
                now = now.replace(tzinfo=task_created.tzinfo)

            if task_created >= cutoff:
                # Add to WIP for duration of task
                duration = min((now - task_created).days, days)
                if duration > 0:
                    wip_values.append(1.0 / duration)

        return wip_values[:30] if wip_values else [0.0]

    def _calculate_blocked_time(self, tasks: List[Task]) -> float:
        """Calculate total blocked time across all tasks."""
        blocked_keywords = ["blocked", "blocker", "阻塞"]
        total_blocked = 0.0

        for task in tasks:
            if task.status.lower() == "blocked":
                total_blocked += 1.0
            elif any(kw in task.title.lower() for kw in blocked_keywords):
                total_blocked += 0.5

        return total_blocked

    async def calculate_member_loads(
        self,
        team_members: List[str],
        period_days: int = 30
    ) -> List[MemberLoad]:
        """Calculate workload metrics for each team member."""
        member_loads: List[MemberLoad] = []

        for login in team_members:
            tasks = await self.fetch_tasks_by_assignee(login)

            # Count tasks by status
            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.status == "done"])
            wip = len([t for t in tasks if t.status == "in_progress"])
            blocked = len([t for t in tasks if t.status == "blocked"])
            on_hold = len([t for t in tasks if t.status == "on_hold"])

            # Check for overdue tasks
            overdue = 0
            cutoff = datetime.now()
            for task in tasks:
                if task.deadline and task.deadline < cutoff and task.status != "done":
                    overdue += 1

            # Get full name
            full_name = get_member_full_name(login)

            member_loads.append(MemberLoad(
                login=login,
                full_name=full_name,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                wip=wip,
                blocked_tasks=blocked,
                on_hold_tasks=on_hold,
                overdue_tasks=overdue,
            ))

        return member_loads

    async def get_throughput_metrics(self, period_days: int = 90) -> ThroughputMetrics:
        """Calculate throughput metrics over time."""
        # Get team members
        members = load_team_members()
        member_logins = [m.get("login") for m in members]

        # Fetch all tasks
        all_tasks = await self.fetch_all_team_tasks(member_logins, period_days)

        # Get completed tasks within period
        cutoff = datetime.now() - timedelta(days=period_days)
        completed_tasks = [
            t for t in all_tasks
            if t.status == "done" and t.updated_at >= cutoff
        ]

        # Calculate daily throughput
        daily_counts: Dict[str, int] = {}
        for task in completed_tasks:
            date_str = task.updated_at.strftime("%Y-%m-%d")
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

        daily_throughput = list(daily_counts.values())

        # Calculate weekly throughput
        weekly_counts: Dict[str, int] = {}
        for date_str, count in daily_counts.items():
            week_num = datetime.strptime(date_str, "%Y-%m-%d").isocalendar()[1]
            week_key = f" week {week_num}"
            weekly_counts[week_key] = weekly_counts.get(week_key, 0) + count

        weekly_throughput = list(weekly_counts.values())

        # Calculate average and standard deviation
        if daily_throughput:
            avg_throughput = sum(daily_throughput) / len(daily_throughput)
            variance = sum((x - avg_throughput) ** 2 for x in daily_throughput) / len(daily_throughput)
            throughput_std = variance ** 0.5
        else:
            avg_throughput = 0.0
            throughput_std = 0.0

        # Determine trend
        if len(daily_throughput) >= 7:
            first_week_avg = sum(daily_throughput[:7]) / 7
            last_week_avg = sum(daily_throughput[-7:]) / 7
            if last_week_avg > first_week_avg * 1.1:
                trend = "increasing"
            elif last_week_avg < first_week_avg * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return ThroughputMetrics(
            daily_throughput=daily_throughput,
            weekly_throughput=weekly_throughput,
            monthly_throughput=[sum(weekly_throughput[-4:])] if weekly_throughput else [],
            avg_throughput=round(avg_throughput, 2),
            throughput_std=round(throughput_std, 2),
            trend=trend,
        )

    async def get_task_status_counts(self) -> TaskStatusCounts:
        """Get task counts by status for the team."""
        members = load_team_members()
        member_logins = [m.get("login") for m in members]

        all_tasks = await self.fetch_all_team_tasks(member_logins, 90)

        status_counts = TaskStatusCounts(
            todo=0,
            in_progress=0,
            done=0,
            review=0,
            testing=0,
            blocked=0,
            on_hold=0,
        )

        for task in all_tasks:
            status_lower = task.status.lower()
            if status_lower == "done":
                status_counts.done += 1
            elif status_lower == "in_progress":
                status_counts.in_progress += 1
            elif status_lower == "todo":
                status_counts.todo += 1
            elif status_lower == "review":
                status_counts.review += 1
            elif status_lower == "testing":
                status_counts.testing += 1
            elif status_lower == "blocked":
                status_counts.blocked += 1
            elif status_lower == "on_hold":
                status_counts.on_hold += 1

        return status_counts

    async def get_bottleneck_data(self, period_days: int = 30) -> Dict[str, Any]:
        """Get bottleneck analysis data."""
        members = load_team_members()
        member_logins = [m.get("login") for m in members]

        all_tasks = await self.fetch_all_team_tasks(member_logins, period_days)

        # Categorize tasks by bottleneck indicators
        review_queue = []
        testing_queue = []
        blocked_tasks = []
        waiting_architecture = []
        waiting_expert = []

        for task in all_tasks:
            title_lower = task.title.lower()
            desc_lower = task.description.lower()

            # Review queue indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["review", "peer review", "code review"]):
                if task.status == "in_progress":
                    review_queue.append(task.source_id or task.id)

            # Testing queue indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["test", "qa", "testing"]):
                if task.status == "in_progress":
                    testing_queue.append(task.source_id or task.id)

            # Blocked tasks
            if task.status == "blocked":
                blocked_tasks.append(task.source_id or task.id)

            # Architecture indicators
            if any(kw in title_lower or kw in desc_lower for kw in ["arch", "architecture", "design"]):
                if task.status == "in_progress":
                    waiting_architecture.append(task.source_id or task.id)

            # Expert-dependent tasks
            if any(kw in title_lower or kw in desc_lower for kw in ["expert", "bus factor", "key person"]):
                waiting_expert.append(task.source_id or task.id)

        return {
            "tasks": len(all_tasks),
            "review_queue": review_queue[:20],
            "testing_queue": testing_queue[:20],
            "blocked_tasks": blocked_tasks[:20],
            "waiting_architecture": waiting_architecture[:20],
            "waiting_expert": waiting_expert[:20],
        }

    async def get_release_data(self, release_id: str) -> Dict[str, Any]:
        """Get release data from tasks."""
        # Search for tasks related to this release
        tasks = self.adapter.search_tasks(release_id, {})

        features = []
        for task in tasks:
            features.append({
                "id": task.source_id or task.id,
                "name": task.title,
                "status": task.status,
                "is_critical": self._is_critical_task(task),
            })

        return {
            "release_id": release_id,
            "features": features,
            "planned_date": self._extract_release_date(tasks),
        }

    def _is_critical_task(self, task: Task) -> bool:
        """Determine if a task is critical for release."""
        title_lower = task.title.lower()
        critical_keywords = ["critical", "must have", "blocker", "release"]
        return any(kw in title_lower for kw in critical_keywords)

    def _extract_release_date(self, tasks: List[Task]) -> Optional[str]:
        """Extract release date from task deadlines or titles."""
        release_dates = []

        for task in tasks:
            if task.deadline:
                release_dates.append(task.deadline.strftime("%Y-%m-%d"))

        if release_dates:
            return min(release_dates)

        return None
