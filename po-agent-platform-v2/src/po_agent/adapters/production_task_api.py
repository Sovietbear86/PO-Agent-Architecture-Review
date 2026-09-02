"""Production AS21 adapter extensions over the proven Task API boundary."""
from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from po_agent.domain.models import Task

from .task_api import (
    AS21SourceError,
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
    _parse_query,
    _task_matches,
)


class ProductionTaskApiAS21Adapter(TaskApiAS21Adapter):
    """Task API adapter with proven sprint/release/history source facts.

    Core task mapping remains in TaskApiAS21Adapter. This subclass adds live
    swtr-read calls needed by production sprint/release grounding. Assignee
    searches are also routed to the live MCP-SWTR facade so they never depend on
    a synchronized/local task cache.
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

    async def get_task(self, task_key: str) -> Optional[Task]:
        """Point-read an exact task from REAL SWTR instead of scanning local task cache.

        `/api/v1/swtr-read/tasks/{code}` wraps MCP `read_unit` as
        `{task_code, unit}`.  The canonical mapper expects the Task API facade
        shape, so normalize the live unit at this boundary and preserve the raw
        unit as `source_data`.  A real 404/not-found is returned as ``None``;
        transport/source failures remain typed source errors.
        """
        normalized = (task_key or "").upper().strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-\d+", normalized):
            return None
        try:
            response = await self._client.get(f"/api/v1/swtr-read/tasks/{normalized}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            if exc.response.status_code in (502, 503):
                raise AS21SourceUnavailable(
                    f"task-api exact task read unavailable: HTTP {exc.response.status_code}"
                ) from exc
            raise AS21SourceError(
                f"task-api exact task read failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(
                f"task-api exact task read failed: {type(exc).__name__}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api exact task endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise AS21SourceError("task-api exact task endpoint returned malformed payload")

        unit = payload.get("unit")
        if not isinstance(unit, dict):
            raise AS21SourceError("task-api exact task endpoint did not provide a unit object")

        source_id = unit.get("code") or payload.get("task_code")
        if not isinstance(source_id, str) or source_id.upper().strip() != normalized:
            raise AS21SourceError("task-api exact task endpoint returned a mismatched task code")

        title = unit.get("summary") or unit.get("title") or unit.get("name")
        if not isinstance(title, str) or not title.strip():
            raise AS21SourceError("task-api exact task endpoint returned a task without title")

        row: dict[str, Any] = {
            "source_id": normalized,
            "title": title,
            "description": unit.get("description"),
            "status": unit.get("workflow_status") or unit.get("status") or "",
            "created_at": unit.get("created_at") or unit.get("createdAt") or unit.get("created"),
            "updated_at": unit.get("updated_at") or unit.get("updatedAt") or unit.get("updated"),
            "deadline": unit.get("deadline") or unit.get("due_date") or unit.get("dueDate"),
            "source": "swtr",
            "source_data": unit,
        }
        mapped = self._map(row)
        if mapped is None:
            raise AS21SourceError("live SWTR task cannot be mapped to canonical Task")
        attachments = await self.get_attachment_metadata(normalized)
        return mapped.model_copy(update={"attachments": attachments})

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

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        """Use the live AS21 TQL route for assignee searches.

        The base adapter scans `/api/v1/tasks`, which is a local/cache facade.
        That is unsuitable for member queries because stale or missing
        `assigned_to` metadata produces false zero-task answers. The live route
        resolves the user in AS21 and executes server-side `assigned_to` TQL.
        Other query shapes keep the existing proven behavior.
        """
        del fields
        if max_results < 0:
            raise ValueError("max_results must be >= 0")
        if max_results == 0:
            return []

        filters, free_text = _parse_query(jql)
        assignee = filters.get("assignee")
        if not assignee:
            return await super().search_tasks(jql, max_results=max_results)

        params: dict[str, Any] = {
            "assignee": assignee,
            "limit": 100,
            "max_pages": 100,
        }
        project_space = filters.get("project_space")
        if project_space:
            params["space"] = project_space

        try:
            response = await self._client.get("/api/v1/swtr-read/assignee-tasks", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise AS21SourceUnavailable(
                f"task-api live assignee read failed: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(
                f"task-api live assignee read failed: {type(exc).__name__}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api live assignee endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("tasks"), list):
            raise AS21SourceError("task-api live assignee endpoint returned malformed payload")

        tasks: list[Task] = []
        for row in payload["tasks"]:
            if not isinstance(row, dict):
                raise AS21SourceError("task-api live assignee row is not an object")
            mapped = self._map(row)
            if mapped is None:
                continue
            if _task_matches(mapped, filters, free_text):
                tasks.append(mapped)
        return tasks[:max_results]

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
