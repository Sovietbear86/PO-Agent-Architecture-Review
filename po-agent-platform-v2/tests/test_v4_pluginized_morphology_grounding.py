from __future__ import annotations

import pytest

from po_agent.harness.agent_core_v4 import V4ContractError
from po_agent.harness.agent_core_v4_pluginized import PluginizedRobustReliableAgentCoreV4Runtime
from po_agent.harness.entity_grounding import TeamDirectory, TeamDirectoryEntry


class _DummyLLM:
    async def complete(self, messages, **kwargs):
        raise AssertionError((messages, kwargs))


class _DummyAdapter:
    async def search_tasks(self, *args, **kwargs):
        raise AssertionError((args, kwargs))


class _DummyLegacy:
    async def execute(self, capability_id, args):
        raise AssertionError((capability_id, args))


def _runtime() -> PluginizedRobustReliableAgentCoreV4Runtime:
    team = TeamDirectory(
        (
            TeamDirectoryEntry(login="Zhdanov.A.Ni", full_name="Александр Жданов", products=("DMS",)),
            TeamDirectoryEntry(login="Garanin.R.V", full_name="Родион Гаранин", products=("DMS",)),
        )
    )
    return PluginizedRobustReliableAgentCoreV4Runtime(
        _DummyAdapter(),
        llm=_DummyLLM(),
        model="test-model",
        team=team,
        legacy_capabilities=_DummyLegacy(),
        max_steps=8,
    )


@pytest.mark.parametrize(
    ("query", "reference"),
    [
        ("Задачи Александра Жданова в DMS", "Александр Жданов"),
        ("Покажи задачи Александру Жданову в DMS", "Александр Жданов"),
        ("Задачи Родиона Гаранина в DMS", "Родион Гаранин"),
        ("Покажи задачи Родиону Гаранину в DMS", "Родион Гаранин"),
    ],
)
def test_plugin_reference_accepts_safe_russian_morphology(query: str, reference: str) -> None:
    runtime = _runtime()
    runtime._validate_call_literals(
        "task.search_assignee",
        {"reference": reference, "space": "DMS"},
        query,
        [],
    )


def test_plugin_reference_still_rejects_invented_person() -> None:
    runtime = _runtime()
    with pytest.raises(V4ContractError):
        runtime._validate_call_literals(
            "task.search_assignee",
            {"reference": "Несуществующий Человек", "space": "DMS"},
            "Задачи Александра Жданова в DMS",
            [],
        )


def test_non_reference_literal_guards_remain_intact() -> None:
    runtime = _runtime()
    with pytest.raises(V4ContractError):
        runtime._validate_call_literals(
            "task.search_assignee",
            {"reference": "Александр Жданов", "space": "WMB"},
            "Задачи Александра Жданова в DMS",
            [],
        )
