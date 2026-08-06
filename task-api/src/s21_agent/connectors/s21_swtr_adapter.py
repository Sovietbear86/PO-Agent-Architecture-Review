"""SWTR/MCP adapter for S21 Agent."""
from __future__ import annotations

from typing import Any
from datetime import datetime
from uuid import UUID

import httpx

from s21_agent.config import settings
from s21_agent.models.task import Task, Comment, Attachment


class SWTRAdapter:
    """Adapter for SberWorks Task Tracker (SWTR) via FastAPI API."""

    def __init__(self, api_port: int | None = None) -> None:
        self.api_port = api_port or 8003  # Default to FastAPI API port
        self.api_host = "localhost"
        self.timeout = 30
        # Create HTTP client that follows redirects
        self._client = httpx.Client(
            base_url=f"http://{self.api_host}:{self.api_port}",
            timeout=httpx.Timeout(self.timeout),
            follow_redirects=True,
        )

    def search_tasks(self, query: str, filters: dict[str, Any] | None = None) -> list[Task]:
        """Search tasks in SWTR."""
        params = {
            "q": query,
            "limit": settings.max_results,
        }

        if filters:
            if "status" in filters:
                params["status"] = filters["status"]
            if "assignee" in filters:
                params["assignee"] = filters["assignee"]
            if "source" in filters:
                params["source"] = filters["source"]

        try:
            response = self._client.get("/api/v1/tasks", params=params)
            response.raise_for_status()
            data = response.json()

            return [self._map_to_task(task) for task in data]
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return []

    def get_task(self, task_id: str) -> Task | None:
        """Get task by ID from SWTR using search API (no sync needed)."""
        try:
            # Use search API to get task by ID
            response = self._client.get("/api/v1/tasks", params={"q": task_id, "limit": 1})
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                return self._map_to_task(data[0])
            return None
        except Exception as e:
            print(f"Error getting task {task_id}: {e}")
            return None

    def _get_task_by_url_direct(self, task_id: str) -> Task | None:
        """Get task directly from SWTR via URL endpoint."""
        import json
        import re

        # Use adapter's API port (8003) for direct call
        url = f"http://{self.api_host}:8003/api/v1/tasks/get_by_url"
        try:
            # Extract task code from URL
            match = re.search(r"/unit/([A-Z0-9-]+)", task_id)
            if not match:
                return None

            task_code = match.group(1)
            response = self._client.post(
                "/api/v1/tasks/get_by_url",
                json={"url": task_id},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return self._map_to_task(data)
        except Exception as e:
            print(f"Error getting task {task_id} via URL: {e}")
            return None

    def get_task_by_url(self, url: str) -> Task | None:
        """Get task by SWTR URL using MCP endpoint."""
        import json
        import re

        # Extract task code from URL
        # Format: https://portal.works.prod.sbt/swtr/units/all/unit/WMB-12345?...
        match = re.search(r"/unit/([A-Z0-9-]+)", url)
        if not match:
            return None

        task_code = match.group(1)

        # Call get_by_url endpoint on agent's port (3001)
        # Use shorter timeout to avoid circular call issues
        try:
            response = httpx.post(
                f"http://{self.api_host}:3001/tasks/get_by_url",
                timeout=10,  # Shorter timeout
                headers={"Content-Type": "application/json"},
                json={"url": url},
            )

            if response.status_code != 200:
                return None

            data = response.json()
            return self._map_to_task(data)
        except httpx.TimeoutException:
            print(f"Timeout getting task {task_code} via URL")
            return None
        except Exception as e:
            print(f"Error getting task {task_code} via URL: {e}")
            return None

    def _map_to_task(self, data: dict[str, Any]) -> Task:
        """Map SWTR API response to Task model."""
        # Extract source_id (SWTR code)
        source_id = data.get("source_id", data.get("id", ""))

        # Parse deadline
        deadline = None
        if data.get("deadline"):
            try:
                deadline = datetime.fromisoformat(data["deadline"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Generate a stable ID from source_id if id is None
        task_id = data.get("id")
        if not task_id and source_id:
            # Create UUID from source_id string
            task_id = str(UUID(int=hash(source_id) & 0xFFFFFFFFFFFFFFFF))

        # Extract SWTR-specific source_data
        source_data = {
            'swtr_code': data.get("source_id"),
            'swtr_summary': data.get("title"),
            'swtr_space': data.get("space"),
            'workflow_status': data.get("status"),
            'priority': data.get("priority"),
            'assignee': data.get("assignee"),
            'created_at': data.get("created_at"),
            'updated_at': data.get("updated_at"),
        }

        return Task(
            id=str(UUID(task_id)) if task_id else "",
            source_id=source_id if source_id else "",
            title=data.get("title", ""),
            description=data.get("description", "") or "",
            status=data.get("status", "todo"),
            assignee=data.get("assignee"),
            deadline=deadline,
            source_url=data.get("source_url"),
            source=data.get("source"),
            created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")) if data.get("updated_at") else datetime.utcnow(),
            source_data=source_data,
            comments=[],
            attachments=[],
            url=data.get("source_url"),
        )
