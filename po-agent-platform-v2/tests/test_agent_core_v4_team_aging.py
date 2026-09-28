from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from po_agent.adapters.task_api import AS21SourceUnavailable
from po_agent.harness.v4_plugins import _task_live_handlers as handlers


def _task(key: str, *, assignee: str, age: int):
    return SimpleNamespace(
        key=key,
        title=key,
        status=SimpleNamespace(value="In progress"),
        assignee=assignee,
        age_days=age,
        is_open=True,
        source_data={"_canonical_created_at_from_source": True},
    )


def test_team_scoped_aging_uses_configured_member_reads_and_deduplicates(monkeypatch):
    monkeypatch.setattr(handlers, "get_all_member_logins", lambda: ["alice", "bob"])

    async def fake_rows(runtime, *, phrase=None, space=None, assignee=None):
        assert space == "WMB"
        if assignee == "alice":
            return [_task("WMB-1", assignee="alice", age=20), _task("WMB-2", assignee="alice", age=4)]
        if assignee == "bob":
            return [_task("WMB-1", assignee="bob", age=20), _task("WMB-3", assignee="bob", age=15)]
        return []

    monkeypatch.setattr(handlers, "_live_rows", fake_rows)
    runtime = SimpleNamespace(adapter=SimpleNamespace())

    result = asyncio.run(
        handlers.build_task_aging(runtime)(
            {"space": "WMB", "threshold_days": "7", "team_scope": "true"}
        )
    )

    assert result.data["team_scope"] is True
    assert result.data["count"] == 2
    assert [row["key"] for row in result.data["tasks"]] == ["WMB-1", "WMB-3"]


def test_team_scoped_aging_fails_closed_if_one_member_read_is_unavailable(monkeypatch):
    monkeypatch.setattr(handlers, "get_all_member_logins", lambda: ["alice", "bob"])

    async def fake_rows(runtime, *, phrase=None, space=None, assignee=None):
        if assignee == "bob":
            raise AS21SourceUnavailable("source down")
        return [_task("WMB-1", assignee="alice", age=20)]

    monkeypatch.setattr(handlers, "_live_rows", fake_rows)
    runtime = SimpleNamespace(adapter=SimpleNamespace())

    with pytest.raises(AS21SourceUnavailable, match="complete assignee reads"):
        asyncio.run(
            handlers.build_task_aging(runtime)(
                {"space": "WMB", "threshold_days": "7", "team_scope": "true"}
            )
        )
