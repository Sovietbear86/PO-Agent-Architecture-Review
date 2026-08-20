from __future__ import annotations

import pytest

from po_agent.harness.core8_semantic_precision import Core8SemanticPrecisionInterpreter
from po_agent.harness.dialogue_runtime import SemanticFrame
from po_agent.harness.fail_closed_dialogue_runtime import FailClosedIntentPreservingDialogueHarnessRuntime
from po_agent.harness.live_entity_grounding import LiveGroundedEntityResolver


class BadSprintDelegate:
    """Model the exact provider degradation observed in QA 019 rerun."""

    async def interpret(self, query: str, *, context=None) -> SemanticFrame:
        return SemanticFrame(
            canonical_query="покажи задачу {task_key}",
            intent_hint="task_lookup",
            slots={"task_key": "SPRNT-1", "person_raw": "Гаранина"},
            confidence=0.9,
            llm_used=True,
        )


class LiveSprintOnlyAdapter:
    """Cached task context is empty, but live SWTR can validate the sprint."""

    async def search_tasks(self, query: str):
        return []

    async def sprint_exists(self, sprint_id: str) -> bool:
        return sprint_id in {"DMS-SPRNT-1", "OLP-SPRNT-17"}


@pytest.mark.asyncio
async def test_full_dms_sprint_id_is_preserved_and_task_lookup_repaired():
    interpreter = Core8SemanticPrecisionInterpreter(BadSprintDelegate())
    frame = await interpreter.interpret("Покажи задачи Гаранина в DMS-SPRNT-1")

    assert frame.intent_hint == "task_search"
    assert frame.slots["sprint_id"] == "DMS-SPRNT-1"
    assert "task_key" not in frame.slots


@pytest.mark.asyncio
async def test_full_olp_sprint_id_is_generic_not_dms_hardcoded():
    interpreter = Core8SemanticPrecisionInterpreter(BadSprintDelegate())
    frame = await interpreter.interpret("Покажи задачи Гаранина в OLP-SPRNT-17")

    assert frame.intent_hint == "task_search"
    assert frame.slots["sprint_id"] == "OLP-SPRNT-17"
    assert "task_key" not in frame.slots


def test_dialogue_enrichment_does_not_extract_sprint_suffix_as_task_key():
    frame = SemanticFrame(
        canonical_query="покажи задачи",
        intent_hint="task_search",
        slots={"sprint_id": "DMS-SPRNT-1"},
    )
    enriched = FailClosedIntentPreservingDialogueHarnessRuntime._enrich_explicit_task_key(
        frame,
        "Покажи задачи Гаранина в DMS-SPRNT-1",
    )

    assert enriched.slots == {"sprint_id": "DMS-SPRNT-1"}


def test_real_task_key_still_enriches_normally():
    frame = SemanticFrame(canonical_query="покажи задачу", intent_hint="task_lookup")
    enriched = FailClosedIntentPreservingDialogueHarnessRuntime._enrich_explicit_task_key(
        frame,
        "Покажи задачу DMS-348",
    )

    assert enriched.slots["task_key"] == "DMS-348"


@pytest.mark.asyncio
async def test_live_grounder_preserves_explicit_sprint_when_cached_known_sprints_empty():
    resolver = LiveGroundedEntityResolver(LiveSprintOnlyAdapter())
    frame = SemanticFrame(
        canonical_query="покажи задачи {sprint_id}",
        intent_hint="task_search",
        slots={"sprint_id": "DMS-SPRNT-1"},
    )

    grounded = await resolver.ground(frame, "Покажи задачи в DMS-SPRNT-1")

    assert grounded.slots["sprint_id"] == "DMS-SPRNT-1"
    assert all(item.field != "sprint_id" for item in grounded.clarifications)


@pytest.mark.asyncio
async def test_live_grounder_rejects_unproven_explicit_sprint():
    resolver = LiveGroundedEntityResolver(LiveSprintOnlyAdapter())
    frame = SemanticFrame(
        canonical_query="покажи задачи {sprint_id}",
        intent_hint="task_search",
        slots={"sprint_id": "DMS-SPRNT-999"},
    )

    grounded = await resolver.ground(frame, "Покажи задачи в DMS-SPRNT-999")

    assert "sprint_id" not in grounded.slots
    assert any(item.field == "sprint_id" for item in grounded.clarifications)
