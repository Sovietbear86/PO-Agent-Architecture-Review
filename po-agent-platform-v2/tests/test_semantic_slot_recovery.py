from __future__ import annotations

import json

import pytest

from po_agent.harness.semantic_slot_recovery import RecoveringLLMFirstSemanticInterpreter
from po_agent.llm.client import LLMChoice, LLMMessage, LLMResponse


class QueueClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)

    async def complete(self, messages, **kwargs):
        payload = self.payloads.pop(0)
        return LLMResponse(
            choices=[LLMChoice(message=LLMMessage(role="assistant", content=json.dumps(payload, ensure_ascii=False)))]
        )


def context():
    return {
        "session_id": "slot-recovery",
        "allowed_intents": ["task_search", "task_lookup"],
        "available_capabilities": [
            {
                "intent": "task_search",
                "skill_id": "task-search",
                "domain": "task",
                "description": "Search tasks using filters",
            }
        ],
    }


@pytest.mark.asyncio
async def test_empty_nested_slots_are_recovered_by_flat_llm_pass():
    empty = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {},
        "clarifications": [],
        "confidence": 0.94,
        "dialogue_act": "new",
    }
    recovered = {
        "person_raw": "Гаранина",
        "product": "DMS",
        "status_raw": "todo",
        "sprint_raw": None,
        "release_raw": None,
        "member_login": None,
        "task_key": None,
        "phrase": None,
    }
    # Primary extraction + semantic audit both reproduce the production failure;
    # the dedicated flat recovery call returns literal user constraints.
    client = QueueClient([empty, empty, recovered])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS со статусом todo",
        context=context(),
    )
    assert frame.intent_hint == "task_search"
    assert frame.slots["person_raw"] == "Гаранина"
    assert frame.slots["product"] == "DMS"
    assert frame.slots["status_raw"] == "todo"


@pytest.mark.asyncio
async def test_recovery_rejects_values_not_present_in_original_query():
    empty = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {},
        "clarifications": [],
        "confidence": 0.90,
        "dialogue_act": "new",
    }
    hallucinated = {
        "person_raw": "Петров",
        "product": "OLP",
        "status_raw": "blocked",
        "sprint_raw": None,
        "release_raw": None,
        "member_login": None,
        "task_key": None,
        "phrase": None,
    }
    client = QueueClient([empty, empty, hallucinated])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS",
        context=context(),
    )
    assert frame.slots == {}


@pytest.mark.asyncio
async def test_recovery_does_not_override_nonempty_primary_slots():
    primary = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"person_raw": "Гаранина", "product": "DMS"},
        "clarifications": [],
        "confidence": 0.98,
        "dialogue_act": "new",
    }
    client = QueueClient([primary, primary])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS",
        context=context(),
    )
    assert frame.slots == {"person_raw": "Гаранина", "product": "DMS"}
    assert client.payloads == []
