from __future__ import annotations

import pytest

from po_agent.harness.contracts import HarnessRequest, ResponseStatus
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.runtime_factory import build_runtime_bundle
from po_agent.harness.session_corrections import (
    SessionCorrection,
    SessionCorrectionSemanticInterpreter,
    SessionCorrectionStore,
)


class _AlwaysWrongAssigneeInterpreter:
    async def interpret(self, query: str, *, context=None) -> SemanticFrame:
        return SemanticFrame(
            canonical_query=query,
            intent_hint="task_search",
            slots={"member_login": "Ivanov", "assignee": "Ivanov"},
            confidence=0.95,
            llm_used=False,
        )


@pytest.mark.asyncio
async def test_session_correction_overlay_is_applied_only_to_same_session():
    store = SessionCorrectionStore()
    store.append(
        SessionCorrection(
            correction_id="c1",
            session_id="s1",
            kind="entity_resolution",
            expected_value="Kalachanov.V.V",
            incorrect_value="Ivanov",
            source_trace_id="t1",
            source_query="show Kalachanov.V.V tasks",
            corrected_query="wrong user",
            slot_overrides={"member_login": "Kalachanov.V.V", "assignee": "Kalachanov.V.V"},
        )
    )
    interpreter = SessionCorrectionSemanticInterpreter(_AlwaysWrongAssigneeInterpreter(), store)

    same = await interpreter.interpret("show tasks", context={"session_id": "s1"})
    other = await interpreter.interpret("show tasks", context={"session_id": "s2"})

    assert same.slots["member_login"] == "Kalachanov.V.V"
    assert same.slots["assignee"] == "Kalachanov.V.V"
    assert other.slots["member_login"] == "Ivanov"
    assert other.slots["assignee"] == "Ivanov"


@pytest.mark.asyncio
async def test_explicit_feedback_is_captured_and_does_not_change_global_learning():
    bundle = build_runtime_bundle(mode="fake", semantic_interpreter=_AlwaysWrongAssigneeInterpreter())
    runtime = bundle.runtime
    session_id = "dialogue-correction-001"

    first = await runtime.process(
        HarnessRequest(
            query="покажи задачи на пользователя Kalachanov.V.V со статусом CLOSED",
            session_id=session_id,
        )
    )
    assert first.status == ResponseStatus.COMPLETED

    correction = await runtime.process(
        HarnessRequest(
            query="ты вывел задачи не Каланчанова, а Иванова",
            session_id=session_id,
        )
    )
    assert correction.status == ResponseStatus.COMPLETED
    assert correction.data["session_correction"]["scope"] == "session"
    assert correction.data["session_correction"]["expected_value"] == "Kalachanov.V.V"
    assert correction.data["_harness"]["production_skill_changed"] is False
    assert correction.data["_harness"]["global_semantics_changed"] is False

    repeated = await runtime.process(
        HarnessRequest(
            query="покажи задачи на пользователя Kalachanov.V.V со статусом CLOSED",
            session_id=session_id,
        )
    )
    assert repeated.status == ResponseStatus.COMPLETED
    assert repeated.data["_harness"]["session_correction_applied"] is True
    assert repeated.data["_harness"]["session_correction_overrides"] == {
        "member_login": "Kalachanov.V.V",
        "assignee": "Kalachanov.V.V",
    }

    fresh_session = await runtime.process(
        HarnessRequest(
            query="покажи задачи на пользователя Kalachanov.V.V со статусом CLOSED",
            session_id="dialogue-correction-002",
        )
    )
    assert fresh_session.status == ResponseStatus.COMPLETED
    assert fresh_session.data["_harness"]["session_correction_applied"] is False
