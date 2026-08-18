"""Read-only rich SWTR facade for facts not exposed by the cached task list.

This router deliberately exposes only proven read operations. It delegates to the
existing MCP-SWTR integration owned by :class:`SWTRSyncService`; callers never
receive credentials and no create/update/transition tool is reachable here.
"""
from __future__ import annotations

import json
import re
from typing import Any

from fastapi import APIRouter, HTTPException

from app.services.swtr_sync_service import SWTRSyncService

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])
_TASK_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")


def _parse_tool_payload(result: dict[str, Any] | None) -> Any:
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="SWTR MCP returned no response")
    if result.get("error"):
        raise HTTPException(status_code=502, detail="SWTR MCP read failed")
    content = result.get("result", {}).get("content", [])
    if not isinstance(content, list):
        raise HTTPException(status_code=502, detail="SWTR MCP returned malformed content")

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
        # Some MCP wrappers return a direct single file object.
        if isinstance(payload.get("id"), str) and isinstance(payload.get("name"), str):
            return [payload]
    if isinstance(payload, list) and all(isinstance(item, dict) for item in payload):
        return payload
    raise HTTPException(status_code=502, detail="SWTR file metadata shape is unsupported")


@router.get("/tasks/{task_code}/files")
async def get_task_files(task_code: str):
    """Return attachment metadata for one SWTR unit, without downloading content."""
    normalized = task_code.upper().strip()
    if not _TASK_CODE_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR task code")

    service = SWTRSyncService()
    result = service._run_mcp_command(  # centralized existing MCP transport
        "tools/call",
        {
            "name": "get_unit_files",
            "arguments": {"unit_code": normalized, "safe": True},
        },
    )
    files = _extract_files(_parse_tool_payload(result))
    return {"task_code": normalized, "files": files}
