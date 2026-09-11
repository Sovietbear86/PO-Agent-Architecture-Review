import asyncio

import pytest

from po_agent.harness.agent_core_v4 import V4ContractError, V4Observation
from po_agent.harness.agent_core_v4_reliable import ReliableAgentCoreV4Runtime
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry


class DummyLLM:
    async def complete(self, messages, **kwargs):
        raise AssertionError((messages, kwargs))


class DummyLegacyCapabilities:
    async def execute(self, capability_id, args):
        raise AssertionError((capability_id, args))


class SprintAdapter:
    def __init__(self):
        self.calls = []
        self.context_tasks = []

    async def search_tasks(self, query, **kwargs):
        self.calls.append((query, kwargs))
        Task = type("Task", (), {})
        one = Task()
        one.sprint_id = "DMS-SPRNT-1"
        two = Task()
        two.sprint_id = "DMS-SPRNT-7"
        return [one, two]

    async def get_sprint_tasks(self, sprint_id, space=None):
        del sprint_id, space
        return list(self.context_tasks)


def _team():
    return TeamDirectory((
        TeamDirectoryEntry(login="Moiseev.A.N", full_name="Андрей Моисеев", products=("DMS", "OLP")),
        TeamDirectoryEntry(login="Garanin.R.V", full_name="Родион Гаранин", products=("DMS",)),
    ))


def _runtime(adapter=None):
    return ReliableAgentCoreV4Runtime(
        adapter or SprintAdapter(),
        llm=DummyLLM(),
        model="test-model",
        team=_team(),
        legacy_capabilities=DummyLegacyCapabilities(),
        max_steps=8,
    )


def test_inflected_full_name_can_be_normalized_only_through_unique_team_scope() -> None:
    runtime = _runtime()
    assert len(runtime._team_candidates("Андрея Моисеева")) == 1
    assert runtime._team_candidates("Андрея Моисеева")[0].login == "Moiseev.A.N"
    assert runtime._reference_is_safe_normalization(
        "Андрей Моисеев",
        "Открытые задачи Андрея Моисеева в DMS",
    )


def test_canonical_assignee_literal_is_accepted_only_when_present_in_trusted_observation() -> None:
    runtime = _runtime()
    observations = [
        V4Observation(
            step=1,
            capability_id="member.resolve",
            arguments={"reference": "Андрея Моисеева"},
            answer="Пользователь подтверждён: Moiseev.A.N.",
            data={"member_login": "Moiseev.A.N", "source": "REAL_AS21"},
        )
    ]

    runtime._validate_call_literals(
        "task.search",
        {"assignee": "Moiseev.A.N", "space": "DMS"},
        "Открытые задачи Андрея Моисеева в DMS",
        observations,
    )

    with pytest.raises(V4ContractError):
        runtime._validate_call_literals(
            "task.search",
            {"assignee": "Invented.X.Y", "space": "DMS"},
            "Открытые задачи Андрея Моисеева в DMS",
            observations,
        )


def test_context_scoped_identity_resolution_can_disambiguate_unseen_person_from_sprint_rows() -> None:
    adapter = SprintAdapter()
    Task = type("Task", (), {})
    first = Task()
    first.assignee = "Александра Гончарова"
    first.assignee_login = "goncharova.a.s"
    first.assignee_id = "goncharova.a.s"
    second = Task()
    second.assignee = "Матвей Кузнецов"
    second.assignee_login = "kuznetsov.m.se"
    second.assignee_id = "kuznetsov.m.se"
    adapter.context_tasks = [first, second]
    runtime = _runtime(adapter)

    resolved = asyncio.run(
        runtime._resolve_identity_in_task_context(
            "Гончарова",
            sprint_id="OLP-SPRNT-5",
            space="OLP",
        )
    )

    assert resolved == "goncharova.a.s"


def test_current_sprint_uses_quoted_space_and_full_collection() -> None:
    adapter = SprintAdapter()
    runtime = _runtime(adapter)

    result = asyncio.run(runtime._sprint_current_source_backed({"product": "DMS"}))

    assert adapter.calls == [('project = "DMS"', {"max_results": 10000})]
    assert result.data["sprint_id"] == "DMS-SPRNT-7"
    assert result.data["source"] == "REAL_AS21"
