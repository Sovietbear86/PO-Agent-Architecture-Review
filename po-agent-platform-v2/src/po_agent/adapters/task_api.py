"""Production-facing AS21 adapter over the existing task-api boundary.

The original PO Agent did not treat ``q`` as JQL.  It extracted task filters in
its own layer and sent the task-api the explicit query parameters that the
FastAPI endpoint actually understands (notably ``assignee``/``source``).  During
the Harness migration that contract was accidentally lost: the new adapter sent
``q=<JQL>`` even though ``/api/v1/tasks`` has no ``q`` parameter.  FastAPI simply
ignored it, so Harness searches could silently return the whole corpus.

This adapter restores the source contract while keeping the newer fail-closed
behaviour.  Supported AS21 facts are mapped into the canonical ``Task`` model,
and filters not natively supported by task-api (space/sprint/release/free text)
are applied deterministically after one bounded read.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from po_agent.domain.models import Attachment, StatusTransition, Task, TaskPriority

from .as21 import AS21Adapter
from .legacy_bridge import LegacyAS21Bridge, _parse_swtr_priority


class AS21SourceError(RuntimeError):
    """Base error for unavailable or malformed AS21 source data."""


class AS21SourceUnavailable(AS21SourceError):
    """The task-api transport cannot be reached or returned an error."""


class AS21CapabilityUnavailable(AS21SourceError):
    """The current task-api contract does not expose the requested source fact."""


class TaskApiAS21Adapter(AS21Adapter):
    """Async, fail-closed adapter for the existing task-api service.

    Important boundary rule: task-api's ``GET /api/v1/tasks`` supports explicit
    filters but does *not* implement JQL and does *not* consume a ``q`` query
    parameter.  JQL-like expressions accepted by this adapter are therefore a
    Harness-side convenience syntax only.
    """

    source_name = "task-api"
    source_facts = frozenset({"tasks", "sprints", "releases"})
    _SERVER_MAX_RESULTS = 10_000

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

    # ------------------------------------------------------------------
    # Mapping helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _scalar(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            value = value.strip()
            return value or None
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, dict):
            for key in ("code", "login", "accountId", "id", "value", "name", "displayName"):
                candidate = value.get(key)
                normalized = TaskApiAS21Adapter._scalar(candidate)
                if normalized:
                    return normalized
        return None

    @classmethod
    def _attribute(cls, source_data: dict[str, Any], *codes: str) -> Any:
        wanted = {code.casefold() for code in codes}
        for attr in source_data.get("swtr_attributes", []) or []:
            if not isinstance(attr, dict):
                continue
            names = {
                str(attr.get("code", "")).casefold(),
                str(attr.get("name", "")).casefold(),
            }
            if names & wanted:
                return attr.get("value")
        return None

    @classmethod
    def _first_source_value(cls, data: dict[str, Any], source_data: dict[str, Any], *keys: str) -> Any:
        for key in keys:
            if key in data and data.get(key) not in (None, "", [], {}):
                return data.get(key)
            if key in source_data and source_data.get(key) not in (None, "", [], {}):
                return source_data.get(key)
        return None

    @classmethod
    def _extract_sprint(cls, data: dict[str, Any], source_data: dict[str, Any]) -> Optional[str]:
        value = cls._first_source_value(data, source_data, "sprint", "sprint_id")
        if value is None:
            value = cls._attribute(source_data, "scrum_board_plugin_sprint", "sprint", "sprint_id")
        return cls._scalar(value)

    @classmethod
    def _extract_release(cls, data: dict[str, Any], source_data: dict[str, Any]) -> Optional[str]:
        value = cls._first_source_value(
            data,
            source_data,
            "release_id",
            "release",
            "fixVersion",
            "fix_version",
            "version",
        )
        if value is None:
            value = cls._attribute(source_data, "fixVersion", "fix_version", "release", "release_id")
        if isinstance(value, list) and value:
            value = value[0]
        return cls._scalar(value)

    @classmethod
    def _extract_space(cls, data: dict[str, Any], source_data: dict[str, Any], task: Task) -> Optional[str]:
        value = cls._first_source_value(data, source_data, "space", "swtr_space", "project", "project_key")
        normalized = cls._scalar(value)
        if normalized:
            return normalized.upper()
        if "-" in task.key:
            return task.key.split("-", 1)[0].upper()
        return None

    @classmethod
    def _extract_assignee_id(cls, data: dict[str, Any], source_data: dict[str, Any]) -> Optional[str]:
        value = cls._first_source_value(
            data,
            source_data,
            "assignee_id",
            "assignee_login",
            "assigneeId",
            "accountId",
        )
        if value is None:
            assignee = source_data.get("assignee")
            if isinstance(assignee, dict):
                value = assignee
        return cls._scalar(value)

    @classmethod
    def _extract_components(cls, data: dict[str, Any], source_data: dict[str, Any]) -> list[str]:
        raw = cls._first_source_value(data, source_data, "components") or []
        if not isinstance(raw, list):
            raw = [raw]
        result: list[str] = []
        for item in raw:
            value = cls._scalar(item)
            if value and value not in result:
                result.append(value)
        return result

    @classmethod
    def _extract_labels(cls, data: dict[str, Any], source_data: dict[str, Any]) -> list[str]:
        raw = cls._first_source_value(data, source_data, "labels")
        if raw is None:
            # Preserve the legacy behaviour as a fallback: some synced SWTR
            # deployments only expose attribute descriptors.
            raw = source_data.get("swtr_attributes", []) or []
        if not isinstance(raw, list):
            raw = [raw]
        result: list[str] = []
        for item in raw:
            value = cls._scalar(item)
            if value and value not in result:
                result.append(value)
        return result

    @classmethod
    def _map(cls, data: dict) -> Task | None:
        mapped = LegacyAS21Bridge._map_fastapi_task(None, data)
        if mapped is None:
            return None

        source_data = data.get("source_data") or {}
        if not isinstance(source_data, dict):
            raise AS21SourceError("task-api source_data must be an object")

        # The canonical model already has these fields; enrich the legacy map
        # rather than throwing away source facts during the Harness boundary.
        mapped.assignee_id = cls._extract_assignee_id(data, source_data)
        mapped.sprint_id = cls._extract_sprint(data, source_data)
        mapped.release_id = cls._extract_release(data, source_data)
        mapped.components = cls._extract_components(data, source_data)
        mapped.labels = cls._extract_labels(data, source_data)

        priority = cls._first_source_value(data, source_data, "priority")
        if isinstance(priority, dict):
            priority = priority.get("name") or priority.get("value") or priority.get("code")
        if isinstance(priority, str):
            mapped.priority = _parse_swtr_priority(priority)

        estimate = cls._first_source_value(data, source_data, "estimate_hours", "estimate")
        if estimate is not None:
            try:
                mapped.estimate_hours = float(estimate)
            except (TypeError, ValueError):
                pass

        return mapped

    # ------------------------------------------------------------------
    # Query contract
    # ------------------------------------------------------------------
    @staticmethod
    def _unquote(value: str) -> str:
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1].strip()
        return value

    @classmethod
    def _parse_query(cls, query: str) -> tuple[dict[str, str], Optional[str]]:
        """Parse the small JQL-like subset used by Harness capabilities.

        Returns ``(filters, free_text)``.  Unknown expressions are kept as free
        text so they cannot accidentally broaden a result set.
        """
        text = (query or "").strip()
        if not text:
            return {}, None

        filters: dict[str, str] = {}
        unmatched: list[str] = []
        parts = re.split(r"\s+AND\s+", text, flags=re.IGNORECASE)
        aliases = {
            "assignee": "assignee",
            "status": "status",
            "source": "source",
            "project": "space",
            "space": "space",
            "sprint": "sprint",
            "fixversion": "release",
            "fix_version": "release",
            "release": "release",
            "release_id": "release",
            "key": "key",
        }
        for part in parts:
            match = re.fullmatch(r"\s*([A-Za-z_][\w]*)\s*=\s*(.+?)\s*", part)
            if not match:
                unmatched.append(part.strip())
                continue
            field = aliases.get(match.group(1).casefold())
            if field is None:
                unmatched.append(part.strip())
                continue
            filters[field] = cls._unquote(match.group(2))

        if filters and not unmatched:
            return filters, None
        if not filters:
            return {}, text
        # Mixed supported + unsupported clauses are fail-closed: the supported
        # filters still narrow the corpus and the unknown part must also match.
        return filters, " ".join(item for item in unmatched if item)

    @staticmethod
    def _equals(left: Optional[str], right: str) -> bool:
        return bool(left) and left.strip().casefold() == right.strip().casefold()

    @classmethod
    def _matches(cls, task: Task, data: dict[str, Any], filters: dict[str, str], free_text: Optional[str]) -> bool:
        source_data = data.get("source_data") or {}

        if "assignee" in filters:
            identities = {value.casefold() for value in (task.assignee, task.assignee_id) if value}
            source_assignee = source_data.get("assignee")
            if isinstance(source_assignee, dict):
                for key in ("login", "accountId", "displayName", "name", "id"):
                    value = cls._scalar(source_assignee.get(key))
                    if value:
                        identities.add(value.casefold())
            if filters["assignee"].casefold() not in identities:
                return False

        if "status" in filters and task.status.value.casefold() != filters["status"].casefold():
            return False
        if "source" in filters and task.source.casefold() != filters["source"].casefold():
            return False
        if "space" in filters:
            space = cls._extract_space(data, source_data, task)
            if not cls._equals(space, filters["space"]):
                return False
        if "sprint" in filters and not cls._equals(task.sprint_id, filters["sprint"]):
            return False
        if "release" in filters and not cls._equals(task.release_id, filters["release"]):
            return False
        if "key" in filters and task.key.casefold() != filters["key"].casefold():
            return False

        if free_text:
            needle = free_text.casefold()
            haystack = "\n".join(
                value for value in (task.key, task.title, task.description or "", task.assignee or "", task.assignee_id or "") if value
            ).casefold()
            if needle not in haystack:
                return False

        return True

    async def _get_tasks(self, query: str, limit: int) -> list[Task]:
        filters, free_text = self._parse_query(query)

        # Use the old working contract where possible: explicit task-api
        # parameters, never a fictitious q/JQL parameter.
        params: dict[str, Any] = {}
        if "assignee" in filters:
            params["assignee"] = filters["assignee"]
        if "source" in filters:
            params["source"] = filters["source"]

        requires_local_filter = bool(free_text or set(filters) - {"assignee", "source"})
        params["limit"] = self._SERVER_MAX_RESULTS if requires_local_filter else min(limit, self._SERVER_MAX_RESULTS)

        try:
            response = await self._client.get("/api/v1/tasks", params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(f"task-api request failed: {type(exc).__name__}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api returned invalid JSON") from exc

        if not isinstance(payload, list):
            raise AS21SourceError("task-api /api/v1/tasks must return a JSON array")

        tasks: list[Task] = []
        for item in payload:
            if not isinstance(item, dict):
                raise AS21SourceError("task-api returned a non-object task item")
            try:
                mapped = self._map(item)
            except AS21SourceError:
                raise
            except Exception as exc:
                raise AS21SourceError("task-api task item cannot be mapped to canonical Task") from exc
            if mapped is None:
                raise AS21SourceError("task-api task item cannot be mapped to canonical Task")
            if self._matches(mapped, item, filters, free_text):
                tasks.append(mapped)
                if len(tasks) >= limit:
                    break
        return tasks

    async def get_task(self, task_key: str) -> Optional[Task]:
        normalized = task_key.upper().strip()
        tasks = await self._get_tasks(f"key = {normalized}", 1)
        return tasks[0] if tasks else None

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        del fields
        if max_results < 1:
            return []
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
