import pytest

from po_agent.harness import HarnessRequest, ResponseStatus
from po_agent.harness.dialogue_runtime import ClarificationNeed, SemanticFrame, DialogueHarnessRuntime
from po_agent.harness.runtime_factory import build_runtime_bundle
from po_agent.harness.skill_catalog import SKILL_CATALOG, canonical_semantic_intents


class ScriptedInterpreter:
    def __init__(self, frame):
        self.frame = frame
        self.last_context = None

    async def interpret(self, query, *, context=None):
        self.last_context = context
        return self.frame


@pytest.mark.asyncio
async def test_dialogue_clarifies_multiple_ambiguous_slots_before_execution():
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login} статус {status} в спринте {sprint_id}",
        intent_hint="task_search",
        slots={"person_raw": "Гаранина", "sprint_raw": "OLP 4", "status_raw": "открытые"},
        clarifications=[
            ClarificationNeed("member_login", "Кого вы имеете в виду?", ("Garanin.R.V", "Garanin.A.V")),
            ClarificationNeed("status", "Какие статусы считать открытыми?", ("все незавершённые", "только In Progress")),
            ClarificationNeed("sprint_id", "Какой именно спринт?", ("OLP-SPRNT-4", "OLP-SPRNT-14")),
        ],
        llm_used=True,
    )
    runtime = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(frame)).runtime
    r1 = await runtime.process(HarnessRequest(query="Покажи открытые задачи Гаранина в спринте OLP 4", session_id="d1"))
    assert r1.status is ResponseStatus.NEEDS_CLARIFICATION
    assert r1.question == "Кого вы имеете в виду?"
    r2 = await runtime.process(HarnessRequest(query="Garanin.R.V", session_id="d1"))
    assert r2.status is ResponseStatus.NEEDS_CLARIFICATION
    assert "статусы" in r2.question
    r3 = await runtime.process(HarnessRequest(query="In Progress", session_id="d1"))
    assert r3.status is ResponseStatus.NEEDS_CLARIFICATION
    assert "спринт" in r3.question
    r4 = await runtime.process(HarnessRequest(query="OLP-SPRNT-4", session_id="d1"))
    assert r4.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}
    assert isinstance(r4.data, dict)
    assert r4.data["filters"] == {"assignee": "Garanin.R.V", "sprint_id": "OLP-SPRNT-4", "status": "In Progress"}
    assert r4.data["_harness"]["llm_used"] is True
    assert "Ответ помог" in r4.data["_harness"]["feedback_prompt"]


@pytest.mark.asyncio
async def test_grounded_composite_search_applies_all_filters_not_only_first_one():
    frame = SemanticFrame(
        canonical_query="task search",
        intent_hint="task_search",
        slots={
            "member_login": "Sidorov.S.S",
            "sprint_id": "WMB-SPRNT-1",
            "status": "not_completed",
        },
        llm_used=True,
    )
    runtime = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(frame)).runtime
    response = await runtime.process(HarnessRequest(query="Покажи открытые задачи Сидорова в первом WMB спринте", session_id="multi"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-search-assignee"
    assert response.data["count"] == 1
    assert response.data["tasks"][0]["key"] == "WMB-102"
    assert response.data["filters"] == {
        "assignee": "Sidorov.S.S",
        "sprint_id": "WMB-SPRNT-1",
        "status": "not_completed",
    }


@pytest.mark.asyncio
async def test_specific_assignee_intent_with_sprint_uses_composite_execution():
    """A specific semantic intent must not discard independent filters."""
    frame = SemanticFrame(
        canonical_query="task search assignee in sprint",
        intent_hint="task_search_assignee",
        slots={
            "member_login": "Sidorov.S.S",
            "sprint_id": "WMB-SPRNT-1",
        },
        llm_used=True,
    )
    runtime = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(frame)).runtime
    response = await runtime.process(HarnessRequest(query="Покажи задачи Sidorov.S.S в WMB-SPRNT-1", session_id="specific-multi"))

    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-search-assignee"
    assert response.data["count"] == 1
    assert response.data["tasks"][0]["key"] == "WMB-102"
    assert response.data["filters"] == {
        "assignee": "Sidorov.S.S",
        "sprint_id": "WMB-SPRNT-1",
    }


@pytest.mark.asyncio
async def test_final_execution_boundary_rejects_unproven_sprint():
    """COMPLETED + empty is forbidden when a production validator says unknown."""
    bundle = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(SemanticFrame("unused")))
    dialogue = bundle.runtime.inner
    while not isinstance(dialogue, DialogueHarnessRuntime):
        dialogue = dialogue.inner

    async def reject_sprint(sprint_id):
        assert sprint_id == "DMS-SPRNT-999999"
        return False

    dialogue.adapter.sprint_exists = reject_sprint
    response = await dialogue._execute_frame(
        SemanticFrame(
            canonical_query="task search sprint",
            intent_hint="task_search_sprint",
            slots={"sprint_id": "DMS-SPRNT-999999"},
            llm_used=True,
        ),
        "unproven-execution",
        0.0,
    )

    assert response.status is ResponseStatus.NEEDS_CLARIFICATION
    assert response.warnings == ["unproven_sprint"]
    assert response.data == {"sprint_id": "DMS-SPRNT-999999", "source_proven": False}


@pytest.mark.asyncio
async def test_unambiguous_semantic_frame_executes_without_clarification():
    frame = SemanticFrame(
        canonical_query="история WMB-101",
        intent_hint="task_history",
        slots={"task_key": "WMB-101"},
        llm_used=True,
    )
    bundle = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(frame))
    response = await bundle.runtime.process(HarnessRequest(query="Покажи историю WMB-101", session_id="d2"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.skill_id == "task-history"
    trace = bundle.runtime.history.get(response.trace_id)
    assert trace is not None
    assert trace.llm_used is True


@pytest.mark.asyncio
async def test_clarification_is_isolated_by_session():
    frame = SemanticFrame(
        canonical_query="найди задачи исполнитель {member_login}",
        clarifications=[ClarificationNeed("member_login", "Какой участник команды?")],
        llm_used=True,
    )
    runtime = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(frame)).runtime
    a = await runtime.process(HarnessRequest(query="Покажи его задачи", session_id="A"))
    b = await runtime.process(HarnessRequest(query="Покажи его задачи", session_id="B"))
    assert a.status is ResponseStatus.NEEDS_CLARIFICATION
    assert b.status is ResponseStatus.NEEDS_CLARIFICATION
    a2 = await runtime.process(HarnessRequest(query="Ivanov.I.I", session_id="A"))
    assert a2.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}
    b2 = await runtime.process(HarnessRequest(query="", session_id="B"))
    assert b2.status is ResponseStatus.FAILED
    assert "query_empty" in b2.warnings


@pytest.mark.asyncio
async def test_empty_query_rejected_before_semantic_interpreter_call():
    class FailingInterpreter:
        async def interpret(self, query, *, context=None):
            raise RuntimeError("Interpreter should not be called for empty query")

    runtime = build_runtime_bundle("fake", semantic_interpreter=FailingInterpreter()).runtime
    r1 = await runtime.process(HarnessRequest(query="", session_id="empty1"))
    assert r1.status is ResponseStatus.FAILED
    assert "query_empty" in r1.warnings
    assert "trace_id" in r1.to_dict()
    assert "session_id" in r1.to_dict()
    r2 = await runtime.process(HarnessRequest(query="   ", session_id="empty2"))
    assert r2.status is ResponseStatus.FAILED
    assert "query_empty" in r2.warnings


@pytest.mark.asyncio
async def test_semantic_interpreter_receives_catalog_driven_contract():
    frame = SemanticFrame(
        canonical_query="найди задачи OLAP",
        intent_hint="task_search",
        slots={"product": "OLAP"},
        llm_used=True,
    )
    interpreter = ScriptedInterpreter(frame)
    runtime = build_runtime_bundle("fake", semantic_interpreter=interpreter).runtime
    await runtime.process(HarnessRequest(query="Найди задачи по OLAP", session_id="contract"))

    context = interpreter.last_context
    assert context is not None
    assert tuple(context["allowed_intents"]) == canonical_semantic_intents()

    capabilities = context["available_capabilities"]
    expected = {entry.id for entry in SKILL_CATALOG if entry.status == "implemented"}
    assert {item["skill_id"] for item in capabilities} == expected
    assert {item["intent"] for item in capabilities} == set(canonical_semantic_intents())
    assert all(item["capability_id"] for item in capabilities)
    assert all(item["description"] for item in capabilities)


# Explicit task key extraction tests


def test_enrich_explicit_task_key_extracted_from_query():
    frame = SemanticFrame(
        canonical_query="покажи задачу OLP-3134",
        intent_hint="task_by_id",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Покажи задачу OLP-3134")
    assert enriched.slots.get("task_key") == "OLP-3134"


def test_enrich_preserves_existing_task_key():
    frame = SemanticFrame(
        canonical_query="покажи задачу OLP-3134",
        intent_hint="task_by_id",
        slots={"task_key": "WMB-101"},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Покажи задачу OLP-3134")
    assert enriched.slots.get("task_key") == "WMB-101"


def test_enrich_zero_task_keys_no_extraction():
    frame = SemanticFrame(
        canonical_query="покажи задачи по OLAP",
        intent_hint="task_search",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Покажи задачи по OLAP")
    assert enriched.slots.get("task_key") is None


def test_enrich_multiple_task_keys_no_arbitrary_selection():
    frame = SemanticFrame(
        canonical_query="сравни OLP-3134 и WMB-101",
        intent_hint="task_comparison",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Сравни OLP-3134 и WMB-101")
    assert enriched.slots.get("task_key") is None


def test_enrich_team_matching_with_extracted_key():
    frame = SemanticFrame(
        canonical_query="кому лучше назначить DMS-341?",
        intent_hint="team_matching",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Кому лучше назначить DMS-341?")
    assert enriched.slots.get("task_key") == "DMS-341"


@pytest.mark.asyncio
async def test_dialogue_executes_with_extracted_task_key():
    frame = SemanticFrame(
        canonical_query="покажи задачу WMB-101",
        intent_hint="task_by_id",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Покажи задачу WMB-101")
    assert enriched.slots.get("task_key") == "WMB-101"

    bundle = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(enriched))
    response = await bundle.runtime.process(HarnessRequest(query="Покажи задачу WMB-101", session_id="extract"))
    assert response.status in {ResponseStatus.COMPLETED, ResponseStatus.PARTIAL}
    if response.data:
        assert "task_key" in response.data


@pytest.mark.asyncio
async def test_dialogue_with_multiple_keys_fails_closed():
    frame = SemanticFrame(
        canonical_query="сравни OLP-3134 и WMB-101",
        intent_hint="unknown_intent",
        slots={},
        llm_used=True,
    )
    enriched = DialogueHarnessRuntime._enrich_explicit_task_key(frame, "Сравни OLP-3134 и WMB-101")
    assert enriched.slots.get("task_key") is None

    bundle = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(enriched))
    response = await bundle.runtime.process(HarnessRequest(query="Сравни OLP-3134 и WMB-101", session_id="multi-key"))
    assert response.status is ResponseStatus.FAILED or response.status is ResponseStatus.NEEDS_CLARIFICATION
