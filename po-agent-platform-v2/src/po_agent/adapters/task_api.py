"""Production-facing AS21 adapter over the existing task-api boundary.

The local task-api is a bounded read facade, not a JQL endpoint. This adapter
translates the small deterministic query contract used by Harness into proven
source parameters plus local filtering over canonical Tasks. Unsupported query
clauses fail closed; they are never sent as ignored parameters.
"""
from __future__ import annotations

from datetime import datetime
import re
from pathlib import Path
from typing import Any, Optional

import httpx

from po_agent.domain.models import (
    Attachment,
    AttachmentType,
    StatusTransition,
    Task,
    get_status_category,
    normalize_task_status,
)
from .as21 import AS21Adapter


class AS21SourceError(RuntimeError):
    pass


class AS21SourceUnavailable(AS21SourceError):
    pass


class AS21CapabilityUnavailable(AS21SourceError):
    pass


def _parse_datetime(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _attributes(source_data: dict) -> dict[str, Any]:
    result: dict[str, Any] = {}
    raw = source_data.get("swtr_attributes", [])
    if not isinstance(raw, list):
        return result
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            result[item["code"]] = item.get("value")
    return result


def _user_identity(value: Any) -> tuple[str | None, str | None, str | None]:
    if not isinstance(value, dict):
        return None, None, None
    external_id = value.get("externalId") if isinstance(value.get("externalId"), str) else None
    login = value.get("login") if isinstance(value.get("login"), str) else None
    parts = [value.get("lastName"), value.get("firstName"), value.get("middleName")]
    display = " ".join(p.strip() for p in parts if isinstance(p, str) and p.strip()) or None
    return display, external_id, login


def _identifier(value: Any) -> str | None:
    if isinstance(value, (str, int)):
        text = str(value).strip()
        return text or None
    if isinstance(value, dict):
        for key in ("code", "id", "externalId", "value", "name"):
            candidate = value.get(key)
            if isinstance(candidate, (str, int)) and str(candidate).strip():
                return str(candidate).strip()
        return None
    if isinstance(value, list):
        for item in value:
            candidate = _identifier(item)
            if candidate:
                return candidate
    return None


def _query_value(raw: str) -> str:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1].strip()
    return value


def _parse_query(query: str) -> tuple[dict[str, str], str | None]:
    text = (query or "").strip()
    if not text:
        return {}, None
    if "=" not in text:
        return {}, text

    aliases = {
        "assignee": "assignee",
        "assigned_to": "assignee",
        "member_login": "assignee",
        "status": "status",
        "project": "project_space",
        "space": "project_space",
        "sprint": "sprint_id",
        "fixversion": "release_id",
        "release": "release_id",
        "key": "key",
        "id": "key",
        "source": "source",
    }
    filters: dict[str, str] = {}
    clauses = re.split(r"\s+AND\s+", text, flags=re.IGNORECASE)
    for clause in clauses:
        match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*", clause)
        if not match:
            raise AS21CapabilityUnavailable(f"unsupported AS21 search clause: {clause!r}")
        source_field = match.group(1).lower()
        field = aliases.get(source_field)
        if field is None:
            raise AS21CapabilityUnavailable(f"unsupported AS21 search field: {match.group(1)}")
        value = _query_value(match.group(2))
        if not value:
            raise AS21CapabilityUnavailable(f"empty AS21 search value for {match.group(1)}")
        if field in filters and filters[field].casefold() != value.casefold():
            return {"__impossible__": "1"}, None
        filters[field] = value
    return filters, None


def _equals(value: str | None, expected: str) -> bool:
    return isinstance(value, str) and value.casefold() == expected.casefold()


def _task_matches(task: Task, filters: dict[str, str], free_text: str | None) -> bool:
    if "__impossible__" in filters:
        return False
    if "key" in filters and not _equals(task.key, filters["key"]):
        return False
    if "source" in filters and not _equals(task.source, filters["source"]):
        return False
    if "project_space" in filters and not _equals(task.project_space, filters["project_space"]):
        return False
    if "sprint_id" in filters and not _equals(task.sprint_id, filters["sprint_id"]):
        return False
    if "release_id" in filters and not _equals(task.release_id, filters["release_id"]):
        return False
    if "assignee" in filters:
        expected = filters["assignee"].casefold()
        candidates = (task.assignee_id, task.assignee_login, task.assignee)
        if not any(isinstance(v, str) and v.casefold() == expected for v in candidates):
            return False
    if "status" in filters:
        expected_raw = filters["status"]
        expected_status = normalize_task_status(expected_raw)
        if expected_status.value != "Unknown":
            if task.status != expected_status:
                return False
        elif not _equals(task.status_raw, expected_raw):
            return False
    if free_text:
        needle = free_text.casefold()
        haystack = "\n".join(v for v in (task.key, task.title, task.description or "") if v).casefold()
        if needle not in haystack:
            return False
    return True


def _attachment_type(name: str, content_type: str | None) -> AttachmentType:
    mime = (content_type or "").casefold()
    suffix = Path(name).suffix.casefold()
    if suffix in {".xlsx", ".xls", ".xlsm", ".xlsb", ".csv", ".ods"} or "spreadsheet" in mime or "excel" in mime:
        return AttachmentType.EXCEL
    if suffix in {".doc", ".docx", ".docm", ".rtf", ".odt"} or "word" in mime or "opendocument.text" in mime:
        return AttachmentType.WORD
    if suffix == ".pdf" or mime == "application/pdf":
        return AttachmentType.PDF
    if suffix == ".msg" or "outlook" in mime:
        return AttachmentType.MSG
    if mime.startswith("image/") or suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return AttachmentType.IMAGE
    if mime.startswith("text/") or suffix in {".txt", ".md", ".json", ".xml"}:
        return AttachmentType.TEXT
    return AttachmentType.OTHER


def _attachment_fields(raw: dict[str, Any]) -> tuple[Any, Any, Any, Any, Any]:
    """Normalize both legacy facade metadata and the real MCP get_unit_files shape."""
    file_path = raw.get("filePathParsedDto") if isinstance(raw.get("filePathParsedDto"), dict) else {}
    metadata = raw.get("fileMetadataDto") if isinstance(raw.get("fileMetadataDto"), dict) else {}
    file_id = raw.get("fileId") or raw.get("id")
    name = raw.get("fileName") or file_path.get("fileName") or raw.get("name")
    size = metadata.get("contentLength") if isinstance(metadata.get("contentLength"), int) else raw.get("size")
    created = raw.get("createdAt") or raw.get("created")
    content_type = metadata.get("contentType") if isinstance(metadata.get("contentType"), str) else raw.get("contentType")
    return file_id, name, size, created, content_type


class TaskApiAS21Adapter(AS21Adapter):
    source_name = "task-api"
    # Real AS21 QA (A3 canonical retest) proved task and attachment metadata reads.
    source_facts = frozenset({"tasks", "attachments"})
    _scan_limit = 10000

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
        source_id = data.get("source_id") or data.get("id")
        if not isinstance(source_id, str) or not source_id:
            return None
        source_data = data.get("source_data") if isinstance(data.get("source_data"), dict) else {}
        attrs = _attributes(source_data)
        status_raw = source_data.get("workflow_status") or data.get("status") or ""
        status = normalize_task_status(str(status_raw))
        display, external_id, login = _user_identity(attrs.get("assigned_to"))
        assignee = data.get("assignee") if isinstance(data.get("assignee"), str) else display
        title = data.get("title")
        if not isinstance(title, str) or not title.strip():
            return None
        created = _parse_datetime(data.get("created_at")) or datetime.now()
        updated = _parse_datetime(data.get("updated_at")) or created
        project_space = source_data.get("swtr_space") if isinstance(source_data.get("swtr_space"), str) else None
        sprint_id = _identifier(data.get("sprint")) or _identifier(attrs.get("scrum_board_plugin_sprint"))
        release_id = _identifier(attrs.get("fix_version_s"))
        return Task(
            key=source_id,
            id=source_id,
            title=title,
            description=data.get("description"),
            status=status,
            status_raw=str(status_raw) or None,
            status_category=get_status_category(status),
            created_at=created,
            updated_at=updated,
            due_date=_parse_datetime(data.get("deadline")),
            assignee=assignee,
            assignee_id=external_id,
            assignee_login=login,
            project_space=project_space,
            sprint_id=sprint_id,
            release_id=release_id,
            source=data.get("source", "swtr") or "swtr",
            source_url=data.get("source_url"),
            source_data=source_data,
        )

    async def _fetch_tasks(self, *, limit: int, offset: int = 0, source: str | None = None) -> list[Task]:
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if source:
            params["source"] = source
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
            except Exception as exc:
                raise AS21SourceError("task-api task item cannot be mapped to canonical Task") from exc
            if mapped is None:
                raise AS21SourceError("task-api task item cannot be mapped to canonical Task")
            tasks.append(mapped)
        return tasks

    async def get_task(self, task_key: str) -> Optional[Task]:
        normalized = task_key.upper().strip()
        if not re.fullmatch(r"[A-Z]+-\d+", normalized):
            return None
        tasks = await self._fetch_tasks(limit=self._scan_limit, source="swtr")
        task = next((item for item in tasks if item.key.upper() == normalized), None)
        if task is None:
            return None
        # Exact task reads are the canonical rich-read boundary: attach proven
        # metadata here so task-level skills can see Office/PDF/MSG attachments
        # without retaining a live AS21 object or doing hidden network fallback.
        attachments = await self.get_attachment_metadata(normalized)
        return task.model_copy(update={"attachments": attachments})

    async def search_tasks(
        self,
        jql: str,
        max_results: int = 50,
        fields: Optional[list[str]] = None,
    ) -> list[Task]:
        del fields
        if max_results < 0:
            raise ValueError("max_results must be >= 0")
        if max_results == 0:
            return []
        filters, free_text = _parse_query(jql)
        if "__impossible__" in filters:
            return []
        source_filter = filters.get("source")
        needs_local_filtering = bool(filters) or bool(free_text)
        fetch_limit = self._scan_limit if needs_local_filtering else min(max_results, self._scan_limit)
        tasks = await self._fetch_tasks(limit=fetch_limit, source=source_filter)
        result = [task for task in tasks if _task_matches(task, filters, free_text)]
        return result[:max_results]

    async def get_sprint_tasks(self, sprint_id: str, space: Optional[str] = None) -> list[Task]:
        query = f"sprint = {sprint_id}" if not space else f"project = {space} AND sprint = {sprint_id}"
        return await self.search_tasks(query, max_results=self._scan_limit)

    async def get_release_tasks(self, release_id: str, space: Optional[str] = None) -> list[Task]:
        query = f"release = {release_id}" if not space else f"project = {space} AND release = {release_id}"
        return await self.search_tasks(query, max_results=self._scan_limit)

    async def get_task_history(self, task_key: str) -> list[StatusTransition]:
        raise AS21CapabilityUnavailable(f"task-api does not expose proven status-transition history for {task_key}")

    async def get_attachment_metadata(
        self,
        task_key: str,
        attachment_id: Optional[str] = None,
    ) -> list[Attachment]:
        normalized = task_key.upper().strip()
        if not re.fullmatch(r"[A-Z]+-\d+", normalized):
            return []
        try:
            response = await self._client.get(f"/api/v1/swtr-read/tasks/{normalized}/files")
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return []
            raise AS21SourceUnavailable(f"task-api SWTR attachment read failed: HTTP {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise AS21SourceUnavailable(f"task-api SWTR attachment read failed: {type(exc).__name__}") from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise AS21SourceError("task-api SWTR attachment endpoint returned invalid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("files"), list):
            raise AS21SourceError("task-api SWTR attachment endpoint returned malformed payload")

        attachments: list[Attachment] = []
        for raw in payload["files"]:
            if not isinstance(raw, dict):
                raise AS21SourceError("SWTR attachment metadata item is not an object")
            file_id, name, size, created_raw, content_type = _attachment_fields(raw)
            created = _parse_datetime(created_raw)
            if not isinstance(file_id, str) or not file_id or not isinstance(name, str) or not name:
                raise AS21SourceError("SWTR attachment metadata misses id/name")
            if not isinstance(size, int) or size < 0:
                raise AS21SourceError("SWTR attachment metadata misses valid size")
            if created is None:
                raise AS21SourceError("SWTR attachment metadata misses valid created timestamp")
            if attachment_id is not None and file_id != attachment_id:
                continue
            attachments.append(
                Attachment(
                    id=file_id,
                    name=name,
                    type=_attachment_type(name, content_type if isinstance(content_type, str) else None),
                    size_bytes=size,
                    created_at=created,
                    url=None,
                )
            )
        return attachments

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()
