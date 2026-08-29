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


def empty_frame():
    return {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {},
        "clarifications": [],
        "confidence": 0.94,
        "dialogue_act": "new",
    }


@pytest.mark.asyncio
async def test_empty_nested_slots_are_recovered_by_flat_llm_pass():
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
    client = QueueClient([empty_frame(), empty_frame(), recovered])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS со статусом todo",
        context=context(),
    )
    assert frame.intent_hint == "task_search"
    assert frame.slots["person_raw"] == "Гаранина"
    assert frame.slots["product"] == "DMS"
    assert frame.slots["status_raw"] == "todo"


@pytest.mark.asyncio
async def test_empty_recovery_llm_still_recovers_literal_filters_deterministically():
    # Production 069 reproducer: both primary/audit and recovery LLM omit slots.
    client = QueueClient([empty_frame(), empty_frame(), {}])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS со статусом todo",
        context=context(),
    )
    assert frame.slots["person_raw"] == "Гаранина"
    assert frame.slots["product"] == "DMS"
    assert frame.slots["status_raw"] == "todo"


@pytest.mark.asyncio
async def test_deterministic_recovery_is_not_specific_to_dms_space():
    client = QueueClient([empty_frame(), empty_frame(), {}])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Смирнова в OLP со статусом Open",
        context=context(),
    )
    assert frame.slots["person_raw"] == "Смирнова"
    assert frame.slots["product"] == "OLP"
    assert frame.slots["status_raw"] == "Open"


@pytest.mark.asyncio
async def test_deterministic_recovery_preserves_explicit_sprint_and_filters():
    client = QueueClient([empty_frame(), empty_frame(), {}])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS-SPRNT-2 со статусом todo",
        context=context(),
    )
    assert frame.slots["person_raw"] == "Гаранина"
    assert frame.slots["sprint_id"] == "DMS-SPRNT-2"
    assert frame.slots["status_raw"] == "todo"
    assert "product" not in frame.slots


@pytest.mark.asyncio
async def test_recovery_rejects_llm_values_not_present_in_original_query():
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
    client = QueueClient([empty_frame(), empty_frame(), hallucinated])
    frame = await RecoveringLLMFirstSemanticInterpreter(client).interpret(
        "Покажи задачи Гаранина в DMS",
        context=context(),
    )
    # Hallucinated values are rejected; literal user constraints are recovered.
    assert frame.slots == {"person_raw": "Гаранина", "product": "DMS"}


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


def test_surface_recovery_does_not_guess_unmarked_free_text():
    slots = RecoveringLLMFirstSemanticInterpreter._deterministic_surface_slots(
        "Расскажи что-нибудь полезное про команду"
    )
    assert slots == {}
