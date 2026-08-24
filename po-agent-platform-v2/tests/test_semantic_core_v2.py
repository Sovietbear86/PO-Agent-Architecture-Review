from __future__ import annotations

import json

import pytest

from po_agent.harness.semantic_core_v2 import (
    ConversationAwareSemanticInterpreter,
    FailClosedSemanticInterpreter,
    LLMFirstSemanticInterpreter,
)
from po_agent.llm.client import LLMChoice, LLMMessage, LLMResponse


class QueueClient:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.seen = []

    async def complete(self, messages, **kwargs):
        self.seen.append(messages)
        payload = self.payloads.pop(0)
        return LLMResponse(choices=[LLMChoice(message=LLMMessage(role="assistant", content=json.dumps(payload, ensure_ascii=False)))])


def context():
    return {
        "session_id": "s1",
        "allowed_intents": ["task_search", "task_lookup", "sprint_health"],
        "available_capabilities": [
            {"intent": "task_search", "skill_id": "task-search", "domain": "task", "description": "Search tasks using filters"},
            {"intent": "task_lookup", "skill_id": "task-lookup", "domain": "task", "description": "Open exact task"},
            {"intent": "sprint_health", "skill_id": "sprint-health", "domain": "sprint", "description": "Sprint health"},
        ],
    }


@pytest.mark.asyncio
async def test_natural_language_slots_come_from_llm_not_magic_keywords():
    client = QueueClient([{
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"person_raw": "Моисеев Андрей", "product": "DMS", "status": "OPEN"},
        "clarifications": [],
        "confidence": 0.97,
        "dialogue_act": "new",
    }])
    interpreter = LLMFirstSemanticInterpreter(client)
    frame = await interpreter.interpret(
        "Привет! покажи, что сейчас есть у пользователя Моисеев Андрей в пространстве DMS со статусом OPEN",
        context=context(),
    )
    assert frame.intent_hint == "task_search"
    assert frame.slots["person_raw"] == "Моисеев Андрей"
    assert frame.slots["product"] == "DMS"
    assert frame.slots["status"] == "OPEN"


@pytest.mark.asyncio
async def test_structural_overlay_preserves_full_sprint_without_language_routing():
    client = QueueClient([{
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"task_key": "SPRNT-1", "person_raw": "Гаранина"},
        "clarifications": [],
        "confidence": 0.95,
        "dialogue_act": "new",
    }])
    interpreter = LLMFirstSemanticInterpreter(client)
    frame = await interpreter.interpret("Что висит у Гаранина в DMS-SPRNT-1?", context=context())
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"
    assert "task_key" not in frame.slots
    assert frame.slots["person_raw"] == "Гаранина"


@pytest.mark.asyncio
async def test_contract_repair_replaces_full_query_raw_slot_with_compact_surface_value():
    query = "Покажи карточки со статусом blocked"
    invalid = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"status_raw": query},
        "clarifications": [],
        "confidence": 0.90,
        "dialogue_act": "new",
    }
    repaired = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"status_raw": "blocked"},
        "clarifications": [],
        "confidence": 0.96,
        "dialogue_act": "new",
    }
    client = QueueClient([invalid, invalid, repaired])
    frame = await LLMFirstSemanticInterpreter(client).interpret(query, context=context())
    assert frame.slots == {"status_raw": "blocked"}
    assert not frame.clarifications


@pytest.mark.asyncio
async def test_contract_repair_restores_raw_person_instead_of_derived_member_login():
    query = "Что назначено Петровой в CRM?"
    invalid = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"member_login": "Petrova.A.A", "product": "CRM"},
        "clarifications": [],
        "confidence": 0.91,
        "dialogue_act": "new",
    }
    repaired = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"person_raw": "Петровой", "product": "CRM"},
        "clarifications": [],
        "confidence": 0.97,
        "dialogue_act": "new",
    }
    client = QueueClient([invalid, invalid, repaired])
    frame = await LLMFirstSemanticInterpreter(client).interpret(query, context=context())
    assert frame.slots["person_raw"] == "Петровой"
    assert frame.slots["product"] == "CRM"
    assert "member_login" not in frame.slots


@pytest.mark.asyncio
async def test_unrepaired_contract_violation_fails_closed_instead_of_broadening():
    query = "Покажи карточки со статусом blocked"
    invalid = {
        "canonical_query": "search tasks",
        "intent_hint": "task_search",
        "slots": {"status_raw": query},
        "clarifications": [],
        "confidence": 0.90,
        "dialogue_act": "new",
    }
    client = QueueClient([invalid, invalid, invalid])
    frame = await LLMFirstSemanticInterpreter(client).interpret(query, context=context())
    assert "status_raw" not in frame.slots
    assert any(need.field == "semantic_contract" for need in frame.clarifications)


@pytest.mark.asyncio
async def test_conversation_context_is_supplied_to_next_semantic_turn():
    client = QueueClient([
        {
            "canonical_query": "search tasks",
            "intent_hint": "task_search",
            "slots": {"person_raw": "Гаранин", "product": "DMS"},
            "clarifications": [],
            "confidence": 0.95,
            "dialogue_act": "new",
        },
        {
            "canonical_query": "search tasks",
            "intent_hint": "task_search",
            "slots": {"person_raw": "Моисеев", "product": "DMS"},
            "clarifications": [],
            "confidence": 0.96,
            "dialogue_act": "correction",
        },
    ])
    interpreter = ConversationAwareSemanticInterpreter(LLMFirstSemanticInterpreter(client))
    await interpreter.interpret("Покажи задачи Гаранина по DMS", context=context())
    second = await interpreter.interpret("Опечатался, я имел в виду Моисеева", context=context())
    second_user_payload = json.loads(client.seen[1][-1].content)
    assert second_user_payload["context"]["previous_turn"]["slots"]["person_raw"] == "Гаранин"
    assert second.slots["person_raw"] == "Моисеев"
    assert second.slots["dialogue_act"] == "correction"


@pytest.mark.asyncio
async def test_production_without_llm_fails_closed_instead_of_regex_guessing():
    frame = await FailClosedSemanticInterpreter().interpret("покажи задачи пользователя X в пространстве DMS")
    assert frame.intent_hint is None
    assert frame.clarifications
    assert frame.confidence == 0.0
