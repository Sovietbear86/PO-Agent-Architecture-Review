"""Unit coverage for schema-aware SWTR read facade behavior."""

import pytest
from fastapi import HTTPException

from app.routers.swtr_read import (
    _normalize_sprint_row,
    _parse_tool_content,
    _schema_aware_get_sprint_tasks_arguments,
    _schema_aware_search_sprints_arguments,
)


class SchemaClient:
    def __init__(self, schema):
        self.schema = schema

    async def tool_input_schema(self, name: str):
        assert name == "get_sprint_tasks"
        return self.schema


def test_parse_tool_content_rejects_access_denied_payload():
    content = [
        {
            "type": "text",
            "text": (
                '{"exceptionUUID":"abc","uiErrorMessage":"Доступ запрещен",'
                '"errorType":"SWTR_ACCESS_DENIED_ERROR"}'
            ),
        }
    ]

    with pytest.raises(HTTPException) as exc_info:
        _parse_tool_content(content)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["error_type"] == "SWTR_ACCESS_DENIED_ERROR"


@pytest.mark.asyncio
async def test_get_sprint_tasks_arguments_include_inferred_space_for_flat_schema():
    client = SchemaClient(
        {
            "properties": {
                "sprint_id": {"type": "string"},
                "space": {"type": "string"},
                "page": {"type": "integer"},
                "limit": {"type": "integer"},
            }
        }
    )

    args = await _schema_aware_get_sprint_tasks_arguments(
        client,
        sprint_id="DMS-SPRNT-2",
        space="DMS",
        page=0,
        limit=100,
    )

    assert args == {"sprint_id": "DMS-SPRNT-2", "space": "DMS", "page": 0, "limit": 100}


@pytest.mark.asyncio
async def test_get_sprint_tasks_arguments_include_inferred_space_for_request_schema():
    client = SchemaClient(
        {
            "properties": {
                "request": {
                    "type": "object",
                    "properties": {
                        "sprintId": {"type": "string"},
                        "projectCode": {"type": "string"},
                        "pageNumber": {"type": "integer"},
                        "pageSize": {"type": "integer"},
                    },
                }
            }
        }
    )

    args = await _schema_aware_get_sprint_tasks_arguments(
        client,
        sprint_id="DMS-SPRNT-2",
        space="DMS",
        page=1,
        limit=50,
    )

    assert args == {
        "request": {
            "sprintId": "DMS-SPRNT-2",
            "projectCode": "DMS",
            "pageNumber": 1,
            "pageSize": 50,
        }
    }


class SprintSchemaClient:
    def __init__(self, schema):
        self.schema = schema

    async def tool_input_schema(self, name: str):
        assert name == "search_sprints"
        return self.schema


@pytest.mark.asyncio
async def test_search_sprints_arguments_use_nested_request_schema():
    client = SprintSchemaClient(
        {
            "properties": {
                "request": {
                    "type": "object",
                    "properties": {
                        "space": {"type": "string"},
                        "page": {"type": "integer"},
                        "size": {"type": "integer"},
                    },
                }
            }
        }
    )
    args = await _schema_aware_search_sprints_arguments(
        client, space="DMS", page=0, limit=50
    )
    assert args == {"request": {"space": "DMS", "page": 0, "size": 50}}


@pytest.mark.asyncio
async def test_search_sprints_arguments_fallback_flat_schema():
    client = SprintSchemaClient(
        {
            "properties": {
                "space": {"type": "string"},
                "page": {"type": "integer"},
                "size": {"type": "integer"},
            }
        }
    )
    args = await _schema_aware_search_sprints_arguments(
        client, space="OLP", page=1, limit=25
    )
    assert args == {"space": "OLP", "page": 1, "size": 25}


def test_normalize_sprint_row_extracts_canonical_fields():
    row = {
        "id": {"code": "DMS-SPRNT-2"},
        "name": "2026_08_1",
        "status": "IN_PROGRESS",
        "startAt": "2026-08-16T21:00:00Z",
        "finishAt": "2026-08-30T21:00:00Z",
        "deleted": False,
    }
    normalized = _normalize_sprint_row(row)
    assert normalized["code"] == "DMS-SPRNT-2"
    assert normalized["status"] == "IN_PROGRESS"
    assert normalized["start_at"] == "2026-08-16T21:00:00Z"
    assert normalized["deleted"] is False


def test_normalize_sprint_row_defaults_deleted_flag():
    normalized = _normalize_sprint_row({"id": {"code": "X-SPRNT-1"}, "name": "n", "status": "NEW"})
    assert normalized["code"] == "X-SPRNT-1"
    assert normalized["deleted"] is False
