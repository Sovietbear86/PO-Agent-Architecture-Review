"""Focused tests for Agent Core v4 source-backed identity governance (Assignment 183, Phase 3).

Assignment 182 showed a person absent from the local roster (e.g. "Петр Иванов",
a genitive mention "Петра Иванова" in the query) can be resolved by REAL AS21
`member.resolve`, yet the downstream local-roster / query-derived guard could
still veto the reference before it reached the source resolver.

The fix is generalized (no surname/person/roster special cases):
- a person reference grounded in the user's own (possibly inflected) text may be
  passed to the governed REAL member.resolve resolver;
- the local roster is a non-production hint and must not veto a REAL-AS21
  identity;
- anti-invention is preserved: a reference/identity with no source observation
  and no grounding in the query is still rejected;
- the Assignment 178 cross-name false positive stays closed.
"""
from __future__ import annotations

import asyncio

import httpx
import pytest

from po_agent.harness.agent_core_v4 import V4ContractError, V4NeedsClarification, V4Observation
from po_agent.harness.agent_core_v4_reliable import ReliableAgentCoreV4Runtime
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry


class DummyLLM:
    async def complete(self, *a, **k):
        raise AssertionError((a, k))


class DummyLegacy:
    async def execute(self, *a, **k):
        raise AssertionError((a, k))


def _team():
    return TeamDirectory((
        TeamDirectoryEntry(login="Zhdanov.A.Ni", full_name="Александр Жданов", products=("DMS",)),
        TeamDirectoryEntry(login="Garanin.R.V", full_name="Родион Гаранин", products=("DMS",)),
    ))


class _NoAdapter:
    pass


def _runtime(adapter=None):
    return ReliableAgentCoreV4Runtime(
        adapter or _NoAdapter(),
        llm=DummyLLM(),
        model="test-model",
        team=_team(),
        legacy_capabilities=DummyLegacy(),
        max_steps=8,
    )


def _member_observation(login: str, reference: str) -> V4Observation:
    return V4Observation(
        step=1,
        capability_id="member.resolve",
        arguments={"reference": reference},
        answer=f"Пользователь подтверждён: {login}.",
        data={
            "reference": reference,
            "member_login": login,
            "external_id": login,
            "source": "REAL_AS21",
        },
    )


# 1. person absent from the local roster but resolvable by REAL source --------

def test_genitive_to_nominative_person_reference_passes_guard():
    runtime = _runtime()
    # "Петр Иванов" is NOT in the local roster, but is grounded in the query
    # (genitive "Петра Иванова"). The reference guard must not veto it.
    runtime._validate_call_literals(
        "member.resolve",
        {"reference": "Петр Иванов", "sprint_id": "DMS-SPRNT-2"},
        "Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2",
        [],
    )


def test_real_resolved_non_roster_login_flows_into_task_search():
    runtime = _runtime()
    observations = [_member_observation("Ivanov.P.Se", "Петр Иванов")]
    runtime._validate_call_literals(
        "task.search",
        {"assignee": "Ivanov.P.Se", "sprint_id": "DMS-SPRNT-2", "status": "not_completed"},
        "Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2",
        observations,
    )


# 2. unresolved/ambiguous person still fails closed (source 409 path) ---------

def test_member_resolve_source_ambiguity_clarifies():
    class AmbiguousAdapter:
        async def _get_resilient(self, path, params=None):
            resp = httpx.Response(
                409,
                request=httpx.Request("GET", path),
                json={"detail": {"message": "ambiguous", "matches": ["Ivanov.P.Se", "Ivanova.P.A"]}},
            )
            resp.raise_for_status()
            return resp

    runtime = _runtime(AmbiguousAdapter())
    with pytest.raises(V4NeedsClarification):
        asyncio.run(runtime._resolve_source_login("Петр Иванов"))


def test_member_resolve_source_unavailable_is_typed():
    import asyncio as _asyncio

    from po_agent.adapters.task_api import AS21SourceUnavailable

    class DownAdapter:
        async def _get_resilient(self, path, params=None):
            raise AS21SourceUnavailable("resolver unavailable")

    runtime = _runtime(DownAdapter())
    with pytest.raises(AS21SourceUnavailable):
        _asyncio.run(runtime._resolve_source_login("Петр Иванов"))


# 3. invented identity without a source observation is still rejected ----------

def test_invented_assignee_without_observation_is_rejected():
    runtime = _runtime()
    with pytest.raises(V4ContractError):
        runtime._validate_call_literals(
            "task.search", {"assignee": "Totally.Invented.X"}, "Покажи задачи", []
        )


def test_invented_person_reference_not_in_query_is_rejected():
    runtime = _runtime()
    assert runtime._reference_is_query_derived_person("Ivan Ivanov", "Покажи задачи") is False
    with pytest.raises(V4ContractError):
        runtime._validate_call_literals("member.resolve", {"reference": "Ivan Ivanov"}, "Покажи задачи", [])


def test_partially_grounded_reference_is_rejected():
    runtime = _runtime()
    # only "Петр" is grounded in the query; "Кузнецов" is not -> not safe
    assert runtime._reference_is_query_derived_person("Петр Кузнецов", "Задачи Петра Иванова") is False


# 4. Assignment 178 cross-name false positive stays closed ---------------------

def test_inflected_name_is_not_normalized_to_unrelated_roster_member():
    runtime = _runtime()
    # "Гарановых" (a different, inflected surname) must not normalize to "Гаранин"
    assert runtime._reference_is_query_derived_person("Гаранин", "Задачи Гарановых") is False


def test_roster_member_still_resolves_when_uniquely_team_scoped():
    runtime = _runtime()
    # A roster member's inflected name is still team-scoped (unchanged behavior).
    assert len(runtime._team_candidates("Гаранина")) == 1
    assert runtime._team_candidates("Гаранина")[0].login == "Garanin.R.V"


# --- direct guard behavior ----------------------------------------------------

def test_reference_guard_accepts_query_grounded_person():
    runtime = _runtime()
    assert runtime._reference_is_safe_normalization(
        "Петр Иванов", "Покажи открытые задачи Петра Иванова в спринте DMS-SPRNT-2"
    ) is True


def test_reference_guard_rejects_ungrounded_person():
    runtime = _runtime()
    assert runtime._reference_is_safe_normalization("Ivan Ivanov", "Покажи задачи") is False