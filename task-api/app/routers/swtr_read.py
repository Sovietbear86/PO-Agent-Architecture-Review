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
    """Normalize proven MCP file-list envelopes without broad guessing."""
    if isinstance(payload, dict):
        for key in ("content", "files"):
            files = payload.get(key)
            if files is None:
                continue
            if not isinstance(files, list):
                raise HTTPException(
                    status_code=502,
                    detail=f"SWTR file metadata field {key!r} is not a list",
                )
            if not all(isinstance(item, dict) for item in files):
                raise HTTPException(
                    status_code=502,
                    detail="SWTR file metadata contains non-object item",
                )
            return files

        if any(key in payload for key in ("fileId", "id")) and any(
            key in payload for key in ("fileName", "name")
        ):
            return [payload]

    if isinstance(payload, list):
        if not all(isinstance(item, dict) for item in payload):
            raise HTTPException(
                status_code=502,
                detail="SWTR file metadata contains non-object item",
            )
        return payload

    raise HTTPException(status_code=502, detail="SWTR file metadata shape is unsupported")


def _transport_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SWTRMCPUnavailable):
        return HTTPException(status_code=503, detail="SWTR MCP unavailable")
    return HTTPException(status_code=502, detail="SWTR MCP protocol error")


def _page_meta(payload: Any) -> dict[str, Any]:
    """Expose a stable pagination summary without rewriting source data."""
    if not isinstance(payload, dict):
        return {"has_next": False, "page": None, "page_size": None, "total": None}
    has_next = payload.get("hasNext")
    if has_next is None:
        has_next = payload.get("has_next")
    page = payload.get("pageNumber", payload.get("page_number", payload.get("page")))
    size = payload.get("pageSize", payload.get("page_size", payload.get("size")))
    total = payload.get("totalElements", payload.get("total_elements", payload.get("total")))
    return {
        "has_next": bool(has_next),
        "page": page,
        "page_size": size,
        "total": total,
    }


@router.get("/health")
async def swtr_read_health():
    """Prove that Task API can reach the live MCP-SWTR SSE service."""
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
    """Return one full real SWTR unit via MCP read_unit, read-only."""
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
    """Return attachment metadata for one SWTR unit, without downloading content."""
    normalized = task_code.upper().strip()
    if not _TASK_CODE_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR task code")

    client = SWTRMCPClient()
    try:
        content = await client.call_tool(
            "get_unit_files",
            {"unit_code": normalized, "safe": True},
        )
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc

    files = _extract_files(_parse_tool_content(content))
    return {"task_code": normalized, "files": files}


@router.get("/spaces/{space}/current-sprint")
async def get_current_sprint(space: str):
    """Read the current sprint for a real SWTR space through the same SSE client."""
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
):
    """Read one explicit page of real sprint tasks via MCP-SWTR.

    MCP installations have used several pagination naming conventions. We
    inspect the live tool schema and send only parameters it actually declares,
    so unsupported argument names can never be silently invented.
    """
    normalized = sprint_id.strip()
    if not normalized or len(normalized) > 200:
        raise HTTPException(status_code=400, detail="Invalid sprint id")

    client = SWTRMCPClient()
    try:
        arguments = await client.supported_arguments(
            "get_sprint_tasks",
            {
                "page": page,
                "page_number": page,
                "pageNumber": page,
                "offset": page * limit,
                "limit": limit,
                "size": limit,
                "page_size": limit,
                "pageSize": limit,
            },
            required={"sprint_id": normalized},
        )
        content = await client.call_tool("get_sprint_tasks", arguments)
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    return {
        "sprint_id": normalized,
        "requested_page": page,
        "requested_limit": limit,
        "tasks": payload,
        "pagination": _page_meta(payload),
        "mcp_arguments": sorted(arguments),
    }


@router.get("/versions")
async def search_versions(
    query: str | None = Query(None, min_length=1, max_length=200),
    space: str | None = Query(None, min_length=1, max_length=80),
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Expose the real read-only MCP `search_versions` capability.

    Argument names are filtered against the live MCP tool schema. The raw
    source payload is preserved so release-health mapping can remain explicit
    and testable rather than relying on guessed source shapes.
    """
    normalized_space = space.upper().strip() if space else None
    if normalized_space and not re.fullmatch(r"^[A-Z][A-Z0-9_-]*$", normalized_space):
        raise HTTPException(status_code=400, detail="Invalid SWTR space")
    search_text = query.strip() if query else None

    client = SWTRMCPClient()
    try:
        arguments = await client.supported_arguments(
            "search_versions",
            {
                "query": search_text,
                "q": search_text,
                "search": search_text,
                "text": search_text,
                "space": normalized_space,
                "project": normalized_space,
                "project_code": normalized_space,
                "page": page,
                "page_number": page,
                "pageNumber": page,
                "offset": page * limit,
                "limit": limit,
                "size": limit,
                "page_size": limit,
                "pageSize": limit,
            },
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
