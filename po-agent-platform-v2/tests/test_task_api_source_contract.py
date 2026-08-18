"""Regression tests for the real task-api -> Harness AS21 boundary.

These tests capture the behaviour that existed before the Harness expansion:
explicit assignee filtering, preservation of SWTR attributes, and no assumption
that task-api understands a q/JQL parameter.
"""
from __future__ import annotations

import asyncio

import httpx

from po_agent.adapters.task_api import TaskApiAS21Adapter


def _task(
    key: str,
    *,
    assignee: str,
    assignee_id: str,
    status: str = "Closed",
    sprint: str = "WMB-SPRNT-7",
    release: str = "WMB-2026-Q3",
) -> dict:
    return {
        "id": f"uuid-{key}",
        "source_id": key,
        "title": f"Task {key}",
        "description": f"Description for {key}",
        "status": status,
        "assignee": assignee,
        "deadline": None,
        "source_url": f"https://portal.works.prod.sbt/swtr/units/all/unit/{key}",
        "source": "swtr",
        "created_at": "2026-08-01T10:00:00",
        "updated_at": "2026-08-10T12:00:00",
        "source_data": {
            "swtr_code": key,
            "swtr_space": key.split("-", 1)[0],
            "workflow_status": status,
            "assignee_id": assignee_id,
            "sprint_id": sprint,
            "release_id": release,
            "priority": "High",
            "estimate_hours": 16,
            "labels": ["backend", "customer"],
            "components": [{"name": "OLAP"}],
        },
        "sprint": sprint,
    }


def test_assignee_filter_uses_supported_task_api_parameter_and_not_q():
    payload = [_task("WMB-101", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V")]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.rstrip("/") == "/api/v1/tasks"
        assert request.url.params.get("assignee") == "Kalachanov.V.V"
        assert "q" not in request.url.params
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(base_url="http://task-api", client=client)
    try:
        tasks = asyncio.run(adapter.search_tasks("assignee = Kalachanov.V.V"))
    finally:
        asyncio.run(client.aclose())

    assert [task.key for task in tasks] == ["WMB-101"]
    assert tasks[0].assignee == "Victor Kalachanov"
    assert tasks[0].assignee_id == "Kalachanov.V.V"


def test_project_sprint_status_and_release_are_filtered_locally_from_one_source_read():
    payload = [
        _task("WMB-101", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V"),
        _task("WMB-102", assignee="Ivan Ivanov", assignee_id="Ivanov.I.I", sprint="WMB-SPRNT-8"),
        _task("DMS-201", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V", sprint="DMS-SPRNT-7", release="DMS-2026-Q3"),
    ]
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.params.get("limit") == "10000"
        assert "q" not in request.url.params
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(base_url="http://task-api", client=client)
    query = "project = WMB AND sprint = WMB-SPRNT-7 AND status = Closed AND fixVersion = WMB-2026-Q3"
    try:
        tasks = asyncio.run(adapter.search_tasks(query))
    finally:
        asyncio.run(client.aclose())

    assert calls == 1
    assert [task.key for task in tasks] == ["WMB-101"]


def test_mapping_preserves_attributes_needed_by_po_agent():
    payload = [_task("WMB-101", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V")]

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(base_url="http://task-api", client=client)
    try:
        task = asyncio.run(adapter.get_task("WMB-101"))
    finally:
        asyncio.run(client.aclose())

    assert task is not None
    assert task.key == "WMB-101"
    assert task.assignee_id == "Kalachanov.V.V"
    assert task.sprint_id == "WMB-SPRNT-7"
    assert task.release_id == "WMB-2026-Q3"
    assert task.priority.value == "High"
    assert task.estimate_hours == 16.0
    assert task.labels == ["backend", "customer"]
    assert task.components == ["OLAP"]


def test_unknown_or_mixed_query_cannot_broaden_results():
    payload = [
        _task("WMB-101", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V"),
        _task("WMB-102", assignee="Victor Kalachanov", assignee_id="Kalachanov.V.V"),
    ]

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://task-api")
    adapter = TaskApiAS21Adapter(base_url="http://task-api", client=client)
    try:
        tasks = asyncio.run(adapter.search_tasks("assignee = Kalachanov.V.V AND nonexistent = NEVER_MATCH"))
    finally:
        asyncio.run(client.aclose())

    assert tasks == []
