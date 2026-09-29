from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routers import swtr_query


@pytest.mark.asyncio
async def test_unscoped_phrase_search_isolates_failed_spaces(monkeypatch):
    monkeypatch.setattr(swtr_query, "SWTRMCPClient", lambda: object())

    async def fake_fetch(client, *, space, assignee_external_id, release_id, limit, max_pages):
        if space in {"CRPV", "STS"}:
            raise HTTPException(status_code=502, detail=f"pagination exceeded max_pages for {space}")
        return [{"source_id": f"{space}-1", "title": "БП 2027", "space": space}]

    monkeypatch.setattr(swtr_query, "_fetch_space_rows", fake_fetch)
    monkeypatch.setattr(
        swtr_query,
        "_canonical_row",
        lambda row: {
            "source_id": row["source_id"],
            "title": row["title"],
            "status": "Open",
            "source_data": {},
        },
    )
    monkeypatch.setattr(swtr_query, "_row_text", lambda row, *names: "")

    result = await swtr_query.query_live_tasks(
        phrase="БП 2027",
        space=None,
        assignee=None,
        release=None,
        limit=100,
        max_pages=100,
    )

    assert result["source_complete"] is False
    assert {row["space"] for row in result["incomplete_spaces"]} == {"CRPV", "STS"}
    assert set(result["completed_spaces"]) == {"DMS", "OLP", "WMB"}
    assert {task["source_id"] for task in result["tasks"]} == {"DMS-1", "OLP-1", "WMB-1"}


@pytest.mark.asyncio
async def test_scoped_phrase_search_keeps_failure_strict(monkeypatch):
    monkeypatch.setattr(swtr_query, "SWTRMCPClient", lambda: object())

    async def fake_fetch(client, *, space, assignee_external_id, release_id, limit, max_pages):
        raise HTTPException(status_code=502, detail=f"pagination exceeded max_pages for {space}")

    monkeypatch.setattr(swtr_query, "_fetch_space_rows", fake_fetch)

    with pytest.raises(HTTPException) as exc:
        await swtr_query.query_live_tasks(
            phrase="БП 2027",
            space="WMB",
            assignee=None,
            release=None,
            limit=100,
            max_pages=100,
        )

    assert exc.value.status_code == 502
