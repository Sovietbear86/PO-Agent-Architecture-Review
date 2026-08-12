"""Fake AS21 adapter for testing purposes."""

import random
from datetime import datetime, timedelta
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
    TeamRole,
)


class FakeAS21Adapter(AS21Adapter):
    """Fake AS21 adapter with predefined fixtures for testing.

    This adapter returns deterministic data based on task keys and query patterns.
    Use for unit testing without real AS21/SWTR connection.
    """

    def __init__(self):
        """Initialize fake adapter with test fixtures."""
        self._tasks: dict[str, Task] = {}
        self._sprints: dict[str, list[str]] = {}
        self._releases: dict[str, list[str]] = {}
        self._attachments: dict[str, list[Attachment]] = {}

        self._init_fixtures()

    def _init_fixtures(self) -> None:
        """Initialize test fixtures."""
        now = datetime.now()

        # Create sample tasks
        task1 = Task(
            key="WMB-101",
            id="task-001",
            title="Implement user authentication",
            description="Add OAuth2 support for user login",
            status=TaskStatus.RESOLVED,
            status_category=StatusCategory.COMPLETED_PENDING,
            status_transitions=[
                StatusTransition(
                    from_status=TaskStatus.OPEN,
                    to_status=TaskStatus.IN_PROGRESS,
                    timestamp=now - timedelta(days=10),
                    author="Ivanov.I.I",
                ),
                StatusTransition(
                    from_status=TaskStatus.IN_PROGRESS,
                    to_status=TaskStatus.RESOLVED,
                    timestamp=now - timedelta(days=3),
                    author="Petrov.P.P",
                ),
            ],
            created_at=now - timedelta(days=12),
            updated_at=now - timedelta(days=3),
            assignee="Ivanov.I.I",
            priority=TaskPriority.HIGH,
            source="test",
        )

        task2 = Task(
            key="WMB-102",
            id="task-002",
            title="Fix login bug",
            description="Users cannot log in on mobile devices",
            status=TaskStatus.IN_PROGRESS,
            status_category=StatusCategory.ACTIVE_WORK,
            status_transitions=[
                StatusTransition(
                    from_status=TaskStatus.OPEN,
                    to_status=TaskStatus.IN_PROGRESS,
                    timestamp=now - timedelta(days=5),
                    author="Sidorov.S.S",
                ),
            ],
            created_at=now - timedelta(days=7),
            updated_at=now - timedelta(days=2),
            assignee="Sidorov.S.S",
            priority=TaskPriority.CRITICAL,
            source="test",
        )

        task3 = Task(
            key="WMB-103",
            id="task-003",
            title="Add analytics dashboard",
            description="Create dashboard for team metrics",
            status=TaskStatus.OPEN,
            status_category=StatusCategory.BACKLOG,
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(days=20),
            priority=TaskPriority.LOW,
            source="test",
        )

        task4 = Task(
            key="DMS-201",
            id="task-004",
            title="Data migration script",
            description="Migrate old data to new schema",
            status=TaskStatus.CLOSED,
            status_category=StatusCategory.COMPLETED,
            status_transitions=[
                StatusTransition(
                    from_status=TaskStatus.OPEN,
                    to_status=TaskStatus.IN_PROGRESS,
                    timestamp=now - timedelta(days=15),
                ),
                StatusTransition(
                    from_status=TaskStatus.IN_PROGRESS,
                    to_status=TaskStatus.CLOSED,
                    timestamp=now - timedelta(days=5),
                ),
            ],
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=5),
            source="test",
        )

        task5 = Task(
            key="DMS-202",
            id="task-005",
            title="API endpoint for reports",
            description="Create REST endpoint for report generation",
            status=TaskStatus.NEED_INFO,
            status_category=StatusCategory.WAITING,
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=1),
            source="test",
        )

        # Store tasks
        self._tasks = {
            "WMB-101": task1,
            "WMB-102": task2,
            "WMB-103": task3,
            "DMS-201": task4,
            "DMS-202": task5,
        }

        # Sprint assignments
        self._sprints = {
            "WMB-SPRNT-1": ["WMB-101", "WMB-102"],
            "WMB-SPRNT-2": ["WMB-103"],
            "DMS-SPRNT-1": ["DMS-201", "DMS-202"],
        }

        # Release assignments
        self._releases = {
            "WMB-2024-Q3": ["WMB-101", "WMB-102", "WMB-103"],
            "DMS-2024-Q3": ["DMS-201", "DMS-202"],
        }

        # Attachments
        self._attachments = {
            "WMB-101": [
                Attachment(
                    id="att-001",
                    name="requirements.xlsx",
                    type=AttachmentType.EXCEL,
                    size_bytes=102400,
                    created_at=now - timedelta(days=12),
                    description="Initial requirements",
                )
            ],
            "WMB-102": [
                Attachment(
                    id="att-002",
                    name="screenshot.png",
                    type=AttachmentType.IMAGE,
                    size_bytes=51200,
                    created_at=now - timedelta(days=6),
                    description="Bug screenshot",
                )
            ],
        }

    async def get_task(self, task_key: str) -> Optional[Task]:
        """Get a single task by its key."""
        return self._tasks.get(task_key)

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        """Search tasks using JQL query (simplified implementation).

        Supports:
        - project = PROJECT_CODE
        - assignee = LOGIN
        - sprint = SPRINT_ID
        - key = TASK_KEY
        """
        results = []

        # Simple JQL parsing
        jql_lower = jql.lower()

        # Filter by project
        if "project" in jql_lower:
            # Extract project code from JQL
            # Handle: project = WMB OR project = WMB ORDER BY created DESC
            parts = jql_lower.split("project")
            if len(parts) > 1:
                rest = parts[1].strip()
                if "=" in rest:
                    project_code = rest.split("=")[-1].strip().split()[0].upper()
                    for task in self._tasks.values():
                        if task.key.startswith(project_code):
                            results.append(task)

        # Filter by assignee
        elif "assignee" in jql_lower:
            assignee = jql.split("=")[-1].strip()
            for task in self._tasks.values():
                if task.assignee and assignee.lower() in task.assignee.lower():
                    results.append(task)

        # Filter by sprint
        elif "sprint" in jql_lower:
            sprint_id = jql.split("=")[-1].strip()
            if sprint_id in self._sprints:
                for key in self._sprints[sprint_id]:
                    if key in self._tasks:
                        results.append(self._tasks[key])

        # Filter by key
        elif "key" in jql_lower:
            key = jql.split("=")[-1].strip()
            if key in self._tasks:
                results.append(self._tasks[key])

        # Default: return all tasks
        else:
            results = list(self._tasks.values())

        # Limit results
        return results[:max_results]

    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        """Get task history (status transitions)."""
        task = self._tasks.get(task_key)
        if task:
            return task.status_transitions
        return []

    async def get_sprint_tasks(
        self,
        sprint_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get all tasks for a sprint."""
        if sprint_id not in self._sprints:
            return []

        tasks = []
        for task_key in self._sprints[sprint_id]:
            if task_key in self._tasks:
                tasks.append(self._tasks[task_key])

        return tasks

    async def get_release_tasks(
        self,
        release_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get all tasks for a release."""
        if release_id not in self._releases:
            return []

        tasks = []
        for task_key in self._releases[release_id]:
            if task_key in self._tasks:
                tasks.append(self._tasks[task_key])

        return tasks

    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        """Get attachment metadata for a task."""
        if task_key not in self._attachments:
            return []

        attachments = self._attachments[task_key]

        if attachment_id:
            return [a for a in attachments if a.id == attachment_id]

        return attachments

    async def close(self) -> None:
        """Close adapter (no-op for fake)."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Get all fixture tasks (for testing)."""
        return list(self._tasks.values())

    def get_task_count(self) -> int:
        """Get count of fixture tasks."""
        return len(self._tasks)
