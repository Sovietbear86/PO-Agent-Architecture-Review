"""Live read-only assignee task facade over MCP-SWTR.

This route deliberately bypasses the cached/local task repository. It resolves a
team login to the authoritative AS21 user code, executes server-side TQL
`assigned_to` filtering through `find_units_by_filter`, follows pagination, and
returns canonical task-shaped rows for the Harness production adapter.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.swtr_mcp_client import (
    SWTRMCPClient,
    SWTRMCPProtocolError,
    SWTRMCPUnavailable,
)
from app.routers.swtr_read import (
    _page_content,
    _page_meta,
    _parse_tool_content,
    _transport_http_error,
)

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])
_ALLOWED_SPACES = frozenset({"WMB", "STS", "OLP", "DMS", "CRPV"})


def _attrs(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    raw = row.get("attributes")
    if not isinstance(raw, list):
        return result
    for item in raw:
        if isinstance(item, dict) and isinstance(item.get("code"), str):
            result[item["code"]] = item.get("value")
    return result


def _value_id(value: Any) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, dict):
        for key in ("code", "externalId", "login", "id", "value", "name"):
            candidate = value.get(key)
            if isinstance(candidate, (str, int)) and str(candidate).strip():
                return str(candidate).strip()
    return None


def _row_value(row: dict[str, Any], attrs: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row.get(name) is not None:
            return row.get(name)
        if name in attrs and attrs.get(name) is not None:
            return attrs.get(name)
    return None


def _canonical_row(row: dict[str, Any]) -> dict[str, Any] | None:
    attrs = _attrs(row)
    code = _value_id(_row_value(row, attrs, "code", "key", "source_id", "id"))
    if not code:
        return None
    summary = _row_value(row, attrs, "summary", "title", "name")
    title = str(summary).strip() if isinstance(summary, (str, int)) and str(summary).strip() else code
    assigned = _row_value(row, attrs, "assigned_to", "assignee")
    space_value = _row_value(row, attrs, "space", "project", "project_space")
    space = _value_id(space_value)
    status_value = _row_value(row, attrs, "workflow_status", "status")
    status = _value_id(status_value)

    swtr_attributes = row.get("attributes") if isinstance(row.get("attributes"), list) else []
    if not swtr_attributes:
        swtr_attributes = []
        if assigned is not None:
            swtr_attributes.append({"code": "assigned_to", "value": assigned})
        if space_value is not None:
            swtr_attributes.append({"code": "space", "value": space_value})
        if status_value is not None:
            swtr_attributes.append({"code": "workflow_status", "value": status_value})

    return {
        "source_id": code,
        "title": title,
        "status": status or "",
        "source": "swtr",
        "source_data": {
            "swtr_space": space,
            "workflow_status": status,
            "swtr_attributes": swtr_attributes,
            "live_assignee_route": True,
        },
    }


async def _resolve_external_id(client: SWTRMCPClient, assignee: str) -> str:
    needle = assignee.strip()
    try:
        content = await client.call_tool(
            "search_users",
            {"request": {"text_search": needle, "page": 0, "size": 100}},
        )
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    rows = _page_content(payload)
    if not rows and isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]

    exact: list[str] = []
    for row in rows:
        code = row.get("code")
        login = row.get("login")
        candidates = [value for value in (code, login) if isinstance(value, str)]
        if any(value.casefold() == needle.casefold() for value in candidates):
            if isinstance(code, str) and code.strip():
                exact.append(code.strip())
    exact = list(dict.fromkeys(exact))
    if len(exact) != 1:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "AS21 assignee identity is ambiguous or not found",
                "assignee": needle,
                "matches": exact,
            },
        )
    return exact[0]


@router.get("/assignee-tasks")
async def get_assignee_tasks(
    assignee: str = Query(..., min_length=1, max_length=120),
    space: str | None = Query(None, min_length=1, max_length=20),
    limit: int = Query(100, ge=1, le=1000),
    max_pages: int = Query(100, ge=1, le=500),
):
    """Return current REAL AS21 tasks for an assignee without local synchronization."""
    normalized_space = space.upper().strip() if space else None
    if normalized_space and normalized_space not in _ALLOWED_SPACES:
        raise HTTPException(status_code=400, detail="Space is outside the approved PO Agent scope")

    client = SWTRMCPClient()
    external_id = await _resolve_external_id(client, assignee)
    all_rows: list[dict[str, Any]] = []
    page = 0

    while page < max_pages:
        arguments = {
            "calculatedAttributes": [],
            "attributes": [
                "code",
                "summary",
                "assigned_to",
                "space",
                "workflow_status",
                "scrum_board_plugin_sprint",
                "fix_version_s",
            ],
            "query": f'assigned_to = "{external_id}"',
            "timeZone": "Europe/Moscow",
            "page": page,
            "size": limit,
        }
        try:
            content = await client.call_tool("find_units_by_filter", arguments)
        except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
            raise _transport_http_error(exc) from exc
        payload = _parse_tool_content(content)
        rows = _page_content(payload)
        meta = _page_meta(payload)
        all_rows.extend(rows)
        if not meta["has_next"]:
            break
        page += 1
    else:
        raise HTTPException(status_code=502, detail="AS21 assignee pagination exceeded max_pages")

    canonical: list[dict[str, Any]] = []
    for row in all_rows:
        mapped = _canonical_row(row)
        if mapped is None:
            continue
        row_space = mapped["source_data"].get("swtr_space")
        if row_space not in _ALLOWED_SPACES:
            continue
        if normalized_space and row_space != normalized_space:
            continue
        canonical.append(mapped)

    return {
        "assignee": assignee,
        "external_id": external_id,
        "space": normalized_space,
        "source": "REAL_AS21",
        "route": "search_users->find_units_by_filter",
        "count": len(canonical),
        "tasks": canonical,
        "pages_read": page + 1,
    }
