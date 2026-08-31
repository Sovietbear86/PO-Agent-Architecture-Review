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
    """Task API adapter with proven sprint/release/history source facts.

    Core task mapping remains in TaskApiAS21Adapter. This subclass adds live
    swtr-read calls needed by production sprint/release grounding. If the MCP
    version-search tool itself is unavailable, release identifiers already
    proven on canonical real AS21 tasks remain a valid read-only grounding
    source; the fallback is explicit in each returned record.
    """

    source_facts = frozenset({"tasks", "attachments", "history", "sprints", "releases"})

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

        rows = payload.get("complete_tasks")
        if not isinstance(rows, list):
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

    async def _task_backed_versions(self, *, query: str | None = None, space: str | None = None) -> list[dict[str, Any]]:
        tasks = await self.search_tasks("", max_results=self._scan_limit)
        wanted_query = (query or "").strip().casefold()
        wanted_space = (space or "").strip().casefold()
        by_id: dict[str, dict[str, Any]] = {}
        for task in tasks:
            release_id = (task.release_id or "").strip()
            if not release_id:
                continue
            if wanted_space and (task.project_space or "").casefold() != wanted_space:
                continue
            if wanted_query and wanted_query not in release_id.casefold():
                continue
            item = by_id.setdefault(
                release_id,
                {
                    "id": release_id,
                    "code": release_id,
                    "name": release_id,
                    "source": "canonical_as21_task.fix_version_s",
                    "evidence_task_keys": [],
                    "fallback": True,
                },
            )
            item["evidence_task_keys"].append(task.key)
        return [by_id[key] for key in sorted(by_id)]

    async def search_versions(self, *, query: str | None = None, space: str | None = None) -> Any:
        params: dict[str, Any] = {"limit": 100}
        if query:
            params["query"] = query
        if space:
            params["space"] = space
        try:
            response = await self._client.get("/api/v1/swtr-read/versions", params=params)
            response.raise_for_status()
        except httpx.HTTPError:
            return await self._task_backed_versions(query=query, space=space)
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api versions endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict) or "versions" not in payload:
            raise AS21SourceError("task-api versions endpoint returned malformed payload")
        return payload["versions"]