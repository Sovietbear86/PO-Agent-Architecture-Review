"""Live-only bounded task query facade for PO Agent V4.

This route exists specifically to keep factual V4 task capabilities off the
historical local /api/v1/tasks store. It reads REAL AS21 through MCP-SWTR,
applies only deterministic post-filters, and fails closed on source/transport
errors.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.routers.swtr_assignee import (
    _ALLOWED_SPACES,
    _attrs,
    _canonical_row,
    _resolve_external_id,
    get_assignee_tasks,
)
from app.routers.swtr_read import (
    _page_content,
    _page_meta,
    _parse_tool_content,
    _transport_http_error,
)
from app.services.swtr_mcp_client import (
    SWTRMCPClient,
    SWTRMCPProtocolError,
    SWTRMCPUnavailable,
)

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])


def _row_text(row: dict[str, Any], *names: str) -> str:
    attrs = _attrs(row)
    unit = row.get("unit") if isinstance(row.get("unit"), dict) else {}
    for name in names:
        value = unit.get(name)
        if value is None:
            value = row.get(name)
        if value is None:
            value = attrs.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


async def _fetch_space_rows(
    client: SWTRMCPClient,
    *,
    space: str,
    assignee_external_id: str | None,
    release_id: str | None,
    limit: int,
    max_pages: int,
) -> list[dict[str, Any]]:
    clauses = [f'space = "{space}"']
    if assignee_external_id:
        clauses.append(f'assigned_to = "{assignee_external_id}"')
    if release_id:
        clauses.append(f'fix_version_s = "{release_id}"')
    query = " AND ".join(clauses)
    rows: list[dict[str, Any]] = []
    seen_codes: set[str] = set()
    for page in range(max_pages):
        try:
            content = await client.call_tool(
                "find_units_by_filter",
                {
                    "request": {
                        "calculatedAttributes": [],
                        "attributes": [
                            "code",
                            "summary",
                            "description",
                            "assigned_to",
                            "space",
                            "workflow_status",
                            "scrum_board_plugin_sprint",
                            "fix_version_s",
                            "created_at",
                            "updated_at",
                            "createdAt",
                            "updatedAt",
                            "deadline",
                        ],
                        "query": query,
                        "timeZone": "Europe/Moscow",
                        "page": page,
                        "size": limit,
                    }
                },
            )
        except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
            raise _transport_http_error(exc) from exc
        payload = _parse_tool_content(content)
        page_rows = _page_content(payload)
        meta = _page_meta(payload)
        new_codes: set[str] = set()
        for row in page_rows:
            mapped = _canonical_row(row)
            code = str(mapped.get("source_id") or "").upper().strip() if mapped else ""
            if code and code not in seen_codes:
                new_codes.add(code)
        if page > 0 and meta["has_next"] and page_rows and not new_codes:
            raise HTTPException(status_code=502, detail=f"AS21 task query pagination repeated a page for {space}; collection completeness is unproven")
        seen_codes.update(new_codes)
        rows.extend(page_rows)
        if not meta["has_next"]:
            return rows
    raise HTTPException(status_code=502, detail=f"AS21 task query pagination exceeded max_pages for {space}")


@router.get("/task-query")
async def query_live_tasks(
    phrase: str | None = Query(None, max_length=500),
    space: str | None = Query(None, max_length=20),
    assignee: str | None = Query(None, max_length=120),
    release: str | None = Query(None, max_length=120),
    limit: int = Query(100, ge=1, le=1000),
    max_pages: int = Query(100, ge=1, le=500),
):
    """Return source-backed task rows without consulting the local task store.

    Pure assignee queries reuse the already-certified live assignee facade. This
    avoids reimplementing identity/pagination semantics and lets a configured
    canonical login be source-confirmed by REAL AS21. Text/scoped scans continue
    through the bounded live task-query path.
    """
    normalized_space = space.upper().strip() if space else None
    if normalized_space and normalized_space not in _ALLOWED_SPACES:
        raise HTTPException(status_code=400, detail="Space is outside the approved PO Agent scope")

    # Row #7 (assignee search) is a canonical identity query, not a generic
    # multi-space scan. Reuse the proven source-backed assignee facade directly.
    if assignee and not (phrase or "").strip() and not (release or "").strip():
        result = await get_assignee_tasks(
            assignee=assignee,
            space=normalized_space,
            limit=limit,
            max_pages=max_pages,
        )
        return {
            "source": "REAL_AS21",
            "route": "assignee-tasks",
            "space": normalized_space,
            "assignee": assignee,
            "external_id": result.get("external_id"),
            "phrase": None,
            "count": result.get("count", 0),
            "tasks": result.get("tasks", []),
        }

    client = SWTRMCPClient()
    external_id = await _resolve_external_id(client, assignee) if assignee else None
    spaces = [normalized_space] if normalized_space else sorted(_ALLOWED_SPACES)

    raw_rows: list[dict[str, Any]] = []
    for current_space in spaces:
        raw_rows.extend(
            await _fetch_space_rows(
                client,
                space=current_space,
                assignee_external_id=external_id,
                release_id=(release or "").strip() or None,
                limit=limit,
                max_pages=max_pages,
            )
        )

    needle = (phrase or "").strip().casefold()
    seen: set[str] = set()
    canonical: list[dict[str, Any]] = []
    for raw in raw_rows:
        mapped = _canonical_row(raw)
        if mapped is None:
            continue
        code = str(mapped.get("source_id") or "").upper().strip()
        if not code or code in seen:
            continue
        description = _row_text(raw, "description", "details", "body")
        title = str(mapped.get("title") or "")
        if needle and needle not in code.casefold() and needle not in title.casefold() and needle not in description.casefold():
            continue
        source_data = mapped.get("source_data") if isinstance(mapped.get("source_data"), dict) else {}
        source_data = dict(source_data)
        source_data["live_task_query_route"] = True
        mapped["description"] = description or None
        # Preserve source timestamps needed by bounded aging/flow analytics.
        # Missing timestamps remain missing; the consumer must not fabricate them.
        timestamp_aliases = {
            "created_at": ("created_at", "createdAt"),
            "updated_at": ("updated_at", "updatedAt"),
            "deadline": ("deadline", "dueDate", "due_date"),
        }
        for field, aliases in timestamp_aliases.items():
            value = _row_text(raw, *aliases)
            if value:
                mapped[field] = value
        mapped["source_data"] = source_data
        seen.add(code)
        canonical.append(mapped)

    return {
        "source": "REAL_AS21",
        "route": "find_units_by_filter",
        "space": normalized_space,
        "assignee": assignee,
        "external_id": external_id,
        "release": (release or "").strip() or None,
        "phrase": phrase,
        "count": len(canonical),
        "tasks": canonical,
    }
