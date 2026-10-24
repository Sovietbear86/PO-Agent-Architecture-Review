import json

import pytest

from po_agent.harness.dialogue_runtime import LLMJsonSemanticInterpreter
from po_agent.llm.mock import MockLLMClient


@pytest.mark.asyncio
async def test_llm_interpreter_parses_groundable_semantic_frame():
    payload = {
        "canonical_query": "найди задачи исполнитель {member_login} статус {status} в спринте {sprint_id}",
        "intent_hint": "task_search",
        "slots": {
            "person_raw": "Гаранин",
            "sprint_raw": "OLP 4",
            "status_raw": "открытые",
            "status_semantic": "open_tasks",
        },
        "clarifications": [],
        "confidence": 0.91,
    }
    client = MockLLMClient(response_text=json.dumps(payload, ensure_ascii=False))
    interpreter = LLMJsonSemanticInterpreter(client, model="qwen-test")
    frame = await interpreter.interpret("Покажи открытые задачи Гаранина в OLP 4", context={"known_sprints": ["OLP-SPRNT-4"]})
    assert frame.llm_used is True
    assert frame.confidence == pytest.approx(0.91)
    assert frame.slots["person_raw"] == "Гаранин"
    assert "{member_login}" in frame.canonical_query


@pytest.mark.asyncio
async def test_llm_interpreter_accepts_json_code_fence_but_not_free_text():
    client = MockLLMClient(response_text='```json\n{"canonical_query":"история WMB-101","slots":{},"clarifications":[],"confidence":1}\n```')
    frame = await LLMJsonSemanticInterpreter(client).interpret("историю WMB-101")
    assert frame.canonical_query == "история WMB-101"

    broken = MockLLMClient(response_text="Конечно, вот ответ")
    with pytest.raises((ValueError, json.JSONDecodeError)):
        await LLMJsonSemanticInterpreter(broken).interpret("что там?")


@pytest.mark.asyncio
async def test_llm_interpreter_clamps_invalid_confidence_and_preserves_clarification():
    client = MockLLMClient(response_text=json.dumps({
        "canonical_query": "найди задачи статус {status}",
        "slots": {"status_semantic": "open_tasks"},
        "clarifications": [{"field": "status", "question": "Что считать открытыми?", "options": ["Open", "In Progress"]}],
        "confidence": 7,
    }, ensure_ascii=False))
    frame = await LLMJsonSemanticInterpreter(client).interpret("открытые задачи")
    assert frame.confidence == 1.0
    assert frame.clarifications[0].field == "status"
    assert frame.clarifications[0].options == ("Open", "In Progress")
