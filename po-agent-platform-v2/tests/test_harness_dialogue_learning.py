import pytest

from po_agent.harness import HarnessRequest, ResponseStatus
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.runtime_factory import build_runtime_bundle


class ScriptedInterpreter:
    def __init__(self, frame):
        self.frame = frame

    async def interpret(self, query, *, context=None):
        return self.frame


@pytest.mark.asyncio
async def test_explicit_reusable_definition_changes_config_not_python(tmp_path):
    frame = SemanticFrame(
        canonical_query="remember semantic definition",
        intent_hint="learn_semantic",
        slots={"learn_term": "open_tasks", "learn_meaning": "not_completed", "learn_scope": "global"},
        llm_used=True,
    )
    bundle = build_runtime_bundle(
        "fake",
        semantic_interpreter=ScriptedInterpreter(frame),
        learned_semantics_path=str(tmp_path / "semantics.json"),
    )
    response = await bundle.runtime.process(HarnessRequest(
        query="Запомни: открытые задачи всегда означают все незавершённые",
        session_id="learn-1",
    ))
    assert response.status is ResponseStatus.COMPLETED
    assert response.data["learning_rule"]["status"] == "active"
    assert bundle.semantics is not None
    assert bundle.semantics.context()["open_tasks"] == "not_completed"
    assert (tmp_path / "semantics.json").exists()


@pytest.mark.asyncio
async def test_conflicting_definition_never_silently_replaces_active_semantics(tmp_path):
    path = str(tmp_path / "semantics.json")
    first = SemanticFrame(
        canonical_query="learn",
        intent_hint="learn_semantic",
        slots={"learn_term": "open_tasks", "learn_meaning": "not_completed"},
        llm_used=True,
    )
    bundle = build_runtime_bundle("fake", semantic_interpreter=ScriptedInterpreter(first), learned_semantics_path=path)
    await bundle.runtime.process(HarnessRequest(query="Запомни первое правило", session_id="learn-a"))

    second = SemanticFrame(
        canonical_query="learn",
        intent_hint="learn_semantic",
        slots={"learn_term": "open_tasks", "learn_meaning": "Open"},
        llm_used=True,
    )
    bundle.runtime.inner.inner.interpreter = ScriptedInterpreter(second)
    response = await bundle.runtime.process(HarnessRequest(query="Теперь всегда считай только Open", session_id="learn-b"))
    assert response.status is ResponseStatus.COMPLETED
    assert response.warnings == ["learning_conflict_pending"]
    assert bundle.semantics.context()["open_tasks"] == "not_completed"
