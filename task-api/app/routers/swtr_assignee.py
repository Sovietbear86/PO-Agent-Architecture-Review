"""Live read-only assignee task facade over MCP-SWTR.

This route deliberately bypasses the cached/local task repository. It resolves a
team login or natural person reference to the authoritative AS21 user code,
executes server-side TQL ``assigned_to`` filtering through find_units_by_filter,
follows pagination, and returns canonical task-shaped rows for the Harness
production adapter.
"""
from __future__ import annotations

import re
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


def _raw_attribute_entries(row: dict[str, Any]) -> list[tuple[str, Any]]:
    entries: list[tuple[str, Any]] = []
    containers = [row]
    nested_unit = row.get("unit")
    if isinstance(nested_unit, dict):
        containers.append(nested_unit)
    for container in containers:
        raw = container.get("attributes")
        if not isinstance(raw, list):
            continue
        for item in raw:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            if not isinstance(code, str):
                descriptor = item.get("attribute")
                code = descriptor.get("code") if isinstance(descriptor, dict) else None
            if isinstance(code, str):
                entries.append((code, item.get("value")))
    return entries


def _attrs(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for code, value in _raw_attribute_entries(row):
        result[code] = value
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


def _status_identifier(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("name", "value", "code", "id"):
            candidate = value.get(key)
            if isinstance(candidate, (str, int)) and str(candidate).strip():
                return str(candidate).strip()
    return ""


def _row_value(row: dict[str, Any], attrs: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row and row.get(name) is not None:
            return row.get(name)
        if name in attrs and attrs.get(name) is not None:
            return attrs.get(name)
    return None


def _canonical_row(row: dict[str, Any]) -> dict[str, Any] | None:
    attrs = _attrs(row)
    unit = row.get("unit") if isinstance(row.get("unit"), dict) else {}

    code = _value_id(_row_value(unit, attrs, "code", "key", "source_id", "id"))
    if not code:
        code = _value_id(_row_value(row, attrs, "code", "key", "source_id", "id"))
    if not code:
        return None

    summary = _row_value(unit, attrs, "summary", "title", "name")
    if summary is None:
        summary = _row_value(row, attrs, "summary", "title", "name")
    title = str(summary).strip() if isinstance(summary, (str, int)) and str(summary).strip() else code

    assigned = _row_value(unit, attrs, "assigned_to", "assignee")
    if assigned is None:
        assigned = _row_value(row, attrs, "assigned_to", "assignee")

    space_value = _row_value(unit, attrs, "space", "project", "project_space")
    if space_value is None:
        space_value = _row_value(row, attrs, "space", "project", "project_space")
    space = _value_id(space_value)

    status_value = _row_value(unit, attrs, "workflow_status", "status")
    if status_value is None:
        status_value = _row_value(row, attrs, "workflow_status", "status")
    status = _status_identifier(status_value)

    swtr_attributes = [{"code": c, "value": v} for c, v in _raw_attribute_entries(row)]
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


async def _search_user_rows(client: SWTRMCPClient, text: str) -> list[dict[str, Any]]:
    try:
        content = await client.call_tool(
            "search_users",
            {"request": {"text_search": text, "page": 0, "size": 100}},
        )
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    rows = _page_content(payload)
    if not rows and isinstance(payload, list):
        rows = [row for row in payload if isinstance(row, dict)]
    return rows


def _russian_nominative_retry(value: str) -> str | None:
    text = value.strip()
    if not re.fullmatch(r"[А-Яа-яЁё]+", text):
        return None
    if len(text) < 4 or not text.casefold().endswith("а"):
        return None
    candidate = text[:-1]
    return candidate if len(candidate) >= 3 else None


def _tokens(value: str) -> frozenset[str]:
    return frozenset(re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", value.casefold()))


def _row_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        if value.strip():
            out.append(value.strip())
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(_row_strings(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(_row_strings(item))
    return out


def _unique_name_match(rows: list[dict[str, Any]], needle: str) -> str | None:
    """Resolve a natural full name only when source rows make it unique.

    This is source-backed token matching, not a roster/surname hardcode. It is
    intentionally conservative: every meaningful token from the user's natural
    reference must appear in at least one source string for the same row, and
    exactly one canonical user code may satisfy that condition.
    """
    wanted = _tokens(needle)
    if not wanted:
        return None
    matches: list[str] = []
    for row in rows:
        code = row.get("code")
        if not isinstance(code, str) or not code.strip():
            continue
        haystack: set[str] = set()
        for text in _row_strings(row):
            haystack.update(_tokens(text))
        if wanted <= haystack:
            matches.append(code.strip())
    unique = list(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


async def _resolve_external_id(client: SWTRMCPClient, assignee: str) -> str:
    needle = assignee.strip()
    rows = await _search_user_rows(client, needle)

    if not rows:
        retry = _russian_nominative_retry(needle)
        if retry and retry.casefold() != needle.casefold():
            rows = await _search_user_rows(client, retry)

    exact: list[str] = []
    all_codes: list[str] = []
    for row in rows:
        code = row.get("code")
        login = row.get("login")
        if isinstance(code, str) and code.strip():
            all_codes.append(code.strip())
        candidates = [value for value in (code, login) if isinstance(value, str)]
        if any(value.casefold() == needle.casefold() for value in candidates):
            if isinstance(code, str) and code.strip():
                exact.append(code.strip())
    exact = list(dict.fromkeys(exact))
    if len(exact) == 1:
        return exact[0]

    natural = _unique_name_match(rows, needle)
    if natural:
        return natural

    unique_codes = list(dict.fromkeys(all_codes))
    if not exact and len(unique_codes) == 1:
        return unique_codes[0]

    raise HTTPException(
        status_code=409,
        detail={
            "message": "AS21 assignee identity is ambiguous or not found",
            "assignee": needle,
            "matches": exact or unique_codes,
        },
    )


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
            "request": {
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
