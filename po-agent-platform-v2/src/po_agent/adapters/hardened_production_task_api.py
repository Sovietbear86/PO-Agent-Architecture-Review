"""Hardened production AS21 adapter for real multi-filter Core-8 queries.

This layer repairs a contract gap exposed by exhaustive live-AS21 testing:
the cached `/api/v1/tasks` representation is not guaranteed to retain space or
sprint relations even though MCP-SWTR can prove them.  We therefore join the
cached canonical task facts with live read-only SWTR evidence instead of
interpreting missing relation fields as an empty result.
"""
from __future__ import annotations

import asyncio
import re
from datetime import datetime
from typing import Any

import httpx

from po_agent.domain.models import Task, get_status_category, normalize_task_status

from .production_task_api import ProductionTaskApiAS21Adapter
from .task_api import (
    AS21SourceError,
    AS21SourceUnavailable,
    TaskApiAS21Adapter,
    _attributes,
    _identifier,
    _parse_datetime,
    _parse_query,
    _task_matches,
    _user_identity,
)

_TASK_CODE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$", re.I)


def _unit_from_payload(value: Any) -> dict[str, Any] | None:
    """Find a real SWTR unit object without guessing from unrelated dictionaries."""
    if isinstance(value, dict):
        code = value.get("code")
        if isinstance(code, str) and _TASK_CODE.fullmatch(code.strip()):
            return value
        for key in ("unit", "content", "task", "data"):
            if key in value:
                found = _unit_from_payload(value[key])
                if found is not None:
                    return found
    elif isinstance(value, list):
        for item in value:
            found = _unit_from_payload(item)
            if found is not None:
                return found
    return None


def _task_code_from_row(row: Any) -> str | None:
    unit = _unit_from_payload(row)
    if unit is not None:
        return str(unit["code"]).upper().strip()
    if isinstance(row, dict):
        for key in ("source_id", "key", "id"):
            value = row.get(key)
            if isinstance(value, str) and _TASK_CODE.fullmatch(value.upper().strip()):
                return value.upper().strip()
    return None


def _sprint_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    complete = payload.get("complete_tasks")
    if isinstance(complete, list):
        return [row for row in complete if isinstance(row, dict)]
    tasks = payload.get("tasks")
    if isinstance(tasks, dict) and isinstance(tasks.get("content"), list):
        return [row for row in tasks["content"] if isinstance(row, dict)]
    if isinstance(tasks, list):
        return [row for row in tasks if isinstance(row, dict)]
    return []


def _space_code(value: Any) -> str | None:
    if isinstance(value, str):
        return value.strip().upper() or None
    if isinstance(value, dict):
        for key in ("code", "id", "value", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip().upper()
    return None


class HardenedProductionTaskApiAS21Adapter(ProductionTaskApiAS21Adapter):
    """Production adapter that treats missing cached relations as unknown, never empty."""

    source_facts = frozenset({"tasks", "attachments", "sprints", "releases", "spaces"})

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._raw_unit_cache: dict[str, dict[str, Any] | None] = {}
        self._relation_lock = asyncio.Lock()

    async def _read_raw_unit(self, task_key: str) -> dict[str, Any] | None:
        key = task_key.upper().strip()
        if key in self._raw_unit_cache:
            return self._raw_unit_cache[key]
        try:
            response = await self._client.get(f"/api/v1/swtr-read/tasks/{key}")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                self._raw_unit_cache[key] = None
                return None
            raise AS21SourceUnavailable(f"raw SWTR task read failed: HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(f"raw SWTR task read failed: {type(exc).__name__}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("raw SWTR task endpoint returned invalid JSON") from exc
        unit = _unit_from_payload(payload.get("unit") if isinstance(payload, dict) else payload)
        self._raw_unit_cache[key] = unit
        return unit

    @staticmethod
    def _map_raw_unit(unit: dict[str, Any], *, sprint_id: str | None = None, space: str | None = None) -> Task | None:
        code = unit.get("code")
        if not isinstance(code, str) or not _TASK_CODE.fullmatch(code.upper().strip()):
            return None
        attrs_list = unit.get("attributes") if isinstance(unit.get("attributes"), list) else []
        source_data = {
            "swtr_code": code,
            "swtr_space": _space_code(unit.get("space")) or (space.upper() if space else None),
            "workflow_status": unit.get("workflow_status"),
            "swtr_attributes": attrs_list,
            "sprint_id": sprint_id,
        }
        attrs = _attributes(source_data)
        status_value = attrs.get("workflow_status") or unit.get("workflow_status") or ""
        if isinstance(status_value, dict):
            status_raw = status_value.get("code") or status_value.get("name") or ""
        else:
            status_raw = str(status_value or "")
        status = normalize_task_status(status_raw)
        display, external_id, login = _user_identity(attrs.get("assigned_to"))
        title = unit.get("summary") or unit.get("title")
        if not isinstance(title, str) or not title.strip():
            return None
        created = _parse_datetime(unit.get("createdAt")) or datetime.now()
        updated = _parse_datetime(unit.get("updatedAt")) or created
        grounded_sprint = sprint_id or _identifier(attrs.get("scrum_board_plugin_sprint"))
        release_id = _identifier(attrs.get("fix_version_s"))
        return Task(
            key=code.upper().strip(),
            id=code.upper().strip(),
            title=title,
            description=unit.get("description") if isinstance(unit.get("description"), str) else None,
            status=status,
            status_raw=status_raw or None,
            status_category=get_status_category(status),
            created_at=created,
            updated_at=updated,
            assignee=display,
            assignee_id=external_id,
            assignee_login=login,
            project_space=source_data["swtr_space"],
            sprint_id=grounded_sprint,
            release_id=release_id,
            source="swtr",
            source_data=source_data,
        )

    async def _hydrate_relation(self, task: Task) -> Task:
        if task.project_space and task.sprint_id:
            return task
        unit = await self._read_raw_unit(task.key)
        if unit is None:
            return task
        attrs = unit.get("attributes") if isinstance(unit.get("attributes"), list) else []
        attr_map = {item.get("code"): item.get("value") for item in attrs if isinstance(item, dict) and item.get("code")}
        project_space = task.project_space or _space_code(unit.get("space"))
        sprint_id = task.sprint_id or _identifier(attr_map.get("scrum_board_plugin_sprint"))
        source_data = dict(task.source_data)
        if project_space:
            source_data["swtr_space"] = project_space
        if sprint_id:
            source_data["sprint_id"] = sprint_id
        if attrs and not source_data.get("swtr_attributes"):
            source_data["swtr_attributes"] = attrs
        return task.model_copy(update={"project_space": project_space, "sprint_id": sprint_id, "source_data": source_data})

    async def _hydrate_relations(self, tasks: list[Task]) -> list[Task]:
        semaphore = asyncio.Semaphore(12)

        async def hydrate(task: Task) -> Task:
            async with semaphore:
                return await self._hydrate_relation(task)

        return list(await asyncio.gather(*(hydrate(task) for task in tasks))) if tasks else []

    async def get_sprint_tasks(self, sprint_id: str, space: str | None = None) -> list[Task]:
        normalized = (sprint_id or "").strip()
        if not normalized:
            return []
        params = {"complete": "true", "limit": 100, "max_pages": 500}
        try:
            response = await self._client.get(f"/api/v1/swtr-read/sprints/{normalized}/tasks", params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise AS21SourceUnavailable(f"task-api sprint task read failed: HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(f"task-api sprint task read failed: {type(exc).__name__}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api sprint task endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict):
            raise AS21SourceError("task-api sprint task endpoint returned malformed payload")
        if payload.get("complete") is False:
            raise AS21SourceError("task-api sprint task endpoint returned an incomplete corpus")

        rows = _sprint_rows(payload)
        codes = []
        seen: set[str] = set()
        for row in rows:
            code = _task_code_from_row(row)
            if code and code not in seen:
                seen.add(code)
                codes.append(code)
        if rows and not codes:
            raise AS21SourceError("live sprint rows do not expose canonical task codes")

        cached = await TaskApiAS21Adapter.search_tasks(self, "", max_results=self._scan_limit)
        cached_by_key = {task.key.upper(): task for task in cached}
        result: list[Task] = []
        normalized_space = space.upper().strip() if space else None
        for code in codes:
            task = cached_by_key.get(code)
            if task is None:
                unit = _unit_from_payload(next((row for row in rows if _task_code_from_row(row) == code), {}))
                task = self._map_raw_unit(unit, sprint_id=normalized, space=normalized_space) if unit else None
                if task is None:
                    raw = await self._read_raw_unit(code)
                    task = self._map_raw_unit(raw, sprint_id=normalized, space=normalized_space) if raw else None
            if task is None:
                continue
            task_space = task.project_space or normalized_space
            if normalized_space and task_space and task_space.casefold() != normalized_space.casefold():
                continue
            result.append(task.model_copy(update={"sprint_id": normalized, "project_space": task_space}))
        return result

    async def search_tasks(self, jql: str, max_results: int = 50, fields: list[str] | None = None) -> list[Task]:
        filters, free_text = _parse_query(jql)
        if "__impossible__" in filters:
            return []
        project = filters.get("project_space")
        sprint = filters.get("sprint_id")
        if not project and not sprint:
            return await super().search_tasks(jql, max_results=max_results, fields=fields)

        remaining = dict(filters)
        remaining.pop("project_space", None)
        remaining.pop("sprint_id", None)

        if sprint:
            candidates = await self.get_sprint_tasks(sprint, space=project)
        else:
            # Narrow by every proven cached filter first, then hydrate the missing
            # relation from raw SWTR. Missing project in cache is UNKNOWN, not NO.
            cached_filters = {k: v for k, v in remaining.items() if k in {"assignee", "status", "release_id", "key", "source"}}
            query = " AND ".join(f"{k if k != 'release_id' else 'release'} = {v}" for k, v in cached_filters.items())
            candidates = await TaskApiAS21Adapter.search_tasks(self, query, max_results=self._scan_limit, fields=fields)
            candidates = await self._hydrate_relations(candidates)

        final_filters = dict(remaining)
        if project:
            final_filters["project_space"] = project
        result = [task for task in candidates if _task_matches(task, final_filters, free_text)]
        return result[:max_results]
