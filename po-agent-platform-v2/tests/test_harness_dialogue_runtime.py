import pytest

from po_agent.harness import HarnessRequest, ResponseStatus
from po_agent.harness.dialogue_runtime import ClarificationNeed, SemanticFrame
from po_agent.harness.runtime_factory import build_runtime_bundle


class ScriptedInterpreter:
    def __init__(self, frame):
        self.frame = frame

    async def interpret(self, query, *, context=None):
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
    assert r4.data["_harness"]["llm_used"] is True
    assert "Ответ помог" in r4.data["_harness"]["feedback_prompt"]


@pytest.mark.asyncio
async def test_unambiguous_semantic_frame_executes_without_clarification():
    frame = SemanticFrame(canonical_query="история WMB-101", intent_hint="task_history", llm_used=True)
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
    assert b2.status is ResponseStatus.NEEDS_CLARIFICATION
