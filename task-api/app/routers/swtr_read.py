"""Read-only rich SWTR facade for facts not exposed by the cached task list.

New Harness read capabilities use the configured live MCP-SWTR transport through
SWTRMCPClient. The historical SWTRSyncService subprocess bridge is not used here
because it is a bulk-sync path rather than a bounded read facade.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services.swtr_mcp_client import (
    SWTRMCPClient,
    SWTRMCPProtocolError,
    SWTRMCPUnavailable,
)
from app.models.history import HistoryEvent, HistoryResponse

router = APIRouter(prefix="/api/v1/swtr-read", tags=["swtr-read"])
_TASK_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
_SPRINT_ID_RE = re.compile(r"^(?P<space>[A-Z][A-Z0-9_-]*)-SPRNT-\d+$", re.I)
_MCP_ERROR_KEYS = ("errorType", "uiErrorMessage", "exceptionUUID")


def _mcp_error_detail(payload: dict[str, Any]) -> dict[str, Any]:
    detail: dict[str, Any] = {}
    if payload.get("errorType"):
        detail["error_type"] = str(payload["errorType"])
    if payload.get("uiErrorMessage"):
        detail["message"] = str(payload["uiErrorMessage"])
    if payload.get("exceptionUUID"):
        detail["exception_uuid"] = str(payload["exceptionUUID"])
    return detail or {"message": "SWTR MCP returned an error payload"}


def _is_not_found_marker(marker: str) -> bool:
    """Recognize authoritative SWTR/MCP not-found errors without masking outages.

    MCP-SWTR currently serializes some missing entities as an error payload that
    would otherwise be surfaced as HTTP 502. Translate only explicit not-found
    markers; transport/protocol failures remain 502/503.
    """
    normalized = marker.upper()
    return any(
        token in normalized
        for token in (
            "NOT_FOUND",
            "NOT FOUND",
            "ELEMENT_NOT_FOUND",
            "ENTITY_NOT_FOUND",
            "UNIT_NOT_FOUND",
            "TASK_NOT_FOUND",
            "НЕ НАЙДЕН",
            "НЕ НАЙДЕНА",
            "НЕ НАЙДЕНО",
            "НЕ СУЩЕСТВУЕТ",
        )
    )


def _raise_mcp_error_payload(payload: Any) -> None:
    if not isinstance(payload, dict) or not any(key in payload for key in _MCP_ERROR_KEYS):
        return
    detail = _mcp_error_detail(payload)
    marker = " ".join(str(value) for value in detail.values())
    upper_marker = marker.upper()
    if _is_not_found_marker(marker):
        status_code = 404
    elif "ACCESS_DENIED" in upper_marker or "ДОСТУП ЗАПРЕЩЕН" in upper_marker:
        status_code = 403
    else:
        status_code = 502
    raise HTTPException(status_code=status_code, detail=detail)


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
    payload = decoded[0] if len(decoded) == 1 else decoded
    _raise_mcp_error_payload(payload)
    return payload


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
    from app.routers.tasks import get_task_service
    from app.schemas.task import task_to_response

    service = get_task_service()
    rows: list[dict[str, Any]] = []
    for task in service.get_tasks(source="swtr", limit=10000, offset=0):
        response = task_to_response(task)
        if isinstance(response.sprint, str) and response.sprint.casefold() == sprint_id.casefold():
            rows.append(response.model_dump(mode="json"))
    return rows


def _first_declared(properties: dict[str, Any], aliases: tuple[str, ...]) -> str | None:
    return next((name for name in aliases if name in properties), None)


def _put_declared(target: dict[str, Any], properties: dict[str, Any], aliases: tuple[str, ...], value: Any) -> None:
    if value is None:
        return
    name = _first_declared(properties, aliases)
    if name is not None:
        target[name] = value


def _infer_space_from_sprint(sprint_id: str) -> str | None:
    match = _SPRINT_ID_RE.fullmatch(sprint_id.strip())
    return match.group("space").upper() if match else None


async def _schema_aware_get_sprint_tasks_arguments(
    client: SWTRMCPClient,
    *,
    sprint_id: str,
    space: str | None,
    page: int,
    limit: int,
) -> dict[str, Any]:
    schema = await client.tool_input_schema("get_sprint_tasks")
    properties = schema.get("properties") if isinstance(schema, dict) else None
    top = properties if isinstance(properties, dict) else {}

    request_schema = top.get("request")
    if isinstance(request_schema, dict):
        nested = request_schema.get("properties")
        nested_props = nested if isinstance(nested, dict) else {}
        if request_schema.get("type") == "object" or nested_props:
            request: dict[str, Any] = {}
            _put_declared(request, nested_props, ("sprint_id", "sprintId", "sprint", "sprint_code", "sprintCode", "code", "id"), sprint_id)
            _put_declared(request, nested_props, ("space", "project", "project_code", "spaceCode", "projectCode"), space)
            _put_declared(request, nested_props, ("page", "page_number", "pageNumber"), page)
            _put_declared(request, nested_props, ("offset", "start"), page * limit)
            _put_declared(request, nested_props, ("limit", "size", "page_size", "pageSize"), limit)
            return {"request": request}

    result: dict[str, Any] = {}
    _put_declared(result, top, ("sprint_id", "sprintId", "sprint", "sprint_code", "sprintCode", "code", "id"), sprint_id)
    _put_declared(result, top, ("space", "project", "project_code", "spaceCode", "projectCode"), space)
    _put_declared(result, top, ("page", "page_number", "pageNumber"), page)
    _put_declared(result, top, ("offset", "start"), page * limit)
    _put_declared(result, top, ("limit", "size", "page_size", "pageSize"), limit)
    if not any(key in result for key in ("sprint_id", "sprintId", "sprint", "sprint_code", "sprintCode", "code", "id")):
        result["sprint_id"] = sprint_id
    return result


async def _schema_aware_search_versions_arguments(
    client: SWTRMCPClient,
    *,
    query: str | None,
    space: str | None,
    page: int,
    limit: int,
) -> dict[str, Any]:
    """Build arguments from the live MCP schema, including nested `request` DTOs.

    Some MCP-SWTR versions expose `search_versions(request: {...})` instead of
    flat query/space parameters. The previous facade only inspected top-level
    aliases and therefore sent an empty object to a tool that required request.
    This builder treats the descriptor as the source of truth and never sends
    undeclared fields when an object schema is available.
    """
    schema = await client.tool_input_schema("search_versions")
    properties = schema.get("properties") if isinstance(schema, dict) else None
    top = properties if isinstance(properties, dict) else {}

    request_schema = top.get("request")
    if isinstance(request_schema, dict):
        request_type = request_schema.get("type")
        nested = request_schema.get("properties")
        nested_props = nested if isinstance(nested, dict) else {}
        if request_type == "object" or nested_props:
            request: dict[str, Any] = {}
            _put_declared(request, nested_props, ("query", "q", "search", "text", "name"), query)
            _put_declared(request, nested_props, ("space", "project", "project_code", "spaceCode", "projectCode"), space)
            offset = page * limit
            _put_declared(request, nested_props, ("page", "page_number", "pageNumber"), page)
            _put_declared(request, nested_props, ("offset", "start"), offset)
            _put_declared(request, nested_props, ("limit", "size", "page_size", "pageSize"), limit)
            return {"request": request}
        if request_type == "string":
            text = query or space
            if not text:
                raise SWTRMCPProtocolError("search_versions request string has no query or space")
            return {"request": text}

    result: dict[str, Any] = {}
    _put_declared(result, top, ("query", "q", "search", "text", "name"), query)
    _put_declared(result, top, ("space", "project", "project_code", "spaceCode", "projectCode"), space)
    _put_declared(result, top, ("page", "page_number", "pageNumber"), page)
    _put_declared(result, top, ("offset", "start"), page * limit)
    _put_declared(result, top, ("limit", "size", "page_size", "pageSize"), limit)
    return result


@router.get("/health")
async def swtr_read_health():
    client = SWTRMCPClient()
    try:
        tools = await client.list_tools()
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    return {
        "status": "connected",
        "transport": client.transport_kind(),
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
    space: str | None = Query(None, min_length=1, max_length=80),
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    complete: bool = Query(False),
    max_pages: int = Query(100, ge=1, le=500),
):
    normalized = sprint_id.strip()
    if not normalized or len(normalized) > 200:
        raise HTTPException(status_code=400, detail="Invalid sprint id")
    normalized_space = (space.upper().strip() if space else _infer_space_from_sprint(normalized))
    if normalized_space and not re.fullmatch(r"^[A-Z][A-Z0-9_-]*$", normalized_space):
        raise HTTPException(status_code=400, detail="Invalid SWTR space")

    client = SWTRMCPClient()
    try:
        properties = await client.tool_input_properties("get_sprint_tasks")
        arguments = await _schema_aware_get_sprint_tasks_arguments(
            client,
            sprint_id=normalized,
            space=normalized_space,
            page=page,
            limit=limit,
        )
        content = await client.call_tool("get_sprint_tasks", arguments)
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc

    payload = _parse_tool_content(content)
    meta = _page_meta(payload)
    result: dict[str, Any] = {
        "sprint_id": normalized,
        "space": normalized_space,
        "requested_page": page,
        "requested_limit": limit,
        "tasks": payload,
        "page": meta,
        "input_properties": sorted(properties),
    }
    if not complete:
        return result

    accumulated = list(_page_content(payload))
    seen_codes = {code for item in accumulated if (code := _source_task_code(item))}
    current_page = page
    while meta["has_next"] and len(accumulated) < limit * max_pages:
        current_page += 1
        try:
            arguments = await _schema_aware_get_sprint_tasks_arguments(
                client,
                sprint_id=normalized,
                space=normalized_space,
                page=current_page,
                limit=limit,
            )
            content = await client.call_tool("get_sprint_tasks", arguments)
        except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
            raise _transport_http_error(exc) from exc
        next_payload = _parse_tool_content(content)
        rows = _page_content(next_payload)
        added = 0
        for item in rows:
            code = _source_task_code(item)
            if code and code in seen_codes:
                continue
            if code:
                seen_codes.add(code)
            accumulated.append(item)
            added += 1
        next_meta = _page_meta(next_payload)
        if next_meta["has_next"] and added == 0:
            # The live schema may not expose an actual page/offset input. Do not
            # loop forever while pretending that the same first page is complete.
            raise HTTPException(
                status_code=502,
                detail="SWTR get_sprint_tasks reports more pages but its callable schema does not permit advancing pagination",
            )
        meta = next_meta

    result["complete_tasks"] = accumulated
    result["complete"] = not meta["has_next"]
    result["pages_fetched"] = current_page - page + 1
    return result


@router.get("/versions")
async def search_versions(
    query: str | None = Query(None, min_length=1, max_length=200),
    space: str | None = Query(None, min_length=1, max_length=80),
    page: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    normalized_space = space.upper().strip() if space else None
    if normalized_space and not re.fullmatch(r"^[A-Z][A-Z0-9_-]*$", normalized_space):
        raise HTTPException(status_code=400, detail="Invalid SWTR space")
    client = SWTRMCPClient()
    try:
        arguments = await _schema_aware_search_versions_arguments(
            client,
            query=query,
            space=normalized_space,
            page=page,
            limit=limit,
        )
        content = await client.call_tool("search_versions", arguments)
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    return {
        "query": query,
        "space": normalized_space,
        "page": page,
        "limit": limit,
        "versions": payload,
    }


@router.get("/tasks/{task_code}/history", response_model=HistoryResponse)
async def get_task_history(task_code: str):
    normalized = task_code.upper().strip()
    if not _TASK_CODE_RE.fullmatch(normalized):
        raise HTTPException(status_code=400, detail="Invalid SWTR task code")
    client = SWTRMCPClient()
    try:
        content = await client.call_tool("get_unit_change_history", {"unit_code": normalized})
    except (SWTRMCPUnavailable, SWTRMCPProtocolError) as exc:
        raise _transport_http_error(exc) from exc
    payload = _parse_tool_content(content)
    if isinstance(payload, dict):
        events_raw = payload.get("content", payload.get("events", []))
    else:
        events_raw = payload
    if not isinstance(events_raw, list):
        raise HTTPException(status_code=502, detail="SWTR change history payload is malformed")
    events: list[HistoryEvent] = []
    for raw in events_raw:
        if not isinstance(raw, dict):
            continue
        field_code = str(raw.get("fieldCode") or raw.get("field_code") or "")
        old_value = raw.get("oldValue", raw.get("old_value"))
        new_value = raw.get("newValue", raw.get("new_value"))
        changed_at_raw = raw.get("changedAt", raw.get("changed_at"))
        actor = raw.get("actor")
        try:
            changed_at = datetime.fromisoformat(str(changed_at_raw).replace("Z", "+00:00")) if changed_at_raw else datetime.now()
        except ValueError:
            changed_at = datetime.now()
        events.append(
            HistoryEvent(
                field_code=field_code,
                old_value=None if old_value is None else str(old_value),
                new_value=None if new_value is None else str(new_value),
                changed_at=changed_at,
                actor=None if actor is None else str(actor),
            )
        )
    return HistoryResponse(task_code=normalized, events=events)
