"""Hardened production AS21 adapter for real multi-filter Core-8 queries.

The cached `/api/v1/tasks` representation and the SWTR sprint-list facade are
not authoritative for relation membership on their own.  Sprint membership is
therefore proven by hydrating each candidate task from the individual SWTR unit
and comparing its real sprint attribute with the requested sprint.  A facade
must never be allowed to broaden a requested sprint silently.
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
    # Some real SWTR sprint responses include `complete_tasks: []` alongside a
    # populated `tasks.content`.  An empty completion projection is not an
    # authoritative empty sprint, so prefer it only when it actually has rows.
    complete = payload.get("complete_tasks")
    if isinstance(complete, list) and complete:
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


def _raw_relations(unit: dict[str, Any]) -> tuple[str | None, str | None]:
    attrs = unit.get("attributes") if isinstance(unit.get("attributes"), list) else []
    attr_map = {item.get("code"): item.get("value") for item in attrs if isinstance(item, dict) and item.get("code")}
    return _space_code(unit.get("space")), _identifier(attr_map.get("scrum_board_plugin_sprint"))


class HardenedProductionTaskApiAS21Adapter(ProductionTaskApiAS21Adapter):
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

    async def sprint_exists(self, sprint_id: str) -> bool:
        normalized = (sprint_id or "").strip()
        if not normalized:
            return False
        return bool(await self.get_sprint_tasks(normalized))

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
