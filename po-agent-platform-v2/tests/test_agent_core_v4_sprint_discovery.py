"""Focused tests for Agent Core v4 generic sprint discovery/list (Assignment 183, Phase 2).

Covers:
- sprint.search period resolution (one / multiple / zero matches, typed ambiguity);
- sprint.list collection capability (all / active-only / deleted / empty);
- the plural-governance cardinality guard: a plural sprint request must not be
  silently answered by the singleton sprint.current skill;
- the generic period normalization (lexical, entity-agnostic).
"""
from __future__ import annotations

import asyncio

import pytest

from po_agent.harness.agent_core_v4 import (
    AgentCoreV4Runtime,
    V4CapabilityUnavailable,
    V4NeedsClarification,
)
from po_agent.harness.agent_core_v4_reliable import ReliableAgentCoreV4Runtime
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry
from po_agent.harness.sprint_period import parse_period, sprint_overlaps_period

_AUG = {"code": "DMS-SPRNT-2", "status": "IN_PROGRESS",
        "start_at": "2026-08-16T21:00:00Z", "finish_at": "2026-08-30T21:00:00Z",
        "deleted": False, "space": "DMS", "source": "REAL_AS21"}
_AUG_ALT = {"code": "DMS-SPRNT-9", "status": "NEW",
            "start_at": "2026-08-25T21:00:00Z", "finish_at": "2026-09-05T21:00:00Z",
            "deleted": False, "space": "DMS", "source": "REAL_AS21"}
_APR = {"code": "DMS-SPRNT-1", "status": "FINISHED",
        "start_at": "2026-04-12T21:00:00Z", "finish_at": "2026-04-26T21:00:00Z",
        "deleted": False, "space": "DMS", "source": "REAL_AS21"}
_MAY = {"code": "DMS-SPRNT-3", "status": "NEW",
        "start_at": "2026-05-01T21:00:00Z", "finish_at": "2026-05-15T21:00:00Z",
        "deleted": False, "space": "DMS", "source": "REAL_AS21"}


class SprintDirectoryAdapter:
    def __init__(self, sprints):
        self._sprints = list(sprints)
        self.calls = []

    async def list_sprints(self, space):
        self.calls.append(("list_sprints", space))
        return [dict(s) for s in self._sprints if s["space"] == space]

    async def get_sprint_tasks(self, sprint_id, space=None):
        return []

    async def get_current_sprint_id(self, space):
        return None

    async def get_task(self, task_key):
        return None


class DummyLLM:
    async def complete(self, messages, **kwargs):
        raise AssertionError((messages, kwargs))


class DummyLegacyCapabilities:
    async def execute(self, capability_id, args):
        raise AssertionError((capability_id, args))


def _team():
    return TeamDirectory((
        TeamDirectoryEntry(login="Zhdanov.A.Ni", full_name="Александр Жданов", products=("DMS",)),
    ))


def _runtime(adapter):
    return ReliableAgentCoreV4Runtime(
        adapter,
        llm=DummyLLM(),
        model="test-model",
        team=_team(),
        legacy_capabilities=DummyLegacyCapabilities(),
        max_steps=8,
    )


# --- sprint.search period resolution ----------------------------------------

def test_sprint_search_one_match_returns_canonical_sprint():
    adapter = SprintDirectoryAdapter([_AUG, _APR])
    runtime = _runtime(adapter)
    result = asyncio.run(runtime._sprint_search({"space": "DMS", "period": "августовский спринт"}))
    assert result.data["sprint_id"] == "DMS-SPRNT-2"
    assert result.data["space"] == "DMS"
    assert result.data["source"] == "REAL_AS21"
    assert adapter.calls == [("list_sprints", "DMS")]


def test_sprint_search_multiple_matches_returns_typed_ambiguity():
    runtime = _runtime(SprintDirectoryAdapter([_AUG, _AUG_ALT]))
    with pytest.raises(V4NeedsClarification) as exc:
        asyncio.run(runtime._sprint_search({"space": "DMS", "period": "август"}))
    assert sorted(exc.value.options) == ["DMS-SPRNT-2", "DMS-SPRNT-9"]


def test_sprint_search_zero_matches_is_typed_not_found():
    runtime = _runtime(SprintDirectoryAdapter([_AUG]))
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._sprint_search({"space": "DMS", "period": "январь"}))


def test_sprint_search_unparseable_period_clarifies():
    runtime = _runtime(SprintDirectoryAdapter([_AUG]))
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._sprint_search({"space": "DMS", "period": "DMS-SPRNT-2"}))


def test_sprint_search_requires_approved_space():
    runtime = _runtime(SprintDirectoryAdapter([_AUG]))
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._sprint_search({"space": "EVIL", "period": "август"}))


def test_sprint_search_fails_closed_without_sprint_directory():
    class NoDirectory:
        pass

    runtime = _runtime(NoDirectory())
    with pytest.raises(V4CapabilityUnavailable):
        asyncio.run(runtime._sprint_search({"space": "DMS", "period": "август"}))


# --- sprint.list collection capability --------------------------------------

def test_sprint_list_returns_full_collection_not_singleton():
    runtime = _runtime(SprintDirectoryAdapter([_APR, dict(_AUG), dict(_MAY)]))
    result = asyncio.run(runtime._sprint_list({"space": "DMS"}))
    assert result.data["count"] == 3
    assert {row["code"] for row in result.data["sprints"]} == {"DMS-SPRNT-1", "DMS-SPRNT-2", "DMS-SPRNT-3"}
    assert result.data["source"] == "REAL_AS21"


def test_sprint_list_active_only_drops_finished():
    runtime = _runtime(SprintDirectoryAdapter([_APR, dict(_AUG), dict(_MAY)]))
    result = asyncio.run(runtime._sprint_list({"space": "DMS", "active_only": "true"}))
    # _APR is FINISHED -> excluded; the two non-closed sprints remain
    assert {row["code"] for row in result.data["sprints"]} == {"DMS-SPRNT-2", "DMS-SPRNT-3"}


def test_sprint_list_drops_deleted_rows():
    runtime = _runtime(SprintDirectoryAdapter([_APR, dict(_AUG, deleted=True)]))
    result = asyncio.run(runtime._sprint_list({"space": "DMS"}))
    assert [row["code"] for row in result.data["sprints"]] == ["DMS-SPRNT-1"]


def test_sprint_list_empty_is_typed():
    runtime = _runtime(SprintDirectoryAdapter([]))
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._sprint_list({"space": "DMS"}))


def test_sprint_list_requires_approved_space():
    runtime = _runtime(SprintDirectoryAdapter([_APR]))
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._sprint_list({"space": "EVIL"}))


# --- plural governance cardinality guard ------------------------------------

def test_plural_sprint_request_is_routed_away_from_singleton_current():
    runtime = _runtime(SprintDirectoryAdapter([_APR, dict(_AUG)]))
    assert runtime._reconcile_loaded_skill("sprint.current", "Активные спринты в DMS") == "sprint.list"
    assert runtime._reconcile_loaded_skill("sprint.current", "Текущий спринт DMS") == "sprint.current"
    assert runtime._reconcile_loaded_skill("tasks.search", "Активные спринты в DMS") == "tasks.search"


def test_cardinality_detector_distinguishes_plural_from_singular():
    detect = AgentCoreV4Runtime.query_requests_sprint_collection
    assert detect("Активные спринты в DMS") is True
    assert detect("Сколько активных спринтов в DMS?") is True
    assert detect("Список спринтов DMS") is True
    assert detect("Текущий спринт DMS") is False
    assert detect("Покажи открытые задачи в спринте DMS-SPRNT-2") is False
    assert detect("Какой сейчас спринт в DMS") is False


# --- generic period normalization (lexical, entity-agnostic) -----------------

def test_parse_period_recognizes_common_forms():
    assert parse_period("августовский спринт") == (8, None)
    assert parse_period("август") == (8, None)
    assert parse_period("август 2026") == (8, 2026)
    assert parse_period("2026-08") == (8, 2026)
    assert parse_period("08.2026") == (8, 2026)
    assert parse_period("December") == (12, None)
    assert parse_period("DMS-SPRNT-2") == (None, None)


def test_overlap_respects_source_period_and_year():
    assert sprint_overlaps_period(_AUG, 8, None) is True
    assert sprint_overlaps_period(_AUG, 8, 2026) is True
    assert sprint_overlaps_period(_AUG, 8, 2025) is False
    assert sprint_overlaps_period(_APR, 8, None) is False
    # a sprint without a readable period can never be proven to match
    assert sprint_overlaps_period({"code": "X", "start_at": None, "finish_at": None}, 8, None) is False