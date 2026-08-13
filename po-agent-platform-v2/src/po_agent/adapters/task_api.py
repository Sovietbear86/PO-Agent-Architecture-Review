"""Production-facing AS21 adapter over the existing task-api boundary.

Unlike the legacy bridge this adapter is asynchronous and fail-closed: transport
or protocol errors are raised, never converted to an empty task list. This is
critical for PO metrics because "source unavailable" must not look like "0 work".
"""
from __future__ import annotations

from typing import Optional

import httpx

from po_agent.domain.models import Attachment, StatusTransition, Task

from .as21 import AS21Adapter
from .legacy_bridge import LegacyAS21Bridge


class AS21SourceError(RuntimeError):
    """Base error for unavailable or malformed AS21 source data."""


class AS21SourceUnavailable(AS21SourceError):
    """The task-api transport cannot be reached or returned an error."""


class AS21CapabilityUnavailable(AS21SourceError):
    """The current task-api contract does not expose the requested source fact."""


class TaskApiAS21Adapter(AS21Adapter):
    """Async, fail-closed adapter for the existing task-api service."""

    def __init__(
        self,
        base_url: str = "http://localhost:8003",
        *,
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=True,
        )

    @staticmethod
    def _map(data: dict) -> Task | None:
        # Reuse the already regression-tested canonical mapping while the
        # transport is strangled away from LegacyAS21Bridge.
        return LegacyAS21Bridge._map_fastapi_task(None, data)

    async def _get_tasks(self, query: str, limit: int) -> list[Task]:
        try:
            response = await self._client.get("/api/v1/tasks", params={"q": query, "limit": limit})
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise AS21SourceUnavailable(f"task-api request failed: {type(exc).__name__}") from exc

        if not isinstance(payload, list):
            raise AS21SourceError("task-api /api/v1/tasks must return a JSON array")

        tasks: list[Task] = []
        for item in payload:
            if not isinstance(item, dict):
                raise AS21SourceError("task-api returned a non-object task item")
            mapped = self._map(item)
            if mapped is not None:
                tasks.append(mapped)
        return tasks

    async def get_task(self, task_key: str) -> Optional[Task]:
        normalized = task_key.upper().strip()
        tasks = await self._get_tasks(normalized, 10)
        for task in tasks:
            if task.key.upper() == normalized:
                return task
        return None

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        del fields  # task-api controls the canonical response shape.
        return await self._get_tasks(jql, max_results)

    async def get_sprint_tasks(self, sprint_id: str, space: Optional[str] = None) -> list[Task]:
        query = f"sprint = {sprint_id}" if not space else f"project = {space} AND sprint = {sprint_id}"
        return await self.search_tasks(query)

    async def get_release_tasks(self, release_id: str, space: Optional[str] = None) -> list[Task]:
        query = f"fixVersion = {release_id}" if not space else f"project = {space} AND fixVersion = {release_id}"
        return await self.search_tasks(query)

    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        raise AS21CapabilityUnavailable(
            f"task-api does not expose status history for {task_key}; do not calculate history metrics from current state"
        )

    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        raise AS21CapabilityUnavailable(
            f"task-api does not expose attachment metadata for {task_key}; empty attachments would be ambiguous"
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
