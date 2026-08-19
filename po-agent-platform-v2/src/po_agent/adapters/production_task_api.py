"""Production AS21 adapter extensions over the proven Task API boundary."""
from __future__ import annotations

from typing import Any

import httpx

from po_agent.domain.models import Task

from .task_api import (
    AS21SourceError,
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
)


class ProductionTaskApiAS21Adapter(TaskApiAS21Adapter):
    """Task API adapter with proven sprint/release source facts.

    Core task mapping remains in TaskApiAS21Adapter. This subclass adds the
    live swtr-read calls needed by production sprint/release grounding while
    retaining canonical Task objects at the Harness boundary.
    """

    source_facts = frozenset({"tasks", "attachments", "sprints", "releases"})

    @staticmethod
    def _find_identifier(value: Any) -> str | None:
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if isinstance(value, dict):
            for key in ("code", "id", "sprintId", "sprint_id", "value"):
                candidate = value.get(key)
                if isinstance(candidate, (str, int)) and str(candidate).strip():
                    return str(candidate).strip()
            for nested in value.values():
                candidate = ProductionTaskApiAS21Adapter._find_identifier(nested)
                if candidate:
                    return candidate
        if isinstance(value, list):
            for item in value:
                candidate = ProductionTaskApiAS21Adapter._find_identifier(item)
                if candidate:
                    return candidate
        return None

    async def get_current_sprint_id(self, space: str) -> str | None:
        normalized = (space or "").upper().strip()
        if not normalized:
            return None
        try:
            response = await self._client.get(f"/api/v1/swtr-read/spaces/{normalized}/current-sprint")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            raise AS21SourceUnavailable(
                f"task-api current sprint read failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(
                f"task-api current sprint read failed: {type(exc).__name__}"
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api current sprint endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise AS21SourceError("task-api current sprint endpoint returned malformed payload")
        return self._find_identifier(payload.get("sprint"))

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None) -> list[Task]:
        normalized = (sprint_id or "").strip()
        if not normalized:
            return []
        try:
            response = await self._client.get(
                f"/api/v1/swtr-read/sprints/{normalized}/tasks",
                params={"complete": "true", "limit": 100, "max_pages": 100},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise AS21SourceUnavailable(
                f"task-api sprint task read failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(
                f"task-api sprint task read failed: {type(exc).__name__}"
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api sprint task endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise AS21SourceError("task-api sprint task endpoint returned malformed payload")

        # Current MCP advertises only sprint_id despite a paged response, so the
        # facade provides complete canonical cache rows explicitly in this field.
        rows = payload.get("complete_tasks")
        if not isinstance(rows, list):
            # If a future MCP supports real all-page traversal, use its content
            # only when it already matches the canonical Task API shape.
            tasks_payload = payload.get("tasks")
            rows = tasks_payload.get("content") if isinstance(tasks_payload, dict) else None
        if not isinstance(rows, list):
            raise AS21SourceError("task-api sprint task endpoint did not provide task rows")

        tasks: list[Task] = []
        for row in rows:
            if not isinstance(row, dict):
                raise AS21SourceError("task-api sprint task row is not an object")
            mapped = self._map(row)
            if mapped is None:
                continue
            if space and (mapped.project_space or "").casefold() != space.casefold():
                continue
            if (mapped.sprint_id or "").casefold() != normalized.casefold():
                continue
            tasks.append(mapped)
        return tasks

    async def search_versions(self, *, query: str | None = None, space: str | None = None) -> Any:
        params: dict[str, Any] = {"limit": 100}
        if query:
            params["query"] = query
        if space:
            params["space"] = space
        try:
            response = await self._client.get("/api/v1/swtr-read/versions", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(
                f"task-api release/version read failed: {type(exc).__name__}"
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api versions endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict) or "versions" not in payload:
            raise AS21SourceError("task-api versions endpoint returned malformed payload")
        return payload["versions"]
