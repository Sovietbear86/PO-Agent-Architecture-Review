from __future__ import annotations

import json

import pytest

from app.routers.swtr_query import _fetch_space_rows


class _Client:
    def __init__(self):
        self.calls = []

    async def call_tool(self, name, payload):
        self.calls.append((name, payload))
        return [{"type": "text", "text": json.dumps({"content": [], "hasNext": False})}]


@pytest.mark.asyncio
async def test_release_filter_is_pushed_into_bounded_source_query():
    client = _Client()
    rows = await _fetch_space_rows(
        client,
        space="DMS",
        assignee_external_id=None,
        release_id="DMS-REL-42",
        limit=100,
        max_pages=3,
    )
    assert rows == []
    assert len(client.calls) == 1
    name, payload = client.calls[0]
    assert name == "find_units_by_filter"
    query = payload["request"]["query"]
    assert 'space = "DMS"' in query
    assert 'fix_version_s = "DMS-REL-42"' in query
