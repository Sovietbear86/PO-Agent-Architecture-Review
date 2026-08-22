"""Read-only rich SWTR facade for facts not exposed by the cached task list.

New Harness read capabilities use the configured live MCP-SWTR transport through
SWTRMCPClient. The historical SWTRSyncService subprocess bridge is not used here
because it is a bulk-sync path rather than a bounded read facade.
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


def _raise_mcp_error_payload(payload: Any) -> None:
    if not isinstance(payload, dict) or not any(key in payload for key in _MCP_ERROR_KEYS):
        return
    detail = _mcp_error_detail(payload)
    marker = " ".join(str(value) for value in detail.values()).upper()
    status_code = 403 if "ACCESS_DENIED" in marker or "ДОСТУП ЗАПРЕЩЕН" in marker else 502
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
        "pagination": meta,
        "mcp_arguments": sorted(arguments),
        "mcp_argument_shape": "request" if "request" in arguments else "flat",
        "mcp_argument_preview": arguments,
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
            next_arguments = await _schema_aware_get_sprint_tasks_arguments(
                client,
                sprint_id=normalized,
                space=normalized_space,
                page=current_page,
                limit=limit,
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
        arguments = await _schema_aware_search_versions_arguments(
            client,
            query=search_text,
            space=normalized_space,
            page=page,
            limit=limit,
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
        "mcp_argument_shape": "request" if "request" in arguments else "flat",
    }
