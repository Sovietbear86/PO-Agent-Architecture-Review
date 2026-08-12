"""Legacy AS21 Bridge adapter - reuses transport from swtr_client.py.

This adapter bridges the existing SWTR integration in task-api:
1. FastAPI server on port 8003 (primary)
2. MCP server subprocess (fallback)

The FastAPI endpoint /api/v1/tasks provides all needed operations:
- GET /api/v1/tasks?q=search&limit=50 - Search tasks
- GET /api/v1/tasks/{id} - Get task by ID
- GET /api/v1/tasks/get_by_url?url=... - Get task by SWTR URL
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from po_agent.adapters.as21 import AS21Adapter
from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    StatusCategory,
    StatusTransition,
    Task,
    TaskPriority,
    TaskStatus,
)

# Add parent directory to path for swtr_client import
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def _parse_swtr_status(raw_status: str) -> TaskStatus:
    """Parse SWTR status string to TaskStatus enum."""
    status_map = {
        "Open": TaskStatus.OPEN,
        "Открыта": TaskStatus.OPEN,
        "Need info": TaskStatus.NEED_INFO,
        "Требуется информация": TaskStatus.NEED_INFO,
        "In progress": TaskStatus.IN_PROGRESS,
        "В работе": TaskStatus.IN_PROGRESS,
        "Ready for review": TaskStatus.READY_FOR_REVIEW,
        "Готово к ревью": TaskStatus.READY_FOR_REVIEW,
        "In review": TaskStatus.IN_REVIEW,
        "На ревью": TaskStatus.IN_REVIEW,
        "Ready for QA": TaskStatus.READY_FOR_QA,
        "Готово к QA": TaskStatus.READY_FOR_QA,
        "QA": TaskStatus.QA,
        "Тестирование": TaskStatus.QA,
        "Reopened": TaskStatus.REOPENED,
        "Переоткрыта": TaskStatus.REOPENED,
        "Resolved": TaskStatus.RESOLVED,
        "Решена": TaskStatus.RESOLVED,
        "Closed": TaskStatus.CLOSED,
        "Закрыта": TaskStatus.CLOSED,
        "Cancelled": TaskStatus.CANCELLED,
        "Отменена": TaskStatus.CANCELLED,
    }
    return status_map.get(raw_status, TaskStatus.OPEN)


def _parse_swtr_priority(raw_priority: Optional[str]) -> Optional[TaskPriority]:
    """Parse SWTR priority string to TaskPriority enum."""
    if not raw_priority:
        return None
    priority_map = {
        "Low": TaskPriority.LOW,
        "Medium": TaskPriority.MEDIUM,
        "High": TaskPriority.HIGH,
        "Urgent": TaskPriority.URGENT,
        "Critical": TaskPriority.CRITICAL,
    }
    return priority_map.get(raw_priority)


def _parse_swtr_datetime(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO format datetime from SWTR."""
    if not date_str:
        return None
    try:
        date_str = date_str.strip()
        if "+" in date_str:
            date_str = date_str.split("+")[0]
        elif "-" in date_str and date_str.count("-") > 2:
            parts = date_str.rsplit("-", 1)
            date_str = parts[0]

        formats = [
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
    except Exception:
        return None


def _map_swtr_issue_to_task(issue: dict) -> Optional[Task]:
    """Map SWTR API issue to canonical Task model."""
    fields = issue.get("fields", {})
    key = issue.get("key", "")

    if not key:
        return None

    status_obj = fields.get("status", {})
    raw_status = status_obj.get("name", "") if isinstance(status_obj, dict) else status_obj

    created = _parse_swtr_datetime(fields.get("created"))
    updated = _parse_swtr_datetime(fields.get("updated"))
    resolved = _parse_swtr_datetime(fields.get("resolutiondate"))
    due_date = _parse_swtr_datetime(fields.get("duedate"))

    assignee_obj = fields.get("assignee")
    assignee = None
    assignee_id = None
    if assignee_obj:
        assignee = assignee_obj.get("displayName") if isinstance(assignee_obj, dict) else assignee_obj
        assignee_id = assignee_obj.get("accountId") if isinstance(assignee_obj, dict) else assignee_obj

    priority_obj = fields.get("priority")
    raw_priority = priority_obj.get("name") if isinstance(priority_obj, dict) else priority_obj

    status_enum = _parse_swtr_status(raw_status)
    category_map = {
        TaskStatus.OPEN: StatusCategory.BACKLOG,
        TaskStatus.NEED_INFO: StatusCategory.WAITING,
        TaskStatus.IN_PROGRESS: StatusCategory.ACTIVE_WORK,
        TaskStatus.READY_FOR_REVIEW: StatusCategory.REVIEW_QUEUE,
        TaskStatus.IN_REVIEW: StatusCategory.REVIEW,
        TaskStatus.READY_FOR_QA: StatusCategory.QA_QUEUE,
        TaskStatus.QA: StatusCategory.TESTING,
        TaskStatus.REOPENED: StatusCategory.ACTIVE_WORK,
        TaskStatus.RESOLVED: StatusCategory.COMPLETED_PENDING,
        TaskStatus.CLOSED: StatusCategory.COMPLETED,
        TaskStatus.CANCELLED: StatusCategory.CANCELLED,
    }
    status_category = category_map.get(status_enum, StatusCategory.UNKNOWN)

    task = Task(
        key=key,
        id=key,
        title=fields.get("summary", ""),
        description=fields.get("description", ""),
        status=status_enum,
        status_category=status_category,
        status_transitions=[],
        created_at=created or datetime.now(),
        updated_at=updated or datetime.now(),
        due_date=due_date,
        resolved_at=resolved,
        assignee=assignee,
        assignee_id=assignee_id,
        priority=_parse_swtr_priority(raw_priority),
        labels=fields.get("labels", []),
        components=[c.get("name", "") for c in fields.get("components", [])],
        source="swtr",
    )

    return task


class LegacyAS21Bridge(AS21Adapter):
    """Bridge adapter that reuses the existing FastAPI server on port 8003.

    This adapter connects to the existing task-api FastAPI server which
    provides full SWTR integration via REST API endpoints.
    """

    def __init__(self, api_port: int = 8003, api_host: str = "localhost"):
        """Initialize bridge adapter with FastAPI server connection."""
        import httpx

        self.api_port = api_port
        self.api_host = api_host
        self.timeout = 30

        # Create HTTP client for FastAPI
        self._client = httpx.Client(
            base_url=f"http://{self.api_host}:{self.api_port}",
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )

    async def get_task(self, task_key: str) -> Optional[Task]:
        """Get a single task by its key using FastAPI search endpoint.

        The FastAPI server doesn't have /tasks/{id} endpoint directly,
        so we use search with q={task_key} and limit=1.
        """
        try:
            response = self._client.get(
                "/api/v1/tasks",
                params={"q": task_key, "limit": 1}
            )
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                # Map to canonical Task model
                return self._map_fastapi_task(data[0])
            return None
        except Exception as e:
            print(f"Error getting task {task_key}: {e}")
            return None

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        """Search tasks using JQL query via FastAPI.

        Note: FastAPI search endpoint uses 'q' parameter (simple query),
        not full JQL. We pass the query as-is and let FastAPI handle it.
        """
        try:
            response = self._client.get(
                "/api/v1/tasks",
                params={"q": jql, "limit": max_results}
            )
            response.raise_for_status()
            data = response.json()

            tasks = []
            for item in data:
                task = self._map_fastapi_task(item)
                if task:
                    tasks.append(task)

            return tasks
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return []

    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        """Get task history (status transitions).

        FastAPI doesn't expose history directly.
        Returns empty list - could be enhanced with custom endpoint.
        """
        return []

    async def get_sprint_tasks(
        self,
        sprint_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get tasks for a sprint using FastAPI search endpoint.

        Construct a query for sprint tasks.
        """
        # Use search with sprint filter
        jql = f"sprint = {sprint_id}" if space is None else f"project = {space} AND sprint = {sprint_id}"
        return await self.search_tasks(jql)

    async def get_release_tasks(
        self,
        release_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get tasks for a release using FastAPI search endpoint.

        SWTR uses 'fixVersion' for releases.
        """
        jql = f"fixVersion = {release_id}"
        return await self.search_tasks(jql)

    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        """Get attachment metadata for a task.

        FastAPI doesn't expose attachments directly.
        Returns empty list - could be enhanced with custom endpoint.
        """
        return []

    async def close(self) -> None:
        """Close adapter and release resources."""
        self._client.close()

    def _map_fastapi_task(self, data: dict) -> Optional[Task]:
        """Map FastAPI response to canonical Task model.

        The FastAPI server returns tasks with these fields:
        - id, source_id, title, description
        - status, assignee, deadline
        - source_url, source, created_at, updated_at
        - source_data (SWTR-specific data)
        """
        # Extract source_id (SWTR code)
        source_id = data.get("source_id", data.get("id", ""))

        if not source_id:
            return None

        # Parse deadline
        deadline = None
        if data.get("deadline"):
            try:
                deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Extract source_data for SWTR-specific info
        source_data = data.get("source_data", {})

        # Get status from source_data if not in top-level
        status_str = data.get("status", "")
        if not status_str and source_data:
            status_str = source_data.get("workflow_status", "")

        # Parse status
        status_enum = _parse_swtr_status(status_str)

        # Determine category
        category_map = {
            TaskStatus.OPEN: StatusCategory.BACKLOG,
            TaskStatus.NEED_INFO: StatusCategory.WAITING,
            TaskStatus.IN_PROGRESS: StatusCategory.ACTIVE_WORK,
            TaskStatus.READY_FOR_REVIEW: StatusCategory.REVIEW_QUEUE,
            TaskStatus.IN_REVIEW: StatusCategory.REVIEW,
            TaskStatus.READY_FOR_QA: StatusCategory.QA_QUEUE,
            TaskStatus.QA: StatusCategory.TESTING,
            TaskStatus.REOPENED: StatusCategory.ACTIVE_WORK,
            TaskStatus.RESOLVED: StatusCategory.COMPLETED_PENDING,
            TaskStatus.CLOSED: StatusCategory.COMPLETED,
            TaskStatus.CANCELLED: StatusCategory.CANCELLED,
        }
        status_category = category_map.get(status_enum, StatusCategory.UNKNOWN)

        # Parse dates
        created_at = None
        updated_at = None
        if data.get("created_at"):
            try:
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if data.get("updated_at"):
            try:
                updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Get labels as strings (not dicts)
        # FastAPI returns labels from source_data which can be dicts
        raw_labels = source_data.get("swtr_attributes", [])
        labels = []
        for label in raw_labels:
            if isinstance(label, str):
                labels.append(label)
            elif isinstance(label, dict):
                # Extract label name or code
                label_str = label.get("name") or label.get("code") or ""
                if label_str:
                    labels.append(label_str)

        # Build status transitions (simplified)
        status_transitions = []
        if source_data.get("swtr_code"):
            # Would need history endpoint for real transitions
            pass

        return Task(
            id=source_id,
            key=source_id,
            title=data.get("title", ""),
            description=data.get("description", ""),
            status=status_enum,
            status_category=status_category,
            status_transitions=status_transitions,
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
            due_date=deadline,
            assignee=data.get("assignee"),
            priority=None,
            labels=labels,
            components=[],
            source=data.get("source", "swtr"),
            source_url=data.get("source_url"),
        )
