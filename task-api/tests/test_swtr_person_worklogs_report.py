"""A230R3.1: bounded author/date worklog facade guardrail tests."""
import json
from datetime import date

import pytest
from fastapi import HTTPException
from app.routers import swtr_read


def _row(*, author="Ivanov.I.I", logged_on="2026-10-20", duration=3600000):
    return {
        "id": "wl-1", "date": logged_on,
        "user": {"externalId": author}, "unit": {"code": "DMS-380"},
        "time": {"time": duration, "temporalUnit": "MILLIS"},
    }


class MockMCP:
    last_args = None
    payload = None

    async def call_tool(self, name, args):
        assert name == "get_work_report_filter"
        MockMCP.last_args = args
        return [{"type": "text", "text": json.dumps(MockMCP.payload)}]


@pytest.mark.asyncio
async def test_author_date_range_source_backed(monkeypatch):
    monkeypatch.setattr(swtr_read, "SWTRMCPClient", MockMCP)
    MockMCP.payload = {"content": [_row()], "pageNumber": 0, "pageSize": 50, "hasNext": False}
    result = await swtr_read.get_person_worklogs_report(
        user="Ivanov.I.I", date_from="2026-10-01", date_to="2026-10-23",
        space="DMS", unit=None, page=0, size=50)
    assert result["complete"] is True
    assert result["page_hours"] == 1.0
    assert result["worklog_count"] == 1
    assert result["attribution"] == "worklog_author_external_id"
    assert MockMCP.last_args == {
        "user_external_id": "Ivanov.I.I", "date_from": "2026-10-01",
        "date_to": "2026-10-23", "page": 0, "size": 50, "space": "DMS",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", [
    {"user": " "},
    {"date_from": "2026-10-25", "date_to": "2026-10-23"},
    {"date_from": "2026-10-01", "date_to": "2026-11-23"},
    {"space": "bad space"},
])
async def test_invalid_queries_fail_before_mcp(monkeypatch, bad):
    class NoCall:
        def __init__(self): raise AssertionError("unsafe MCP request")
    monkeypatch.setattr(swtr_read, "SWTRMCPClient", NoCall)
    args = {"user":"Ivanov.I.I", "date_from":"2026-10-01", "date_to":"2026-10-23",
            "space":None, "unit":None, "page":0, "size":50}
    args.update(bad)
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_person_worklogs_report(**args)
    assert err.value.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    {"content":[_row(author="Another.Person")], "pageNumber":0, "hasNext":False},
    {"content":[_row(logged_on="2026-09-30")], "pageNumber":0, "hasNext":False},
    {"content":[_row(duration=None)], "pageNumber":0, "hasNext":False},
    {"content":[_row()], "pageNumber":0}, # no proof of pagination completeness
    {"content":[_row()], "pageNumber":1, "hasNext":False},
    {"content":"no rows", "pageNumber":0, "hasNext":False},
])
async def test_source_mismatch_fails_closed(monkeypatch, payload):
    monkeypatch.setattr(swtr_read, "SWTRMCPClient", MockMCP)
    MockMCP.payload=payload
    with pytest.raises(HTTPException) as err:
        await swtr_read.get_person_worklogs_report(
            user="Ivanov.I.I", date_from="2026-10-01", date_to="2026-10-23",
            space=None, unit=None, page=0, size=50)
    assert err.value.status_code == 502


@pytest.mark.asyncio
async def test_has_next_is_not_a_complete_zero(monkeypatch):
    monkeypatch.setattr(swtr_read, "SWTRMCPClient", MockMCP)
    MockMCP.payload = {"content":[], "pageNumber":0, "hasNext":True}
    result=await swtr_read.get_person_worklogs_report(
        user="Ivanov.I.I", date_from="2026-10-01", date_to="2026-10-23",
        space=None, unit=None, page=0, size=50)
    assert result["complete"] is False
    assert result["has_next"] is True
