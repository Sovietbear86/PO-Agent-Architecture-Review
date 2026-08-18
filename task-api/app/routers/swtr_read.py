"""Read-only rich SWTR facade for facts not exposed by the cached task list.

New Harness read capabilities use the live MCP-SWTR SSE transport through
SWTRMCPClient.  The historical SWTRSyncService subprocess/stdin bridge is not
used here because the live MCP server is an SSE service.
"""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException

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
        files = payload.get("files")
        if isinstance(files, list):
            if not all(isinstance(item, dict) for item in files):
                raise HTTPException(status_code=502, detail="SWTR file metadata contains non-object item")
            return files
        # Some MCP wrappers return one file object directly.
        if any(key in payload for key in ("fileId", "id")) and any(
            key in payload for key in ("fileName", "name")
        ):
            return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise HTTPException(status_code=502, detail="SWTR file metadata shape is unsupported")


def _transport_http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, SWTRMCPUnavailable):
        return HTTPException(status_code=503, detail="SWTR MCP unavailable")
    return HTTPException(status_code=502, detail="SWTR MCP protocol error")


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
async def get_sprint_tasks(sprint_id: str):
    """Read tasks for one real sprint via the live MCP-SWTR SSE service."""
    normalized = sprint_id.strip()
    if not normalized or len(normalized) > 200:
        raise HTTPException(status_code=400, detail="Invalid sprint id")

    client = SWTRMCPClient()
    try:
        content = await client.call_tool("get_sprint_tasks", {"sprint_id": normalized})
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    return {"sprint_id": normalized, "tasks": _parse_tool_content(content)}
