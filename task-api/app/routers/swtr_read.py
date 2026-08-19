"""Read-only rich SWTR facade for facts not exposed by the cached task list.

New Harness read capabilities use the live MCP-SWTR SSE transport through
SWTRMCPClient. The historical SWTRSyncService subprocess/stdin bridge is not
used here because the live MCP server is an SSE service.
"""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.swtr_mcp_client import (
    SWTRMCPClient,
    SWTRMCPProtocolError,
    SWTRMCPUnavailable,
)

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])
_TASK_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def _parse_tool_content(content: list[dict[str, Any]]) -> Any:
    decoded: list[Any] = []
    for item in content:
        if not isinstance(item, dict) or item.get("type") != "text":
            continue
        text = item.get("text")
        if not isinstance(text, str):
            continue
        try:
            decoded.append(json.loads(text))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=502, detail="SWTR MCP returned invalid JSON") from exc

    if not decoded:
        raise HTTPException(status_code=502, detail="SWTR MCP returned no JSON payload")
    if len(decoded) == 1:
        return decoded[0]
    return decoded


def _extract_files(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("content", "files"):
            files = payload.get(key)
            if files is None:
                continue
            if not isinstance(files, list):
                raise HTTPException(status_code=502, detail=f"SWTR file metadata field {key!r} is not a list")
            if not all(isinstance(item, dict) for item in files):
                raise HTTPException(status_code=502, detail="SWTR file metadata contains non-object item")
            return files
        if any(key in payload for key in ("fileId", "id")) and any(key in payload for key in ("fileName", "name")):
            return [payload]
    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise HTTPException(status_code=502, detail="SWTR file metadata contains non-object item")
        return payload
    raise HTTPException(status_code=502, detail="SWTR file metadata shape is unsupported")


def _transport_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SWTRMCPUnavailable):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


def _page_meta(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"has_next": False, "page": None, "page_size": None, "total": None}
    has_next = payload.get("hasNext")
    if has_next is None:
        has_next = payload.get("has_next")
    page = payload.get("pageNumber", payload.get("page_number", payload.get("page")))
    size = payload.get("pageSize", payload.get("page_size", payload.get("size")))
    total = payload.get("totalElements", payload.get("total_elements", payload.get("total")))
    return {"has_next": bool(has_next), "page": page, "page_size": size, "total": total}


def _page_content(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        content = payload.get("content")
        if isinstance(content, list) and all(isinstance(item, dict) for item in content):
            return content
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    return []


def _source_task_code(item: dict[str, Any]) -> str | None:
    for key in ("code", "source_id", "key", "id"):
        value = item.get(key)
        if isinstance(value, str) and _TASK_CODE_RE.fullmatch(value.upper().strip()):
            return value.upper().strip()
    return None


def _cached_complete_sprint_tasks(sprint_id: str) -> list[dict[str, Any]]:
    """Return complete canonical SWTR cache rows for a sprint.

    This is an explicit completeness fallback for MCP installations whose
    get_sprint_tasks schema exposes only sprint_id even though the response is
    paginated. The Task API cache is the already-proven primary task source; the
    response labels this fallback rather than pretending it is another MCP page.
    """
    from app.routers.tasks import get_task_service
    from app.schemas.task import task_to_response

    service = get_task_service()
    rows: list[dict[str, Any]] = []
    for task in service.get_tasks(source="swtr", limit=10000, offset=0):
        response = task_to_response(task)
        if isinstance(response.sprint, str) and response.sprint.casefold() == sprint_id.casefold():
            rows.append(response.model_dump(mode="json"))
    return rows


@router.get("/health")
async def swtr_read_health():
    client = SWTRMCPClient()
    try:
        tools = await client.list_tools()
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    return {
        "status": "connected",
        "transport": "sse",
        "tool_count": len(tools),
        "read_unit": "read_unit" in tools,
        "get_unit_files": "get_unit_files" in tools,
        "get_sprint_tasks": "get_sprint_tasks" in tools,
        "search_versions": "search_versions" in tools,
    }


@router.get("/tasks/{task_code}")
async def get_task_raw(task_code: str):
    normalized = task_code.upper().strip()
    if not _TASK_CODE_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR task code")
    client = SWTRMCPClient()
    try:
        content = await client.call_tool("read_unit", {"code": normalized})
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    return {"task_code": normalized, "unit": _parse_tool_content(content)}


@router.get("/tasks/{task_code}/files")
async def get_task_files(task_code: str):
    normalized = task_code.upper().strip()
    if not _TASK_CODE_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR task code")
    client = SWTRMCPClient()
    try:
        content = await client.call_tool("get_unit_files", {"unit_code": normalized, "safe": True})
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    files = _extract_files(_parse_tool_content(content))
    return {"task_code": normalized, "files": files}


@router.get("/spaces/{space}/current-sprint")
async def get_current_sprint(space: str):
    normalized = space.upper().strip()
    if not re.fullmatch(r"^[A-Z][A-Z0-9_-]*$", normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR space")
    client = SWTRMCPClient()
    try:
        content = await client.call_tool("get_current_sprint", {"space": normalized})
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    return {"space": normalized, "sprint": _parse_tool_content(content)}


@router.get("/sprints/{sprint_id}/tasks")
async def get_sprint_tasks(
    sprint_id: str,
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    complete: bool = Query(False),
    max_pages: int = Query(100, ge=1, le=500),
):
    """Read sprint tasks with explicit completeness semantics.

    If the live MCP tool exposes page/offset arguments, `complete=true` walks
    every page until hasNext=false. If the MCP tool itself exposes only
    `sprint_id` while returning a paged response, Task API falls back explicitly
    to its proven canonical SWTR cache for completeness and reconciles the live
    first-page task IDs against that cache.
    """
    normalized = sprint_id.strip()
    if not normalized or len(normalized) > 200:
        raise HTTPException(status_code=400, detail="Invalid sprint id")

    client = SWTRMCPClient()
    try:
        properties = await client.tool_input_properties("get_sprint_tasks")
        arguments = await client.preferred_alias_arguments(
            "get_sprint_tasks",
            [
                (("page", "page_number", "pageNumber", "offset"), page if "offset" not in properties else page * limit),
                (("limit", "size", "page_size", "pageSize"), limit),
            ],
            required={"sprint_id": normalized},
        )
        content = await client.call_tool("get_sprint_tasks", arguments)
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc

    payload = _parse_tool_content(content)
    meta = _page_meta(payload)
    result: dict[str, Any] = {
        "sprint_id": normalized,
        "requested_page": page,
        "requested_limit": limit,
        "tasks": payload,
        "pagination": meta,
        "mcp_arguments": sorted(arguments),
        "complete": not meta["has_next"],
        "completeness_source": "mcp",
    }
    if not complete or not meta["has_next"]:
        return result

    paging_names = properties.intersection({"page", "page_number", "pageNumber", "offset"})
    if paging_names:
        all_items = _page_content(payload)
        seen = {code for code in (_source_task_code(item) for item in all_items) if code}
        current_page = page
        pages_read = 1
        while meta["has_next"]:
            if pages_read >= max_pages:
                raise HTTPException(status_code=502, detail="SWTR sprint pagination exceeded max_pages")
            current_page += 1
            next_arguments = await client.preferred_alias_arguments(
                "get_sprint_tasks",
                [
                    (("page", "page_number", "pageNumber", "offset"), current_page if "offset" not in properties else current_page * limit),
                    (("limit", "size", "page_size", "pageSize"), limit),
                ],
                required={"sprint_id": normalized},
            )
            try:
                next_payload = _parse_tool_content(await client.call_tool("get_sprint_tasks", next_arguments))
            except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
                raise _transport_http_error(exc) from exc
            for item in _page_content(next_payload):
                code = _source_task_code(item)
                if code and code in seen:
                    continue
                if code:
                    seen.add(code)
                all_items.append(item)
            meta = _page_meta(next_payload)
            pages_read += 1
        result.update({
            "tasks": {"content": all_items, "hasNext": False, "pageNumber": page, "pageSize": limit},
            "pagination": {"has_next": False, "page": page, "page_size": limit, "total": len(all_items)},
            "pages_read": pages_read,
            "complete": True,
            "completeness_source": "mcp-all-pages",
        })
        return result

    cached = _cached_complete_sprint_tasks(normalized)
    live_codes = {code for code in (_source_task_code(item) for item in _page_content(payload)) if code}
    cached_codes = {
        str(item.get("source_id") or item.get("id") or "").upper()
        for item in cached
        if item.get("source_id") or item.get("id")
    }
    result.update({
        "complete_tasks": cached,
        "complete_task_count": len(cached),
        "complete": True,
        "completeness_source": "task-api-canonical-cache",
        "live_first_page_reconciled": live_codes.issubset(cached_codes) if live_codes else None,
        "pagination_limitation": "MCP get_sprint_tasks exposes no page/offset input despite hasNext=true",
    })
    return result


@router.get("/versions")
async def search_versions(
    query: str | None = Query(None, min_length=1, max_length=200),
    space: str | None = Query(None, min_length=1, max_length=80),
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Expose the real read-only MCP `search_versions` capability."""
    normalized_space = space.upper().strip() if space else None
    if normalized_space and not re.fullmatch(r"^[A-Z][A-Z0-9_-]*$", normalized_space):
        raise HTTPException(status_code=400, detail="Invalid SWTR space")
    search_text = query.strip() if query else None

    client = SWTRMCPClient()
    try:
        properties = await client.tool_input_properties("search_versions")
        arguments = await client.preferred_alias_arguments(
            "search_versions",
            [
                (("query", "q", "search", "text"), search_text),
                (("space", "project", "project_code"), normalized_space),
                (("page", "page_number", "pageNumber", "offset"), page if "offset" not in properties else page * limit),
                (("limit", "size", "page_size", "pageSize"), limit),
            ],
        )
        content = await client.call_tool("search_versions", arguments)
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    return {
        "query": search_text,
        "space": normalized_space,
        "versions": payload,
        "pagination": _page_meta(payload),
        "mcp_arguments": sorted(arguments),
    }
