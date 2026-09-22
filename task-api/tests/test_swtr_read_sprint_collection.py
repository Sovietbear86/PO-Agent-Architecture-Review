"""Assignment 185 — B1 regression: bounded complete sprint-task collection.

B1: the live ``get_sprint_tasks`` MCP tool schema accepts no page input, so
requesting page 1 returns the same first page again. The previous collection
loop keyed identity on top-level row fields that miss the nested ``unit.code``,
so it re-absorbed the identical page, amplified one 100-row page into ~10,000
duplicate rows (25 MB / 51 s), and then failed closed for any sprint with more
than 100 tasks (e.g. DMS-SPRNT-1 with 104).

The fix:
* canonical identity from nested ``unit.code`` (task-code shape validated, so
  sprint/version ids are never mistaken for task identities);
* a page that contributes zero new canonical identities stops the loop
  immediately (no amplification);
* when the primary view cannot prove a complete set, the source-backed,
  pageable sprint-constraint query (``find_units_by_filter``) is preferred and
  swapped in only when it is at least as complete as the primary view;
* when neither can prove completeness, the response carries a typed
  ``complete=false`` (never an empty or fabricated "complete" set).
"""

import json

import pytest

from app.routers import swtr_read
from app.routers.swtr_read import (
    _canonical_sprint_task_row,
    _raw_attribute_entries,
    _source_task_code,
    _status_identifier,
)


# ---------------------------------------------------------------------------
# Raw-row fixtures (both live encodings)
# ---------------------------------------------------------------------------


def _ws(name: str, status_type: str) -> dict:
    return {"code": f"enc_{status_type}", "name": name, "statusType": status_type}


def _nested_row(code: str, *, summary: str = "Task", space: str = "DMS",
                ws: dict | None = None, sprint: str = "DMS-SPRNT-1") -> dict:
    """get_sprint_tasks shape: unit nested, flat attribute entries."""
    attrs = []
    if ws is not None:
        attrs.append({"code": "workflow_status", "value": ws})
    if sprint is not None:
        attrs.append({"code": "scrum_board_plugin_sprint", "value": {"code": sprint}})
    return {"unit": {"code": code, "summary": summary, "space": {"code": space}, "attributes": attrs}}


def _flat_row(code: str, *, summary: str = "Task", space: str = "DMS",
              ws: dict | None = None, sprint: str = "DMS-SPRNT-1") -> dict:
    """find_units_by_filter (TQL) shape: flat top-level fields."""
    attrs = []
    if ws is not None:
        attrs.append({"code": "workflow_status", "value": ws})
    if sprint is not None:
        attrs.append({"code": "scrum_board_plugin_sprint", "value": {"code": sprint}})
    return {"code": code, "summary": summary, "space": space, "attributes": attrs}


def _page(rows: list[dict], *, has_next: bool) -> dict:
    return {"hasNext": has_next, "content": rows}


def _content(payload: dict) -> list[dict]:
    return [{"type": "text", "text": json.dumps(payload)}]


def _sprint_rows(codes) -> list[dict]:
    return [_nested_row(c, ws=_ws("In progress", "progress")) for c in codes]


def _tql_rows(codes) -> list[dict]:
    return [_flat_row(c, ws=_ws("In progress", "progress")) for c in codes]


# ---------------------------------------------------------------------------
# Fake MCP client
# ---------------------------------------------------------------------------


class ScriptedClient:
    """Scripted SWTRMCPClient for the get_sprint_tasks / TQL surface.

    ``sprint`` maps a requested page index to a page payload; missing pages
    repeat the last one (models a source that cannot paginate forward).
    ``tql_pages`` is an ordered list of TQL page payloads.
    """

    def __init__(self, sprint, tql_pages):
        self.sprint = sprint
        self.tql_pages = tql_pages or []
        self.sprint_calls = 0
        self.tql_calls = 0
        self.tql_page_index = 0

    async def tool_input_properties(self, name: str):
        return {"sprint_id", "space", "page", "limit"}

    async def tool_input_schema(self, name: str):
        return {"properties": {"sprint_id": {}, "space": {}, "page": {}, "limit": {}}}

    async def call_tool(self, name: str, arguments: dict):
        if name == "get_sprint_tasks":
            self.sprint_calls += 1
            page = arguments.get("page", 0)
            return _content(self.sprint(page))
        if name == "find_units_by_filter":
            self.tql_calls += 1
            idx = self.tql_page_index
            self.tql_page_index += 1
            payload = self.tql_pages[idx] if idx < len(self.tql_pages) else _page([], has_next=False)
            return _content(payload)
        raise AssertionError(f"unexpected tool {name}")


def _install(monkeypatch, client) -> None:
    monkeypatch.setattr(swtr_read, "SWTRMCPClient", lambda: client)


# ---------------------------------------------------------------------------
# Helper unit coverage
# ---------------------------------------------------------------------------


class TestSourceTaskCode:
    def test_nested_unit_code(self):
        assert _source_task_code(_nested_row("DMS-390")) == "DMS-390"

    def test_top_level_code(self):
        assert _source_task_code(_flat_row("DMS-390")) == "DMS-390"

    def test_sprint_id_is_not_a_task_code(self):
        row = {"id": {"code": "DMS-SPRNT-1"}}
        assert _source_task_code(row) is None

    def test_non_string_code_rejected(self):
        assert _source_task_code({"unit": {"code": 12345}}) is None
        assert _source_task_code({"unit": {}}) is None


class TestRawAttributeEntries:
    def test_flat_encoding_top_level(self):
        entries = dict(_raw_attribute_entries(
            _flat_row("DMS-1", ws={"name": "In progress", "statusType": "progress"})))
        assert entries["workflow_status"] == {"name": "In progress", "statusType": "progress"}

    def test_nested_encoding_under_unit(self):
        row = {"unit": {"code": "DMS-1", "attributes": [
            {"attribute": {"code": "workflow_status"}, "value": {"name": "Closed", "statusType": "done"}},
        ]}}
        entries = dict(_raw_attribute_entries(row))
        assert entries["workflow_status"] == {"name": "Closed", "statusType": "done"}


class TestStatusIdentifier:
    def test_prefers_human_name_over_opaque_id(self):
        assert _status_identifier({"code": "CNCLLD_x", "name": "CANCELLED", "statusType": "done"}) == "CANCELLED"

    def test_plain_string(self):
        assert _status_identifier("In progress") == "In progress"

    def test_missing(self):
        assert _status_identifier(None) == ""


class TestCanonicalRow:
    def test_nested_row_preserves_workflow_semantics(self):
        row = _canonical_sprint_task_row(_nested_row("DMS-390", summary="Fix bug",
                                                      ws=_ws("In progress", "progress")))
        assert row is not None
        assert row["source_id"] == "DMS-390"
        assert row["title"] == "Fix bug"
        assert row["status"] == "In progress"
        codes = {e["code"]: e["value"] for e in row["source_data"]["swtr_attributes"]}
        assert codes["workflow_status"]["statusType"] == "progress"
        assert row["source_data"]["swtr_space"] == "DMS"

    def test_flat_row_resolves_top_level_fields(self):
        row = _canonical_sprint_task_row(_flat_row("DMS-400", summary="Flat",
                                                    ws=_ws("Closed", "done")))
        assert row is not None
        assert row["source_id"] == "DMS-400"
        assert row["title"] == "Flat"
        assert row["status"] == "Closed"
        assert row["source_data"]["swtr_space"] == "DMS"

    def test_no_code_returns_none(self):
        assert _canonical_sprint_task_row({"unit": {"summary": "no code"}}) is None


# ---------------------------------------------------------------------------
# Endpoint collection behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stuck_first_page_falls_back_to_tql_and_is_complete(monkeypatch):
    # Live bug: get_sprint_tasks cannot paginate -> always returns the same
    # 100 rows with hasNext. TQL has the true 104. Expect 104 unique, complete.
    first_100 = [f"DMS-{i}" for i in range(1, 101)]
    extra_4 = [f"DMS-{i}" for i in range(101, 105)]
    stuck_page = _page(_sprint_rows(first_100), has_next=True)  # repeated for every page

    client = ScriptedClient(
        sprint=lambda page: stuck_page,  # cannot advance
        tql_pages=[
            _page(_tql_rows(first_100), has_next=True),
            _page(_tql_rows(extra_4), has_next=False),
        ],
    )
    _install(monkeypatch, client)

    result = await swtr_read.get_sprint_tasks(
        sprint_id="DMS-SPRNT-1", space=None, page=0, limit=100,
        complete=True, max_pages=50,
    )

    codes = [row["source_id"] for row in result["complete_tasks"]]
    assert len(codes) == 104
    assert len(set(codes)) == 104
    assert result["complete"] is True
    assert result["membership_proven"] is True
    assert result["source_path"] == "tql_sprint_constraint"
    assert all(row["sprint_id"] == "DMS-SPRNT-1" for row in result["complete_tasks"])
    assert client.tql_calls == 2


@pytest.mark.asyncio
async def test_stuck_page_without_tql_is_typed_incomplete_not_amplified(monkeypatch):
    # TQL returns nothing (outage/empty). Primary view is bounded to 100 unique
    # rows and the response is typed incomplete — never amplified, never empty.
    first_100 = [f"DMS-{i}" for i in range(1, 101)]
    stuck_page = _page(_sprint_rows(first_100), has_next=True)
    client = ScriptedClient(sprint=lambda page: stuck_page, tql_pages=[])
    _install(monkeypatch, client)

    result = await swtr_read.get_sprint_tasks(
        sprint_id="DMS-SPRNT-1", space=None, page=0, limit=100,
        complete=True, max_pages=50,
    )

    assert result["complete"] is False
    assert result["membership_proven"] is False
    assert result["source_path"] == "get_sprint_tasks"
    codes = [row["source_id"] for row in result["complete_tasks"]]
    assert len(codes) == 100
    assert len(set(codes)) == 100


@pytest.mark.asyncio
async def test_properly_paginated_source_is_complete_via_primary(monkeypatch):
    # A source whose get_sprint_tasks truly paginates: no TQL needed.
    first_100 = [f"DMS-{i}" for i in range(1, 101)]
    extra_4 = [f"DMS-{i}" for i in range(101, 105)]
    pages = {0: _page(_sprint_rows(first_100), has_next=True),
             1: _page(_sprint_rows(extra_4), has_next=False)}
    client = ScriptedClient(sprint=lambda page: pages.get(page, pages[1]), tql_pages=[])
    _install(monkeypatch, client)

    result = await swtr_read.get_sprint_tasks(
        sprint_id="DMS-SPRNT-1", space=None, page=0, limit=100,
        complete=True, max_pages=50,
    )

    codes = [row["source_id"] for row in result["complete_tasks"]]
    assert len(codes) == 104
    assert len(set(codes)) == 104
    assert result["complete"] is True
    assert result["membership_proven"] is True
    assert result["source_path"] == "get_sprint_tasks"
    assert all(row["sprint_id"] == "DMS-SPRNT-1" for row in result["complete_tasks"])
    assert client.tql_calls == 0


@pytest.mark.asyncio
async def test_small_sprint_single_page_is_complete(monkeypatch):
    codes = [f"DMS-{i}" for i in range(1, 11)]
    client = ScriptedClient(sprint=lambda page: _page(_sprint_rows(codes), has_next=False), tql_pages=[])
    _install(monkeypatch, client)

    result = await swtr_read.get_sprint_tasks(
        sprint_id="DMS-SPRNT-2", space=None, page=0, limit=100,
        complete=True, max_pages=50,
    )

    assert result["complete"] is True
    assert result["membership_proven"] is True
    assert result["source_path"] == "get_sprint_tasks"
    assert [row["source_id"] for row in result["complete_tasks"]] == codes
    assert all(row["sprint_id"] == "DMS-SPRNT-2" for row in result["complete_tasks"])
    assert client.tql_calls == 0


@pytest.mark.asyncio
async def test_tql_smaller_than_primary_is_not_swapped(monkeypatch):
    # TQL returns a different, smaller set; swapping would lose data.
    first_100 = [f"DMS-{i}" for i in range(1, 101)]
    smaller = [f"OLP-{i}" for i in range(1, 51)]
    stuck_page = _page(_sprint_rows(first_100), has_next=True)
    client = ScriptedClient(
        sprint=lambda page: stuck_page,
        tql_pages=[_page(_tql_rows(smaller), has_next=False)],
    )
    _install(monkeypatch, client)

    result = await swtr_read.get_sprint_tasks(
        sprint_id="DMS-SPRNT-1", space=None, page=0, limit=100,
        complete=True, max_pages=50,
    )

    assert result["complete"] is False
    assert result["source_path"] == "get_sprint_tasks"
    codes = [row["source_id"] for row in result["complete_tasks"]]
    assert len(codes) == 100
    assert "OLP-1" not in codes