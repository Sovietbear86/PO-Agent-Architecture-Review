import asyncio
from types import SimpleNamespace

import pytest

from po_agent.domain.models import StatusCategory, TaskStatus
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
        self.current_sprint = "DMS-SPRNT-7"
        self.task = None

    async def search_tasks(self, query, **kwargs):
        raise AssertionError("sprint.current must never use generic/local-cache search_tasks")

    async def get_current_sprint_id(self, space):
        self.calls.append(("get_current_sprint_id", space))
        return self.current_sprint

    async def get_sprint_tasks(self, sprint_id, space=None):
        del sprint_id, space
        return list(self.context_tasks)

    async def get_task(self, task_key):
        self.calls.append(("get_task", task_key))
        return self.task


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


def test_unrelated_surname_with_common_prefix_is_not_normalized_to_real_team_member() -> None:
    runtime = _runtime()
    assert runtime._team_candidates("Гарановых") == ()


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


def test_task_lookup_exposes_canonical_assignee_for_downstream_binding() -> None:
    adapter = SprintAdapter()
    adapter.task = SimpleNamespace(
        key="DMS-380",
        id="DMS-380",
        title="Lineager auth",
        description="details",
        status=TaskStatus.QA,
        status_category=StatusCategory.TESTING,
        assignee="Семавин Михаил Михайлович",
        assignee_id="Semavin.M.M",
        assignee_login="Semavin.M.M",
        project_space="DMS",
        sprint_id="DMS-SPRNT-1",
        release_id=None,
        source="swtr",
    )
    runtime = _runtime(adapter)

    result = asyncio.run(runtime._task_lookup_source_backed({"task_key": "DMS-380"}))

    assert adapter.calls == [("get_task", "DMS-380")]
    assert result.data["assignee_login"] == "Semavin.M.M"
    assert result.data["task"]["assignee_login"] == "Semavin.M.M"

    observation = V4Observation(
        step=1,
        capability_id="task.lookup",
        arguments={"task_key": "DMS-380"},
        answer=result.answer,
        data=result.data,
    )
    runtime._validate_call_literals(
        "task.search",
        {"assignee": "semavin.m.m"},
        "Покажи DMS-380 и затем задачи его исполнителя",
        [observation],
    )


def test_current_sprint_uses_authoritative_live_method_and_never_generic_search() -> None:
    adapter = SprintAdapter()
    runtime = _runtime(adapter)

    result = asyncio.run(runtime._sprint_current_source_backed({"product": "DMS"}))

    assert adapter.calls == [("get_current_sprint_id", "DMS")]
    assert result.data["sprint_id"] == "DMS-SPRNT-7"
    assert result.data["source"] == "REAL_AS21"


def test_current_sprint_not_found_remains_explicit_real_source_empty_state() -> None:
    adapter = SprintAdapter()
    adapter.current_sprint = None
    runtime = _runtime(adapter)

    result = asyncio.run(runtime._sprint_current_source_backed({"product": "DMS"}))

    assert adapter.calls == [("get_current_sprint_id", "DMS")]
    assert result.data["sprint_id"] is None
    assert result.warnings == ["current_sprint_not_found"]
