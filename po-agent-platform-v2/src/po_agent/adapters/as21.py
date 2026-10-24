"""AS21 adapter module for PO Agent Platform v2."""

from abc import ABC, abstractmethod
from typing import Optional

from po_agent.domain.models import (
    Task,
    TaskKey,
    SprintId,
    ReleaseId,
    StatusTransition,
    Attachment,
    AttachmentType,
)


class AS21Adapter(ABC):
    """Abstract base class for AS21/SWTR adapter."""

    @abstractmethod
    async def get_task(self, task_key: str) -> Optional[Task]:
        """Get a single task by its key.

        Args:
            task_key: Task identifier (e.g., WMB-123)

        Returns:
            Task if found, None otherwise
        """

    @abstractmethod
    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        """Search tasks using JQL query.

        Args:
            jql: JQL query string
            max_results: Maximum number of results
            fields: List of fields to return

        Returns:
            List of matching tasks
        """

    @abstractmethod
    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        """Get task history (status transitions).

        Args:
            task_key: Task identifier

        Returns:
            List of status transitions
        """

    @abstractmethod
    async def get_sprint_tasks(
        self,
        sprint_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get all tasks for a sprint.

        Args:
            sprint_id: Sprint identifier
            space: Project space (optional)

        Returns:
            List of sprint tasks
        """

    @abstractmethod
    async def get_release_tasks(
        self,
        release_id: str,
        space: Optional[str] = None,
    ) -> list[Task]:
        """Get all tasks for a release.

        Args:
            release_id: Release identifier
            space: Project space (optional)

        Returns:
            List of release tasks
        """

    @abstractmethod
    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        """Get attachment metadata for a task.

        Args:
            task_key: Task identifier
            attachment_id: Optional specific attachment ID

        Returns:
            List of attachment metadata
        """

    @abstractmethod
    async def close(self) -> None:
        """Close adapter and release resources."""
