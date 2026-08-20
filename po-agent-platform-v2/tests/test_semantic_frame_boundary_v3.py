from __future__ import annotations

import json

import pytest

from po_agent.harness.semantic_core_v2 import LLMFirstSemanticInterpreter
from po_agent.llm.client import LLMChoice, LLMMessage, LLMResponse


class QueueClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)

    async def complete(self, messages, **kwargs):
        payload = self.payloads.pop(0)
        return LLMResponse(choices=[LLMChoice(message=LLMMessage(role="assistant", content=json.dumps(payload, ensure_ascii=False)))])


def ctx():
    return {
        "allowed_intents": ["task_search", "task_lookup", "sprint_health"],
        "available_capabilities": [{"intent": "task_search", "skill_id": "task-search"}],
    }


@pytest.mark.asyncio
async def test_audit_restores_person_constraint_dropped_by_first_pass():
    client = QueueClient([
        {
            "canonical_query": "tasks in sprint",
            "intent_hint": "task_search",
            "slots": {"sprint_id": "DMS-SPRNT-1"},
            "clarifications": [],
            "confidence": 0.8,
            "dialogue_act": "new",
        },
        {
            "intent_hint": "task_search",
            "slots": {"person_raw": "Гаранина", "sprint_id": "DMS-SPRNT-1"},
            "clarifications": [],
            "confidence": 0.98,
            "audit_ok": True,
        },
    ])
    frame = await LLMFirstSemanticInterpreter(client).interpret(
        "Что висит на Гаранине в спринте DMS-SPRNT-1?", context=ctx()
    )
    assert frame.slots["person_raw"] == "Гаранина"
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"


@pytest.mark.asyncio
async def test_audit_preserves_all_multifilter_constraints():
    client = QueueClient([
        {
            "canonical_query": "search",
            "intent_hint": "task_search",
            "slots": {"person_raw": "Моисеева", "product": "DMS"},
            "clarifications": [],
            "confidence": 0.7,
            "dialogue_act": "new",
        },
        {
            "intent_hint": "task_search",
            "slots": {
                "person_raw": "Моисеева",
                "product": "DMS",
                "sprint_id": "DMS-SPRNT-2",
                "status": "OPEN",
            },
            "clarifications": [],
            "confidence": 0.99,
            "audit_ok": True,
        },
    ])
    frame = await LLMFirstSemanticInterpreter(client).interpret(
        "Покажи OPEN-задачи Моисеева в DMS-SPRNT-2", context=ctx()
    )
    assert frame.slots["person_raw"] == "Моисеева"
    assert frame.slots["product"] == "DMS"
    assert frame.slots["sprint_id"] == "DMS-SPRNT-2"
    assert frame.slots["status"] == "OPEN"


@pytest.mark.asyncio
async def test_structural_overlay_overrides_sentence_accidentally_put_in_sprint_id():
    bad_sentence = "ПОКАЖИ ЗАДАЧИ ГАРАНИНА В DMS-SPRNT-1"
    client = QueueClient([
        {
            "canonical_query": "search",
            "intent_hint": "task_search",
            "slots": {"person_raw": "Гаранина", "sprint_id": bad_sentence},
            "clarifications": [],
            "confidence": 0.9,
            "dialogue_act": "new",
        },
        {
            "intent_hint": "task_search",
            "slots": {"person_raw": "Гаранина", "sprint_id": bad_sentence},
            "clarifications": [],
            "confidence": 0.9,
            "audit_ok": False,
        },
    ])
    frame = await LLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS-SPRNT-1", context=ctx()
    )
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"


@pytest.mark.asyncio
async def test_sprint_suffix_is_never_interpreted_as_task_key():
    client = QueueClient([
        {
            "canonical_query": "search",
            "intent_hint": "task_search",
            "slots": {"task_key": "SPRNT-1", "person_raw": "Гаранин"},
            "clarifications": [],
            "confidence": 0.9,
            "dialogue_act": "new",
        },
        {
            "intent_hint": "task_search",
            "slots": {"task_key": "SPRNT-1", "person_raw": "Гаранин"},
            "clarifications": [],
            "confidence": 0.9,
            "audit_ok": True,
        },
    ])
    frame = await LLMFirstSemanticInterpreter(client).interpret(
        "DMS-SPRNT-1: что у Гаранина?", context=ctx()
    )
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"
    assert "task_key" not in frame.slots
