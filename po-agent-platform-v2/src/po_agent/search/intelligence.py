"""Task Intelligence Search for PO Agent Platform v2.

This module provides intelligent search capabilities for tasks including:
- Phrase search (title, description)
- Task key search (exact match)
- Assignee search
- Sprint search
- Release search
- Attachment type search
"""

from datetime import datetime
from typing import Optional

from po_agent.domain.models import (
    AttachmentType,
    Task,
)


class TaskIntelligenceSearch:
    """Intelligent search engine for tasks.

    Provides flexible search across multiple dimensions:
    - Text search in title/description
    - Structured searches by assignee, sprint, release
    - Filter by status, priority, date range
    """

    def __init__(self):
        """Initialize search engine."""
        self._results_cache: dict = {}

    def search_by_phrase(
        self,
        tasks: list[Task],
        phrase: str,
        case_sensitive: bool = False,
        max_results: int = 50,
    ) -> list[Task]:
        """Search tasks by phrase in title and description.

        Args:
            tasks: List of tasks to search
            phrase: Search phrase
            case_sensitive: Whether to match case
            max_results: Maximum results to return

        Returns:
            List of matching tasks
        """
        if not phrase:
            return tasks[:max_results]

        results = []
        phrase_lower = phrase.lower() if not case_sensitive else phrase

        for task in tasks:
            title = task.title.lower() if not case_sensitive else task.title
            description = (task.description or "").lower() if not case_sensitive else task.description or ""

            if phrase_lower in title or phrase_lower in description:
                results.append(task)

            if len(results) >= max_results:
                break

        return results

    def search_by_task_key(
        self,
        tasks: list[Task],
        task_key: str,
        fuzzy: bool = False,
    ) -> list[Task]:
        """Search tasks by task key (e.g., WMB-123).

        Args:
            tasks: List of tasks to search
            task_key: Task key to find
            fuzzy: Whether to use fuzzy matching (prefix match)

        Returns:
            List of matching tasks
        """
        results = []
        task_key_upper = task_key.upper()

        for task in tasks:
            if task.key.upper() == task_key_upper:
                results.append(task)
                break

            if fuzzy and task.key.upper().startswith(task_key_upper):
                results.append(task)

        return results

    def search_by_assignee(
        self,
        tasks: list[Task],
        assignee: str,
        partial_match: bool = True,
    ) -> list[Task]:
        """Search tasks by assignee.

        Args:
            tasks: List of tasks to search
            assignee: Assignee name/login to search for
            partial_match: Whether to allow partial matches

        Returns:
            List of tasks assigned to the specified person
        """
        results = []
        assignee_lower = assignee.lower()

        for task in tasks:
            if not task.assignee:
                continue

            task_assignee_lower = task.assignee.lower()

            if partial_match:
                if assignee_lower in task_assignee_lower:
                    results.append(task)
            else:
                if task_assignee_lower == assignee_lower:
                    results.append(task)

        return results

    def search_by_sprint(
        self,
        tasks: list[Task],
        sprint_id: str,
        partial_match: bool = True,
    ) -> list[Task]:
        """Search tasks by sprint ID.

        Args:
            tasks: List of tasks to search
            sprint_id: Sprint ID to search for
            partial_match: Whether to allow partial matches

        Returns:
            List of tasks in the specified sprint
        """
        results = []
        sprint_id_lower = sprint_id.lower()

        for task in tasks:
            if not task.sprint_id:
                continue

            task_sprint_lower = task.sprint_id.lower()

            if partial_match:
                if sprint_id_lower in task_sprint_lower:
                    results.append(task)
            else:
                if task_sprint_lower == sprint_id_lower:
                    results.append(task)

        return results

    def search_by_release(
        self,
        tasks: list[Task],
        release_id: str,
        partial_match: bool = True,
    ) -> list[Task]:
        """Search tasks by release ID.

        Args:
            tasks: List of tasks to search
            release_id: Release ID to search for
            partial_match: Whether to allow partial matches

        Returns:
            List of tasks in the specified release
        """
        results = []
        release_id_lower = release_id.lower()

        for task in tasks:
            if not task.release_id:
                continue

            task_release_lower = task.release_id.lower()

            if partial_match:
                if release_id_lower in task_release_lower:
                    results.append(task)
            else:
                if task_release_lower == release_id_lower:
                    results.append(task)

        return results

    def search_by_attachment_type(
        self,
        tasks: list[Task],
        attachment_type: AttachmentType,
    ) -> list[Task]:
        """Search tasks by attachment type.

        Args:
            tasks: List of tasks to search
            attachment_type: Type of attachment to search for

        Returns:
            List of tasks with attachments of the specified type
        """
        results = []
        attachment_type_lower = attachment_type.value.lower()

        for task in tasks:
            for attachment in task.attachments:
                if attachment_type_lower in attachment.type.value.lower():
                    results.append(task)
                    break

        return results

    def search_by_status(
        self,
        tasks: list[Task],
        status: str,
    ) -> list[Task]:
        """Search tasks by status.

        Args:
            tasks: List of tasks to search
            status: Status to search for

        Returns:
            List of tasks with the specified status
        """
        status_lower = status.lower()
        return [t for t in tasks if t.status.value.lower() == status_lower]

    def search_by_priority(
        self,
        tasks: list[Task],
        priority: str,
    ) -> list[Task]:
        """Search tasks by priority.

        Args:
            tasks: List of tasks to search
            priority: Priority to search for

        Returns:
            List of tasks with the specified priority
        """
        if not priority:
            return tasks

        priority_lower = priority.lower()
        return [
            t for t in tasks
            if t.priority and t.priority.value.lower() == priority_lower
        ]

    def search_by_date_range(
        self,
        tasks: list[Task],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[Task]:
        """Search tasks by date range.

        Args:
            tasks: List of tasks to search
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of tasks created within the date range
        """
        results = []

        for task in tasks:
            created = task.created_at

            if start_date and created < start_date:
                continue

            if end_date and created > end_date:
                continue

            results.append(task)

        return results

    def search_combined(
        self,
        tasks: list[Task],
        query: Optional[str] = None,
        assignee: Optional[str] = None,
        sprint_id: Optional[str] = None,
        release_id: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_results: int = 100,
    ) -> list[Task]:
        """Search tasks with combined filters.

        Args:
            tasks: List of tasks to search
            query: Text search query
            assignee: Filter by assignee
            sprint_id: Filter by sprint
            release_id: Filter by release
            status: Filter by status
            priority: Filter by priority
            start_date: Filter by start date
            end_date: Filter by end date
            max_results: Maximum results

        Returns:
            List of matching tasks
        """
        results = tasks

        # Apply text search
        if query:
            results = self.search_by_phrase(results, query, max_results=1000)

        # Apply assignee filter
        if assignee:
            results = self.search_by_assignee(results, assignee)

        # Apply sprint filter
        if sprint_id:
            results = self.search_by_sprint(results, sprint_id)

        # Apply release filter
        if release_id:
            results = self.search_by_release(results, release_id)

        # Apply status filter
        if status:
            results = self.search_by_status(results, status)

        # Apply priority filter
        if priority:
            results = self.search_by_priority(results, priority)

        # Apply date range filter
        if start_date or end_date:
            results = self.search_by_date_range(results, start_date, end_date)

        # Limit results
        return results[:max_results]

    def get_search_stats(
        self,
        tasks: list[Task],
    ) -> dict:
        """Get search statistics.

        Args:
            tasks: List of tasks to analyze

        Returns:
            Dictionary with search statistics
        """
        total = len(tasks)
        with_title = len([t for t in tasks if t.title])
        with_description = len([t for t in tasks if t.description])
        with_assignee = len([t for t in tasks if t.assignee])
        with_sprint = len([t for t in tasks if t.sprint_id])
        with_release = len([t for t in tasks if t.release_id])
        with_attachments = len([t for t in tasks if t.attachments])

        return {
            "total_tasks": total,
            "with_title": with_title,
            "with_description": with_description,
            "with_assignee": with_assignee,
            "with_sprint": with_sprint,
            "with_release": with_release,
            "with_attachments": with_attachments,
        }
