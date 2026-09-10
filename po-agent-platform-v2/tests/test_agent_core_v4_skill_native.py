import asyncio

from po_agent.harness.agent_core_v4 import (
    AgentCoreV4Runtime,
    SkillNativePlannerV4,
    _literal_is_query_derived,
)
from po_agent.harness.entity_grounding import TeamDirectory
from po_agent.llm.client import LLMChoice, LLMMessage, LLMResponse


class ScriptedLLM:
    def __init__(self, outputs):
        self.outputs = list(outputs)

    async def complete(self, messages, **kwargs):
        del messages, kwargs
        raw = self.outputs.pop(0)
        return LLMResponse(choices=[LLMChoice(message=LLMMessage(role="assistant", content=raw))])


class DummyAdapter:
    pass


class DummyLegacyCapabilities:
    async def execute(self, capability_id, args):
        raise AssertionError((capability_id, args))


def _runtime(llm):
    return AgentCoreV4Runtime(
        DummyAdapter(),
        llm=llm,
        model="test-model",
        team=TeamDirectory(),
        legacy_capabilities=DummyLegacyCapabilities(),
    )


def test_compact_catalog_contains_procedures_not_entity_facts() -> None:
    runtime = _runtime(ScriptedLLM([]))
    catalog = runtime.catalog.compact()
    serialized = str(catalog)

    assert "tasks.search" in serialized
    assert "sprint.health" in serialized
    assert "Гаранин" not in serialized
    assert "Калачанов" not in serialized
    assert "Моисеев" not in serialized
    assert "OLP-SPRNT-5" not in serialized


def test_planner_progressively_loads_skill_from_raw_query_without_semantic_frame() -> None:
    llm = ScriptedLLM([
        '{"load_skill":{"skill_id":"tasks.search"},"call":null,"ready":null,"rationale":"need task search procedure"}',
        '{"load_skill":null,"call":{"capability_id":"member.resolve","arguments":{"reference":"Гончарова"}},"ready":null,"rationale":"resolve person from source"}',
    ])
    runtime = _runtime(llm)
    planner = SkillNativePlannerV4(llm, model="test-model")

    first = asyncio.run(planner.next_decision(
        user_query="Открытые задачи Гончарова в спринте OLP-SPRNT-5",
        catalog=runtime.catalog,
        loaded_skills=(),
        observations=[],
    ))
    assert first.kind == "load_skill"
    assert first.skill_id == "tasks.search"

    second = asyncio.run(planner.next_decision(
        user_query="Открытые задачи Гончарова в спринте OLP-SPRNT-5",
        catalog=runtime.catalog,
        loaded_skills=("tasks.search",),
        observations=[],
    ))
    assert second.kind == "call"
    assert second.capability_id == "member.resolve"
    assert second.arguments == {"reference": "Гончарова"}


def test_literal_guard_allows_inflected_source_reference_but_rejects_unrelated_name() -> None:
    query = "Открытые задачи Гончарова в спринте OLP-SPRNT-5"
    assert _literal_is_query_derived("Гончаров", query)
    assert _literal_is_query_derived("OLP-SPRNT-5", query)
    assert not _literal_is_query_derived("Иванов", query)


def test_loaded_skill_exposes_only_its_governed_capabilities() -> None:
    runtime = _runtime(ScriptedLLM([]))
    allowed = runtime.catalog.allowed_capabilities(("task.quality",))
    assert allowed == frozenset({"task.quality"})
    assert "member.resolve" not in allowed
    assert "task.search" not in allowed
