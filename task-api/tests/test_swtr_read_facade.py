"""Unit coverage for schema-aware SWTR read facade behavior."""

import pytest
from fastapi import HTTPException

from app.routers.swtr_read import (
    _parse_tool_content,
    _schema_aware_get_sprint_tasks_arguments,
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
